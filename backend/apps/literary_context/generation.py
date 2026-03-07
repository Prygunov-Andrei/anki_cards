"""
WordContextMedia generation pipeline:
  1. Find matching fragment via 3-tier search
  2. Extract sentences containing the word
  3. Generate hint text via LLM
  4. Create WordContextMedia record
"""
import json
import logging
import re
from typing import Optional

from apps.cards.llm_utils import get_openai_client
from .models import (
    LiterarySource, LiteraryFragment, WordContextMedia,
    LiteraryContextSettings,
)
from .search import find_matching_fragment

logger = logging.getLogger(__name__)


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


def generate_word_context(
    word,
    source: LiterarySource,
    config: Optional[LiteraryContextSettings] = None,
    skip_hint: bool = False,
) -> WordContextMedia:
    """
    Generate literary context media for a word.

    Args:
        word: Word model instance (has original_word, translation, language).
        source: Literary source to search within.
        config: Settings (loaded from DB if None).
        skip_hint: Skip LLM hint generation.

    Returns:
        WordContextMedia instance (created or updated).
    """
    config = config or LiteraryContextSettings.get()

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

    # Step 3: Create or update WordContextMedia
    context_media, _ = WordContextMedia.objects.update_or_create(
        word=word,
        source=source,
        defaults={
            'anchor': anchor,
            'fragment': fragment,
            'hint_text': hint_text,
            'sentences': [{'text': s, 'source': source.slug} for s in sentences],
            'is_fallback': is_fallback,
            'match_method': match_method,
            'match_score': match_score,
        },
    )

    return context_media


def generate_batch_context(
    words,
    source: LiterarySource,
    config: Optional[LiteraryContextSettings] = None,
    skip_existing: bool = True,
    skip_hint: bool = False,
) -> dict:
    """
    Generate literary context for multiple words.

    Args:
        words: Queryset or list of Word instances.
        source: Literary source to search within.
        config: Settings (loaded from DB if None).
        skip_existing: Skip words that already have context media.
        skip_hint: Skip LLM hint generation.

    Returns:
        Stats dict: {total, generated, skipped, fallback, errors}.
    """
    config = config or LiteraryContextSettings.get()
    stats = {'total': 0, 'generated': 0, 'skipped': 0, 'fallback': 0, 'errors': 0}

    for word in words:
        stats['total'] += 1

        if skip_existing and WordContextMedia.objects.filter(word=word, source=source).exists():
            stats['skipped'] += 1
            continue

        try:
            ctx = generate_word_context(word, source, config, skip_hint=skip_hint)
            stats['generated'] += 1
            if ctx.is_fallback:
                stats['fallback'] += 1
        except Exception as e:
            logger.error(f'Failed to generate context for "{word.original_word}": {e}')
            stats['errors'] += 1

    return stats
