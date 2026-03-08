"""
WordContextMedia generation pipeline:
  1. Find matching fragment via 3-tier search
  2. Enrich SceneAnchor (scene description + image)
  3. Extract sentences containing the word
  4. Generate hint text via LLM
  5. Create WordContextMedia record
"""
import json
import logging
import re
from typing import Optional, Callable

from apps.core.llm import get_openai_client
from .models import (
    LiterarySource, LiteraryFragment, WordContextMedia,
    LiteraryContextSettings,
)
from .search import find_matching_fragment

logger = logging.getLogger(__name__)


def _build_effective_config(config, user=None):
    """
    Build effective config by overlaying non-empty user settings onto system defaults.
    Empty strings and None values on user are ignored (fallback to config).
    """
    if user is None:
        return config

    # Overlay model fields
    for field in ('hint_generation_model', 'scene_description_model',
                  'matching_model', 'keyword_extraction_model'):
        user_val = getattr(user, field, '')
        if user_val:
            setattr(config, field, user_val)

    # Overlay temperatures (always set on user, use user value)
    for field in ('hint_temperature', 'scene_description_temperature',
                  'matching_temperature', 'keyword_temperature'):
        user_val = getattr(user, field, None)
        if user_val is not None:
            setattr(config, field, user_val)

    # Overlay prompt templates (only if non-empty)
    for field in ('hint_prompt_template', 'scene_description_prompt',
                  'keyword_extraction_prompt', 'image_prompt_template'):
        user_val = getattr(user, field, '')
        if user_val:
            setattr(config, field, user_val)

    return config


def _extract_sentences(content: str, word: str) -> list[str]:
    """Extract sentences containing the word (or its forms) from fragment content."""
    sentence_pattern = re.compile(r'(?<=[.!?…])\s+')
    sentences = sentence_pattern.split(content.strip())

    matching = []
    word_lower = word.lower()
    for s in sentences:
        if word_lower in s.lower():
            matching.append(s.strip())

    # If no exact match, return the first 2 sentences as context
    if not matching and sentences:
        matching = [s.strip() for s in sentences[:2]]

    return matching


def _generate_hint(
    word: str,
    translation: str,
    fragment_content: str,
    language: str,
    config: LiteraryContextSettings,
) -> str:
    """Generate a contextual hint for the word using LLM."""
    language_names = {
        'ru': 'Russian', 'en': 'English', 'de': 'German',
        'pt': 'Portuguese', 'es': 'Spanish', 'fr': 'French',
        'it': 'Italian', 'tr': 'Turkish',
    }
    language_name = language_names.get(language, 'English')

    prompt = config.hint_prompt_template.format(
        fragment_content=fragment_content,
        word=word,
        translation=translation,
        language_name=language_name,
    )

    client = get_openai_client()
    response = client.chat.completions.create(
        model=config.hint_generation_model,
        messages=[
            {
                'role': 'system',
                'content': (
                    f'You are a hint generation assistant for language learning. '
                    f'Create a short, memorable hint in {language_name}.'
                ),
            },
            {'role': 'user', 'content': prompt},
        ],
        temperature=config.hint_temperature,
        max_tokens=150,
    )

    return response.choices[0].message.content.strip()


def enrich_anchor(anchor, fragment, config):
    """
    Enrich a SceneAnchor with scene description and image if missing.

    Args:
        anchor: SceneAnchor instance.
        fragment: LiteraryFragment instance (for content).
        config: LiteraryContextSettings instance.
    """
    # Step 1: Generate scene description if missing
    if not anchor.scene_description:
        try:
            from .corpus_processing import generate_scene_description
            scene_data = generate_scene_description(
                fragment.content,
                fragment.text.language,
                config,
            )
            anchor.scene_description = scene_data['description']
            anchor.characters = scene_data['characters']
            valid_moods = [c[0] for c in anchor._meta.get_field('mood').choices]
            if scene_data['mood'] in valid_moods:
                anchor.mood = scene_data['mood']
            anchor.save(update_fields=[
                'scene_description', 'characters', 'mood',
            ])
            logger.info(f'Scene description generated for anchor {anchor.id}')
        except Exception as e:
            logger.error(f'Failed to generate scene description for anchor {anchor.id}: {e}')

    # Step 2: Generate image if missing
    if not anchor.image_file and anchor.scene_description:
        try:
            from .image_generation import generate_scene_image
            generate_scene_image(anchor, config)
        except Exception as e:
            logger.error(f'Failed to generate scene image for anchor {anchor.id}: {e}')


def generate_word_context(
    word,
    source: LiterarySource,
    config: Optional[LiteraryContextSettings] = None,
    skip_hint: bool = False,
    user=None,
) -> WordContextMedia:
    """
    Generate literary context media for a word.

    Args:
        word: Word model instance (has original_word, translation, language).
        source: Literary source to search within.
        config: Settings (loaded from DB if None).
        skip_hint: Skip LLM hint generation.
        user: User instance for per-user settings override.

    Returns:
        WordContextMedia instance (created or updated).
    """
    config = config or LiteraryContextSettings.get()
    config = _build_effective_config(config, user)

    # Step 1: Find matching fragment
    fragment, match_method, match_score = find_matching_fragment(
        word=word.original_word,
        translation=word.translation,
        source=source,
        language=word.language,
        config=config,
    )

    # Step 2: Extract sentences and generate hint
    sentences = []
    hint_text = ''
    anchor = None
    is_fallback = fragment is None

    if fragment:
        anchor = fragment.anchor
        sentences = _extract_sentences(fragment.content, word.original_word)

        # Step 2b: Enrich anchor (scene description + image)
        enrich_anchor(anchor, fragment, config)

        if not skip_hint:
            try:
                hint_text = _generate_hint(
                    word=word.original_word,
                    translation=word.translation,
                    fragment_content=fragment.content,
                    language=word.language,
                    config=config,
                )
            except Exception as e:
                logger.error(f'Failed to generate hint for "{word.original_word}": {e}')

    # Step 2c: Generate hint audio
    hint_audio_path = ''
    if hint_text:
        try:
            from .audio_generation import generate_literary_audio
            voice_id = getattr(user, 'elevenlabs_voice_id', '') if user else ''
            audio_path = generate_literary_audio(
                hint_text, word.language,
                voice_id=voice_id or None,
                subdir='literary_hints',
            )
            if audio_path:
                hint_audio_path = audio_path
        except Exception as e:
            logger.error(f'Failed to generate hint audio for "{word.original_word}": {e}')

    # Step 3: Create or update WordContextMedia
    defaults = {
        'anchor': anchor,
        'fragment': fragment,
        'hint_text': hint_text,
        'sentences': [{'text': s, 'source': source.slug} for s in sentences],
        'is_fallback': is_fallback,
        'match_method': match_method,
        'match_score': match_score,
    }
    if hint_audio_path:
        defaults['hint_audio'] = hint_audio_path

    context_media, _ = WordContextMedia.objects.update_or_create(
        word=word,
        source=source,
        defaults=defaults,
    )

    return context_media


def generate_batch_context(
    words,
    source: LiterarySource,
    config: Optional[LiteraryContextSettings] = None,
    skip_existing: bool = True,
    skip_hint: bool = False,
    force: bool = False,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
    user=None,
) -> dict:
    """
    Generate literary context for multiple words.

    Args:
        words: Queryset or list of Word instances.
        source: Literary source to search within.
        config: Settings (loaded from DB if None).
        skip_existing: Skip words that already have context media.
        skip_hint: Skip LLM hint generation.
        force: Force regeneration even if context media exists.
        on_progress: Callback(current, total, word_text) for progress reporting.
        user: User instance for per-user settings override.

    Returns:
        Stats dict with keys: total, generated, skipped, fallback, errors, unmatched_words.
    """
    config = config or LiteraryContextSettings.get()
    config = _build_effective_config(config, user)
    word_list = list(words)
    total = len(word_list)
    stats = {
        'total': total,
        'generated': 0,
        'skipped': 0,
        'fallback': 0,
        'errors': 0,
        'unmatched_words': [],
    }

    for i, word in enumerate(word_list):
        if on_progress:
            on_progress(i, total, word.original_word)

        if not force and skip_existing and WordContextMedia.objects.filter(word=word, source=source).exists():
            stats['skipped'] += 1
            continue

        try:
            ctx = generate_word_context(word, source, config, skip_hint=skip_hint, user=user)
            stats['generated'] += 1
            if ctx.is_fallback:
                stats['fallback'] += 1
                stats['unmatched_words'].append({
                    'id': word.id,
                    'original_word': word.original_word,
                    'translation': word.translation,
                })
        except Exception as e:
            logger.error(f'Failed to generate context for "{word.original_word}": {e}')
            stats['errors'] += 1

    if on_progress:
        on_progress(total, total, '')

    return stats
