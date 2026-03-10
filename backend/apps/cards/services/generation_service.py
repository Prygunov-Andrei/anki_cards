"""
Generation service: card/deck generation, .apkg file creation.
"""
import uuid
import logging
from pathlib import Path

from django.conf import settings
from django.db import transaction

from apps.words.models import Word
from apps.cards.models import GeneratedDeck, Deck, Card
from apps.cards.utils import generate_apkg
from apps.cards.llm_utils import (
    translate_words,
    generate_deck_name,
    detect_category,
    select_image_style,
)
from .media_service import resolve_word_media, get_relative_media_path

logger = logging.getLogger(__name__)


def _find_translation(word: str, translations: dict) -> str:
    """Find translation by exact match or normalized key."""
    translation = translations.get(word, '')
    if not translation:
        word_normalized = word.strip().rstrip('.,!?;:')
        for key, trans in translations.items():
            if key.strip().rstrip('.,!?;:') == word_normalized:
                return trans
    return translation


@transaction.atomic
def generate_cards(user, words_list: list[str], language: str,
                   translations: dict, audio_files: dict, image_files: dict,
                   deck_name: str, image_style: str = 'balanced',
                   save_to_decks: bool = True) -> dict:
    """
    Generate Anki cards: create/update Words, generate .apkg, optionally save as Deck.

    Args:
        user: The requesting user.
        words_list: List of words to create cards for.
        language: Target language code.
        translations: Dict of {word: translation}.
        audio_files: Dict of {word: audio_path_string}.
        image_files: Dict of {word: image_path_string}.
        deck_name: Name for the deck.
        image_style: Image style preset.
        save_to_decks: Whether to save as a Deck in the app.

    Returns:
        Dict with file_id, download_url, deck_name, cards_count, deck_id (optional).
    """
    words_data = []
    media_files = []

    for word in words_list:
        translation = _find_translation(word, translations)

        # Get or create Word in DB
        word_obj, created = Word.objects.get_or_create(
            user=user,
            original_word=word,
            language=language,
            defaults={'translation': translation},
        )

        if not created and word_obj.translation != translation:
            word_obj.translation = translation
            word_obj.save(update_fields=['translation'])

        word_data = {
            'original_word': word,
            'translation': translation,
        }

        # Resolve audio
        audio_path, is_new_audio = resolve_word_media(
            word, audio_files, word_obj, 'audio')
        if audio_path:
            word_data['audio_file'] = str(audio_path)
            if str(audio_path) not in media_files:
                media_files.append(str(audio_path))
            if is_new_audio:
                word_obj.audio_file = get_relative_media_path(audio_path)
                word_obj.save(update_fields=['audio_file'])

        # Resolve image
        image_path, is_new_image = resolve_word_media(
            word, image_files, word_obj, 'images')
        if image_path:
            word_data['image_file'] = str(image_path)
            if str(image_path) not in media_files:
                media_files.append(str(image_path))
            if is_new_image:
                word_obj.image_file = get_relative_media_path(image_path)
                word_obj.save(update_fields=['image_file'])

        words_data.append(word_data)

    # Generate .apkg file
    file_id = uuid.uuid4()
    temp_dir = Path(settings.MEDIA_ROOT) / 'temp_files'
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = temp_dir / f"{file_id}.apkg"

    generate_apkg(
        words_data=words_data,
        deck_name=deck_name,
        media_files=media_files if media_files else None,
        output_path=output_path,
    )

    generated_deck = GeneratedDeck.objects.create(
        id=file_id,
        user=user,
        deck_name=deck_name,
        file_path=str(output_path),
        cards_count=len(words_data) * 2,
    )

    # Try anki sync import (non-critical)
    try:
        from apps.anki_sync.utils import import_apkg_to_anki_collection
        import_apkg_to_anki_collection(user=user, apkg_path=output_path)
    except Exception as e:
        logger.warning(f"Anki sync import failed: {e}")

    response_data = {
        'file_id': file_id,
        'download_url': f'/api/cards/download/{file_id}/',
        'deck_name': deck_name,
        'cards_count': generated_deck.cards_count,
    }

    # Save to "My Decks"
    if save_to_decks:
        deck = Deck.objects.create(
            user=user,
            name=deck_name,
            target_lang=language,
            source_lang=getattr(user, 'native_language', 'ru') or 'ru',
            literary_source=getattr(user, 'active_literary_source', None),
            is_learning_active=True,
        )
        word_objects = Word.objects.filter(
            user=user, original_word__in=words_list, language=language)
        deck.words.set(word_objects)

        # Ensure every word has a normal Card (signal only fires on create,
        # but words may already exist from bulk-create or previous decks)
        for word_obj in word_objects:
            Card.create_from_word(word_obj, 'normal')

        response_data['deck_id'] = deck.id
        response_data['deck_url'] = f'/decks/{deck.id}'

    return response_data


def auto_enrich_simple_mode(user, words_list: list[str], language: str,
                            translations: dict, deck_name: str) -> tuple[dict, str, str]:
    """
    Auto-translate, auto-name deck, auto-select image style for simple mode.

    Returns:
        (updated_translations, updated_deck_name, image_style)
    """
    learning_language = getattr(user, 'learning_language', None) or language
    native_language = getattr(user, 'native_language', None) or 'ru'

    # Auto-translate missing words
    if not translations or len(translations) < len(words_list):
        auto_translations = translate_words(
            words_list=words_list,
            learning_language=learning_language,
            native_language=native_language,
            user=user,
        )
        translations = {**auto_translations, **translations}

    # Auto-generate deck name
    if not deck_name or deck_name == 'Новая колода':
        deck_name = generate_deck_name(
            words_list=words_list,
            learning_language=learning_language,
            native_language=native_language,
            user=user,
        )

    # Auto-detect category and select image style
    category = detect_category(
        words_list=words_list,
        language=learning_language,
        native_language=native_language,
        user=user,
    )
    image_style = select_image_style(category)

    return translations, deck_name, image_style


def generate_apkg_from_deck(user, deck_id: int) -> dict:
    """
    Generate .apkg file from an existing Deck.

    Returns:
        Dict with file_id, message.
    """
    deck = Deck.objects.select_related('user').prefetch_related('words').get(
        id=deck_id, user=user)

    words = deck.words.all()
    if not words.exists():
        raise ValueError('Deck is empty. Add words before generating.')

    words_data = []
    media_files = []

    for word in words:
        word_data = {
            'original_word': word.original_word,
            'translation': word.translation,
            'card_type': word.card_type,
        }

        # Resolve audio
        if word.audio_file:
            audio_path = normalize_media_name(word.audio_file.name, 'audio')
            if audio_path and audio_path.exists():
                word_data['audio_file'] = str(audio_path)
                media_files.append(str(audio_path))

        # Resolve image
        if word.image_file:
            image_path = normalize_media_name(word.image_file.name, 'images')
            if image_path and image_path.exists():
                word_data['image_file'] = str(image_path)
                media_files.append(str(image_path))

        words_data.append(word_data)

    # Generate .apkg
    file_id = str(uuid.uuid4())
    output_path = Path(settings.MEDIA_ROOT) / "temp_files" / f"{file_id}.apkg"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_apkg(
        words_data=words_data,
        deck_name=deck.name,
        media_files=media_files if media_files else None,
        output_path=output_path,
    )

    generated_deck = GeneratedDeck.objects.create(
        user=user,
        deck_name=deck.name,
        file_path=str(output_path),
        cards_count=len(words_data) * 2,
    )

    # Try anki sync
    try:
        from apps.anki_sync.utils import import_apkg_to_anki_collection
        import_apkg_to_anki_collection(user=user, apkg_path=output_path)
    except Exception as e:
        logger.warning(f"Anki sync import failed: {e}")

    return {
        'file_id': str(generated_deck.id),
        'message': 'Deck generated successfully',
    }


def normalize_media_name(name: str, media_subdir: str) -> Path | None:
    """
    Normalize a FileField .name to absolute path.
    Handles URLs, absolute paths, and relative paths.
    """
    from .media_service import normalize_media_path
    return normalize_media_path(name, media_subdir=media_subdir)
