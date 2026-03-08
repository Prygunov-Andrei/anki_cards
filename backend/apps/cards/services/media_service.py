"""
Media service: path normalization, file upload, image/audio generation orchestration.
"""
import uuid
import logging
from pathlib import Path

from django.conf import settings

from apps.words.models import Word
from apps.cards.llm_utils import (
    generate_image,
    generate_audio_with_tts,
    edit_image_with_gemini,
    extract_words_from_photo,
)
from apps.cards.token_utils import (
    spend_tokens,
    refund_tokens,
    check_balance,
    get_image_generation_cost,
)
from apps.core.constants import (
    AUDIO_GENERATION_COST,
    IMAGE_GENERATION_COST,
    IMAGE_EDIT_COST,
    PHOTO_OCR_COST,
)

logger = logging.getLogger(__name__)


def normalize_media_path(raw_path: str, media_subdir: str = '') -> Path | None:
    """
    Normalize a media path from various formats to an absolute Path.

    Handles:
    - Full URLs (https://.../media/images/file.jpg)
    - Absolute paths (/var/www/media/images/file.jpg)
    - /media/ prefixed paths (/media/images/file.jpg)
    - Relative paths (images/file.jpg)

    Args:
        raw_path: The raw path string (URL, absolute, or relative).
        media_subdir: Optional subdirectory hint (e.g. 'audio', 'images')
            used when extracting from URLs.

    Returns:
        Absolute Path to the file, or None if input is empty.
    """
    if not raw_path:
        return None

    media_root = Path(settings.MEDIA_ROOT)

    # Full URL — extract relative path
    if raw_path.startswith(('http://', 'https://')):
        media_marker = f'/media/{media_subdir}/' if media_subdir else '/media/'
        if media_marker in raw_path:
            relative = (f'{media_subdir}/' if media_subdir else '') + raw_path.split(media_marker)[-1]
            return media_root / relative
        if '/media/' in raw_path:
            return media_root / raw_path.split('/media/')[-1]
        # Last resort: take filename
        if media_subdir:
            return media_root / media_subdir / raw_path.split('/')[-1]
        return None

    # /media/ prefixed path
    if raw_path.startswith('/media/'):
        return media_root / raw_path[len('/media/'):]

    # Already absolute
    if Path(raw_path).is_absolute():
        return Path(raw_path)

    # Relative path
    return media_root / raw_path


def get_relative_media_path(absolute_path: Path) -> str:
    """Convert absolute path to relative path from MEDIA_ROOT."""
    media_root = Path(settings.MEDIA_ROOT)
    return str(absolute_path.relative_to(media_root))


def get_media_url(relative_path: str) -> str:
    """Build media URL from relative path."""
    return f"{settings.MEDIA_URL}{relative_path}"


def resolve_word_media(word_text: str, media_files_dict: dict, word_obj: Word,
                       media_type: str) -> tuple[Path | None, bool]:
    """
    Resolve media file for a word: try exact match, then normalized match,
    then fall back to existing DB media.

    Args:
        word_text: The word text to look up.
        media_files_dict: Dict of {word: path_string} from user input.
        word_obj: The Word model instance.
        media_type: 'audio' or 'images'.

    Returns:
        (absolute_path, is_new) — path to media file and whether it's new or from DB.
    """
    # Try exact match
    raw_path = media_files_dict.get(word_text)

    # Try normalized match
    if not raw_path:
        word_normalized = word_text.strip().rstrip('.,!?;:')
        for key, path in media_files_dict.items():
            key_normalized = key.strip().rstrip('.,!?;:')
            if key_normalized == word_normalized or key.strip() == word_text.strip():
                raw_path = path
                break

    if raw_path:
        abs_path = normalize_media_path(raw_path, media_subdir=media_type)
        if abs_path and abs_path.exists():
            return abs_path, True
        logger.error(f"Media file not found: {abs_path} (raw: {raw_path})")
        return None, False

    # Fall back to existing DB media
    file_field = word_obj.audio_file if media_type == 'audio' else word_obj.image_file
    if file_field:
        existing_path = Path(settings.MEDIA_ROOT) / file_field.name
        if existing_path.exists():
            return existing_path, False

    return None, False


def save_uploaded_file(uploaded_file, subdir: str, allowed_extensions: list[str] = None) -> tuple[Path, str]:
    """
    Save an uploaded file to MEDIA_ROOT/subdir/ with a unique name.

    Returns:
        (absolute_path, file_id)
    """
    file_id = str(uuid.uuid4())
    ext = Path(uploaded_file.name).suffix.lower()

    if allowed_extensions and ext not in allowed_extensions:
        ext = allowed_extensions[0]

    filename = f"{file_id}{ext}"
    target_dir = Path(settings.MEDIA_ROOT) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / filename
    with open(file_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    return file_path, file_id


def generate_image_for_word(user, word: str, translation: str, language: str,
                            word_id: int = None, image_style: str = 'balanced',
                            provider: str = None, gemini_model: str = None) -> dict:
    """
    Generate image for a word, handle token spending/refund, save to Word model.

    Returns dict with image_url, image_id, file_path, prompt.
    Raises ValueError for validation errors, RuntimeError for generation errors.
    """
    # Resolve inverted words
    if word_id:
        try:
            word_obj = Word.objects.get(id=word_id, user=user)
            if word_obj.card_type == 'inverted':
                word, translation = word_obj.translation, word_obj.original_word
        except Word.DoesNotExist:
            pass

    # Resolve provider
    if not provider or provider == 'auto':
        provider = getattr(user, 'image_provider', 'openai')
    if provider == 'gemini' and not gemini_model:
        gemini_model = getattr(user, 'gemini_model', 'gemini-2.5-flash-image')

    cost = get_image_generation_cost(provider=provider, gemini_model=gemini_model)
    cost = max(1, int(cost))

    balance = check_balance(user)
    if balance < cost:
        raise ValueError(f'Недостаточно токенов. Требуется: {cost}, доступно: {balance}')

    token, success = spend_tokens(user, cost,
        description=f"Image generation for '{word}' ({provider}, model: {gemini_model or 'N/A'})")
    if not success:
        raise ValueError(f'Недостаточно токенов для генерации изображения. Требуется: {cost}')

    try:
        image_path, prompt = generate_image(
            word=word, translation=translation, language=language,
            user=user,
            native_language=getattr(user, 'native_language', 'ru'),
            english_translation=None,
            image_style=image_style,
            provider=provider,
            gemini_model=gemini_model,
        )

        relative_path = get_relative_media_path(image_path)
        image_url = get_media_url(relative_path)

        # Bind to word if word_id provided
        if word_id:
            try:
                word_obj = Word.objects.get(id=word_id, user=user)
                word_obj.image_file.name = relative_path
                word_obj.save()
            except Word.DoesNotExist:
                pass

        return {
            'image_url': image_url,
            'image_id': image_path.stem,
            'file_path': str(image_path),
            'prompt': prompt,
        }
    except Exception:
        refund_tokens(user, cost, description=f"Refund for image generation error for '{word}'")
        raise


def edit_image_for_word(user, word_id: int, mixin: str) -> dict:
    """
    Edit an existing word's image via Gemini image-to-image.

    Returns dict with image_url, image_id, file_path, prompt, mixin, word_id.
    """
    word_obj = Word.objects.get(id=word_id, user=user)

    if not word_obj.image_file:
        raise ValueError('У этого слова нет изображения для редактирования. Сначала сгенерируйте изображение.')

    source_path = Path(settings.MEDIA_ROOT) / word_obj.image_file.name
    if not source_path.exists():
        raise FileNotFoundError(f'Image file not found: {word_obj.image_file.name}')

    cost = IMAGE_EDIT_COST
    balance = check_balance(user)
    if balance < cost:
        raise ValueError(f'Недостаточно токенов. Требуется: {cost}, доступно: {balance}')

    token, success = spend_tokens(user, cost,
        description=f"Image edit for '{word_obj.original_word}' (mixin: '{mixin}')")
    if not success:
        raise ValueError(f'Недостаточно токенов. Требуется: {cost}')

    try:
        new_image_path, prompt = edit_image_with_gemini(
            source_image_path=source_path,
            mixin=mixin,
            user=user,
            model='gemini-3.1-flash-image-preview',
        )

        relative_path = get_relative_media_path(new_image_path)
        image_url = get_media_url(relative_path)

        word_obj.image_file.name = relative_path
        word_obj.save()

        return {
            'image_url': image_url,
            'image_id': new_image_path.stem,
            'file_path': str(new_image_path),
            'prompt': prompt,
            'mixin': mixin,
            'word_id': word_id,
        }
    except Exception:
        refund_tokens(user, cost,
            description=f"Refund for image edit error for '{word_obj.original_word}'")
        raise


def generate_audio_for_word(user, word: str, language: str,
                            word_id: int = None, provider: str = None) -> dict:
    """
    Generate audio for a word, handle tokens, save to Word model.

    Returns dict with audio_url, audio_id, file_path.
    """
    if not provider:
        provider = getattr(user, 'audio_provider', 'openai')

    # Portuguese defaults to gTTS
    if language == 'pt' and provider == 'openai':
        if not hasattr(user, 'audio_provider') or user.audio_provider == 'openai':
            provider = 'gtts'

    # Check/spend tokens (only for OpenAI)
    if provider == 'openai':
        balance = check_balance(user)
        if balance < AUDIO_GENERATION_COST:
            raise ValueError(
                f'Недостаточно токенов. Требуется: {AUDIO_GENERATION_COST}, доступно: {balance}')

        token, success = spend_tokens(user, AUDIO_GENERATION_COST,
            description=f"Audio generation for '{word}' (OpenAI TTS)")
        if not success:
            raise ValueError('Недостаточно токенов для генерации аудио')

    try:
        audio_path = generate_audio_with_tts(
            word=word, language=language, user=user, provider=provider)

        relative_path = get_relative_media_path(audio_path)
        audio_url = get_media_url(relative_path)

        if word_id:
            try:
                word_obj = Word.objects.get(id=word_id, user=user)
                word_obj.audio_file.name = relative_path
                word_obj.save()
            except Word.DoesNotExist:
                pass

        return {
            'audio_url': audio_url,
            'audio_id': audio_path.stem,
            'file_path': str(audio_path),
        }
    except Exception:
        if provider == 'openai':
            refund_tokens(user, AUDIO_GENERATION_COST,
                description=f"Refund for audio generation error for '{word}'")
        raise


def extract_words_from_photo_service(user, image_data: bytes,
                                     target_lang: str, source_lang: str) -> list[str]:
    """Extract words from photo via LLM vision, handling tokens."""
    balance = check_balance(user)
    if balance < PHOTO_OCR_COST:
        raise ValueError(
            f'Недостаточно токенов. Требуется: {PHOTO_OCR_COST}, доступно: {balance}')

    token, success = spend_tokens(user, PHOTO_OCR_COST,
        description=f"Photo word extraction ({target_lang} -> {source_lang})")
    if not success:
        raise ValueError('Не удалось списать токены')

    try:
        return extract_words_from_photo(
            image_data=image_data,
            target_lang=target_lang,
            source_lang=source_lang,
        )
    except Exception:
        refund_tokens(user, PHOTO_OCR_COST,
            description="Refund for photo extraction error")
        raise
