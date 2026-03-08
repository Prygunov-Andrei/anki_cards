"""
Deck service: CRUD, merge, word management, invert, empty cards.
"""
import logging

from django.db import transaction

from apps.words.models import Word
from apps.cards.models import Deck, Card

logger = logging.getLogger(__name__)


def add_words_to_deck(user, deck: Deck, words_data: list[dict]) -> tuple[list[int], list[dict]]:
    """
    Add words to a deck. Supports existing word_id or creating new words.

    Args:
        user: The requesting user.
        deck: The Deck instance.
        words_data: List of dicts, each with word_id or original_word/translation/language.

    Returns:
        (added_word_ids, errors)
    """
    from apps.cards.serializers import DeckWordAddSerializer

    added_words = []
    errors = []

    for word_data in words_data:
        serializer = DeckWordAddSerializer(data=word_data)
        if not serializer.is_valid():
            errors.append(serializer.errors)
            continue

        word_id = serializer.validated_data.get('word_id')

        if word_id:
            try:
                word = Word.objects.get(id=word_id, user=user)
                if word not in deck.words.all():
                    deck.words.add(word)
                    added_words.append(word.id)
            except Word.DoesNotExist:
                errors.append({'word_id': f'Word with ID {word_id} not found'})
        else:
            original_word = serializer.validated_data['original_word']
            translation = serializer.validated_data['translation']
            language = serializer.validated_data['language']
            image_url = serializer.validated_data.get('image_url', '')
            audio_url = serializer.validated_data.get('audio_url', '')

            word, created = Word.objects.get_or_create(
                user=user,
                original_word=original_word,
                language=language,
                defaults={'translation': translation},
            )

            if not created:
                word.translation = translation

            if image_url:
                relative_path = image_url.replace('/media/', '') if image_url.startswith('/media/') else image_url
                word.image_file.name = relative_path

            if audio_url:
                relative_path = audio_url.replace('/media/', '') if audio_url.startswith('/media/') else audio_url
                word.audio_file.name = relative_path

            word.save()

            if word not in deck.words.all():
                deck.words.add(word)
                added_words.append(word.id)

    if added_words:
        deck.save()

    return added_words, errors


def update_word_in_deck(user, deck: Deck, word_id: int, data: dict) -> dict:
    """
    Update a word's fields within a deck context.

    Returns dict with updated word data.
    Raises ValueError for validation errors, Word.DoesNotExist if not found.
    """
    try:
        word = deck.words.get(id=word_id)
    except Word.DoesNotExist:
        raise Word.DoesNotExist(f'Word with ID {word_id} not found in deck')

    updated_fields = []
    errors = {}

    # Update original_word
    original_word = data.get('original_word')
    if original_word is not None:
        original_word = original_word.strip()
        if not original_word:
            errors['original_word'] = 'Field cannot be empty'
        elif len(original_word) > 200:
            errors['original_word'] = 'Max length: 200 characters'
        else:
            existing = Word.objects.filter(
                user=user, original_word=original_word, language=word.language
            ).exclude(id=word_id).first()
            if existing:
                errors['original_word'] = f'Word "{original_word}" already exists for this language'
            else:
                word.original_word = original_word
                updated_fields.append('original_word')

    # Update translation
    translation = data.get('translation')
    if translation is not None:
        translation = translation.strip()
        if not translation:
            errors['translation'] = 'Field cannot be empty'
        elif len(translation) > 200:
            errors['translation'] = 'Max length: 200 characters'
        else:
            word.translation = translation
            updated_fields.append('translation')

    # Update image_file
    image_file = data.get('image_file')
    if image_file is not None:
        if image_file == '' or image_file is None:
            word.image_file = None
        else:
            relative_path = image_file.replace('/media/', '') if image_file.startswith('/media/') else image_file
            word.image_file.name = relative_path
        updated_fields.append('image_file')

    # Update audio_file
    audio_file = data.get('audio_file')
    if audio_file is not None:
        if audio_file == '' or audio_file is None:
            word.audio_file = None
        else:
            relative_path = audio_file.replace('/media/', '') if audio_file.startswith('/media/') else audio_file
            word.audio_file.name = relative_path
        updated_fields.append('audio_file')

    if errors:
        raise ValueError(errors)

    if not updated_fields:
        raise ValueError('No fields to update')

    word.save()

    return {
        'id': word.id,
        'original_word': word.original_word,
        'translation': word.translation,
        'language': word.language,
        'image_file': word.image_file.url if word.image_file else None,
        'audio_file': word.audio_file.url if word.audio_file else None,
        'updated_fields': updated_fields,
    }


@transaction.atomic
def merge_decks(user, deck_ids: list[int], target_deck_id: int = None,
                new_deck_name: str = 'Merged deck',
                delete_source_decks: bool = False) -> dict:
    """
    Merge multiple decks into one.

    Returns dict with merge result.
    """
    decks = Deck.objects.filter(id__in=deck_ids, user=user)

    if decks.count() != len(deck_ids):
        raise ValueError('Some decks not found or do not belong to you')

    if len(set(deck_ids)) != len(deck_ids):
        raise ValueError('Duplicate deck IDs in list')

    all_words = set()
    for deck in decks:
        all_words.update(deck.words.all())

    if not all_words:
        raise ValueError('All specified decks are empty')

    if target_deck_id:
        target_deck = Deck.objects.get(id=target_deck_id, user=user)
        if not delete_source_decks and target_deck_id in deck_ids:
            raise ValueError(
                'Target deck cannot be in source list unless source decks are deleted')
    else:
        first_deck = decks.first()
        target_deck = Deck.objects.create(
            user=user,
            name=new_deck_name,
            target_lang=first_deck.target_lang,
            source_lang=first_deck.source_lang,
        )

    target_deck.words.add(*all_words)
    target_deck.save()

    deleted_decks = []
    if delete_source_decks:
        decks_to_delete = decks.exclude(id=target_deck.id)
        for deck in decks_to_delete:
            deleted_decks.append({'id': deck.id, 'name': deck.name})
            deck.delete()

    from apps.cards.serializers import DeckDetailSerializer
    result_serializer = DeckDetailSerializer(target_deck)

    return {
        'message': f'Decks merged into "{target_deck.name}"',
        'target_deck': result_serializer.data,
        'words_count': len(all_words),
        'source_decks_count': len(deck_ids),
        'deleted_decks': deleted_decks if delete_source_decks else None,
    }


@transaction.atomic
def invert_all_words(user, deck_id: int) -> dict:
    """
    Create inverted Card objects for all words in a deck.
    """
    deck = Deck.objects.select_related('user').prefetch_related('words').get(
        id=deck_id, user=user)

    words = deck.words.all()
    if not words.exists():
        raise ValueError('Deck is empty')

    inverted_cards = []
    skipped_words = []
    errors = []

    for word in words:
        try:
            if word.card_type in ('inverted', 'empty'):
                skipped_words.append({
                    'id': word.id,
                    'original_word': word.original_word,
                    'reason': f'Skipped: legacy {word.card_type} Word',
                })
                continue

            existing = Card.objects.filter(
                user=user, word=word, card_type='inverted').first()
            if existing:
                skipped_words.append({
                    'id': word.id,
                    'original_word': word.original_word,
                    'reason': 'Inverted card already exists',
                })
                continue

            inverted_card = Card.create_inverted(word)
            inverted_cards.append({
                'card_id': inverted_card.id,
                'word_id': word.id,
                'original_word': word.original_word,
                'translation': word.translation,
                'card_type': 'inverted',
            })
        except Exception as e:
            errors.append({
                'word_id': word.id,
                'original_word': word.original_word,
                'error': str(e),
            })

    if inverted_cards:
        deck.save()

    return {
        'deck_id': deck_id,
        'deck_name': deck.name,
        'inverted_cards_count': len(inverted_cards),
        'inverted_cards': inverted_cards,
        'skipped_words': skipped_words or None,
        'errors': errors or None,
    }


def invert_single_word(user, deck_id: int, word_id: int) -> dict:
    """Create an inverted Card for a single word in a deck."""
    deck = Deck.objects.select_related('user').prefetch_related('words').get(
        id=deck_id, user=user)

    try:
        word = deck.words.get(id=word_id)
    except Word.DoesNotExist:
        raise Word.DoesNotExist(f'Word with ID {word_id} not found in deck')

    if word.card_type in ('inverted', 'empty'):
        raise ValueError(f'Cannot invert {word.card_type} word.')

    existing = Card.objects.filter(
        user=user, word=word, card_type='inverted').first()
    if existing:
        raise ValueError('Inverted card already exists for this word.')

    inverted_card = Card.create_inverted(word)
    deck.save()

    return {
        'original_word': {
            'id': word.id,
            'original_word': word.original_word,
            'translation': word.translation,
            'language': word.language,
        },
        'inverted_card': {
            'card_id': inverted_card.id,
            'word_id': word.id,
            'card_type': 'inverted',
        },
    }


@transaction.atomic
def create_empty_cards_for_deck(user, deck_id: int) -> dict:
    """Create empty cards for all normal words in a deck."""
    deck = Deck.objects.select_related('user').prefetch_related('words').get(
        id=deck_id, user=user)

    words = deck.words.all()
    if not words.exists():
        raise ValueError('Deck is empty')

    empty_cards = []
    skipped_cards = []
    errors = []

    for word in words:
        try:
            is_inverted = (
                word.card_type == 'inverted' or
                (word.card_type == 'normal' and word.language == deck.source_lang)
            )
            is_empty = word.card_type == 'empty' or word.original_word.startswith('_empty_')

            if is_inverted or is_empty:
                reason = 'inverted' if is_inverted else 'empty'
                skipped_cards.append({
                    'id': word.id,
                    'original_word': word.original_word,
                    'reason': f'Skipped: {reason} card',
                })
                continue

            result = _create_single_empty_card(user, deck, word)
            if result:
                empty_cards.append(result)
            else:
                skipped_cards.append({
                    'id': word.id,
                    'original_word': word.original_word,
                    'reason': 'Already in deck',
                })
        except Exception as e:
            errors.append({
                'word_id': word.id,
                'original_word': word.original_word,
                'error': str(e),
            })

    if empty_cards or skipped_cards:
        deck.save()

    return {
        'deck_id': deck_id,
        'deck_name': deck.name,
        'empty_cards_count': len(empty_cards),
        'empty_cards': empty_cards,
        'skipped_cards': skipped_cards or None,
        'errors': errors or None,
    }


def create_empty_card_for_word(user, deck_id: int, word_id: int) -> dict:
    """Create an empty card for a single word in a deck."""
    deck = Deck.objects.select_related('user').prefetch_related('words').get(
        id=deck_id, user=user)

    try:
        word = deck.words.get(id=word_id)
    except Word.DoesNotExist:
        raise Word.DoesNotExist(f'Word with ID {word_id} not found in deck')

    is_inverted = (
        word.card_type == 'inverted' or
        (word.card_type == 'normal' and word.language == deck.source_lang)
    )
    is_empty = word.card_type == 'empty' or word.original_word.startswith('_empty_')

    if is_inverted or is_empty:
        reason = 'inverted' if is_inverted else 'empty'
        raise ValueError(
            f'Cannot create empty card for {reason} card. '
            'Empty cards are only created for normal cards.')

    empty_original = f"_empty_{word.id}"
    empty_translation = f"{word.original_word} // {word.translation}"
    empty_language = deck.target_lang

    empty_card = Word.objects.filter(
        user=user, original_word=empty_original, language=empty_language).first()

    if empty_card:
        empty_card.translation = empty_translation
        empty_card.card_type = 'empty'
        empty_card.audio_file = word.audio_file
        empty_card.image_file = word.image_file
        empty_card.save()
        created = False
    else:
        empty_card = Word.objects.create(
            user=user,
            original_word=empty_original,
            translation=empty_translation,
            language=empty_language,
            card_type='empty',
            audio_file=word.audio_file,
            image_file=word.image_file,
        )
        created = True

    was_in_deck = empty_card in deck.words.all()
    if not was_in_deck:
        deck.words.add(empty_card)
        deck.save()

    return {
        'original_word': {
            'id': word.id,
            'original_word': word.original_word,
            'translation': word.translation,
            'language': word.language,
        },
        'empty_card': {
            'id': empty_card.id,
            'original_word': empty_card.original_word,
            'translation': empty_card.translation,
            'language': empty_card.language,
            'created': created,
            'added_to_deck': not was_in_deck,
        },
    }


def set_literary_source(user, deck_id: int, source_slug: str = None,
                        use_global: bool = False) -> dict:
    """Set literary source for a deck."""
    deck = Deck.objects.get(id=deck_id, user=user)

    if use_global:
        deck.literary_source_override = False
        deck.save(update_fields=['literary_source_override', 'updated_at'])
        return {'status': 'global'}

    if source_slug:
        from apps.literary_context.models import LiterarySource
        from django.shortcuts import get_object_or_404
        source = get_object_or_404(LiterarySource, slug=source_slug, is_active=True)
        deck.literary_source = source
        deck.literary_source_override = True
        deck.save(update_fields=['literary_source', 'literary_source_override', 'updated_at'])
        return {'status': 'source', 'source_slug': source.slug, 'source_name': source.name}

    deck.literary_source = None
    deck.literary_source_override = True
    deck.save(update_fields=['literary_source', 'literary_source_override', 'updated_at'])
    return {'status': 'standard'}


def _create_single_empty_card(user, deck: Deck, word: Word) -> dict | None:
    """Helper to create a single empty card. Returns result dict or None if already in deck."""
    empty_original = f"_empty_{word.id}"
    empty_translation = f"{word.original_word} // {word.translation}"
    empty_language = deck.target_lang

    empty_card = Word.objects.filter(
        user=user, original_word=empty_original, language=empty_language).first()

    if empty_card:
        empty_card.translation = empty_translation
        empty_card.card_type = 'empty'
        empty_card.audio_file = word.audio_file
        empty_card.image_file = word.image_file
        empty_card.save()
        created = False
    else:
        empty_card = Word.objects.create(
            user=user,
            original_word=empty_original,
            translation=empty_translation,
            language=empty_language,
            card_type='empty',
            audio_file=word.audio_file,
            image_file=word.image_file,
        )
        created = True

    if empty_card not in deck.words.all():
        deck.words.add(empty_card)
        return {
            'id': empty_card.id,
            'original_word': empty_card.original_word,
            'translation': empty_card.translation,
            'language': empty_card.language,
            'created': created,
        }

    return None
