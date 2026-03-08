"""
3-tier word-to-fragment matching:
  Tier A: Keyword match (always available)
  Tier B: Semantic similarity via pgvector (if available)
  Tier C: LLM-based matching (if enabled in settings)
"""
import json
import logging
import re
from typing import Optional

from django.db.models import Q

from apps.core.llm import get_openai_client
from .models import (
    LiteraryFragment, LiterarySource, LiteraryContextSettings,
)

logger = logging.getLogger(__name__)

# Graceful pgvector import
try:
    from pgvector.django import CosineDistance
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    logger.info('pgvector not available, semantic search disabled')


def find_matching_fragment(
    word: str,
    translation: str,
    source: LiterarySource,
    language: str,
    config: Optional[LiteraryContextSettings] = None,
) -> tuple[Optional[LiteraryFragment], str, float]:
    """
    Find the best matching fragment for a word using 3-tier matching.

    Args:
        word: The word to match (in target language, e.g. "Hund").
        translation: Translation of the word (e.g. "dog", "собака").
        source: Literary source to search within.
        language: Language code of fragments to search.
        config: Settings (loaded from DB if None).

    Returns:
        Tuple of (fragment or None, match_method, score).
        match_method: 'keyword', 'semantic', 'llm', or 'none'.
    """
    config = config or LiteraryContextSettings.get()

    # Tier A: Keyword match
    fragment, score = _keyword_match(word, translation, source, language)
    if fragment:
        return fragment, 'keyword', score

    # Tier B: Semantic search (if pgvector available and fragment has embeddings)
    if HAS_PGVECTOR:
        fragment, score = _semantic_match(word, translation, source, language, config)
        if fragment and score >= config.semantic_match_min_score:
            return fragment, 'semantic', score

    # Tier C: LLM matching (if enabled)
    if config.llm_match_enabled:
        fragment, score = _llm_match(word, translation, source, language, config)
        if fragment:
            return fragment, 'llm', score

    return None, 'none', 0.0


def _keyword_match(
    word: str,
    translation: str,
    source: LiterarySource,
    language: str,
) -> tuple[Optional[LiteraryFragment], float]:
    """Tier A: Match by keyword in key_words JSON field."""
    fragments = LiteraryFragment.objects.filter(
        anchor__source=source,
        text__language=language,
    )

    # Try exact match on word first
    for fragment in fragments:
        for kw in fragment.key_words:
            if kw.lower() == word.lower():
                return fragment, 1.0

    # Try case-insensitive contains on word
    for fragment in fragments:
        for kw in fragment.key_words:
            if word.lower() in kw.lower() or kw.lower() in word.lower():
                return fragment, 0.8

    # Try translation
    for fragment in fragments:
        for kw in fragment.key_words:
            if kw.lower() == translation.lower():
                return fragment, 0.7

    # Try content contains (word appears directly in fragment text)
    for fragment in fragments:
        if word.lower() in fragment.content.lower():
            return fragment, 0.6

    return None, 0.0


def _semantic_match(
    word: str,
    translation: str,
    source: LiterarySource,
    language: str,
    config: LiteraryContextSettings,
) -> tuple[Optional[LiteraryFragment], float]:
    """Tier B: Semantic similarity via pgvector."""
    if not HAS_PGVECTOR:
        return None, 0.0

    from .embedding_utils import generate_embedding

    # Generate embedding for the word + translation context
    query_text = f"{word} ({translation})"
    try:
        query_embedding = generate_embedding(query_text, config)
    except Exception as e:
        logger.warning(f'Failed to generate embedding for "{query_text}": {e}')
        return None, 0.0

    # Find closest fragment by cosine distance
    fragments = (
        LiteraryFragment.objects
        .filter(
            anchor__source=source,
            text__language=language,
            embedding__isnull=False,
        )
        .annotate(distance=CosineDistance('embedding', query_embedding))
        .order_by('distance')
    )

    first = fragments.first()
    if first is None:
        return None, 0.0

    # Convert cosine distance to similarity (1 - distance)
    similarity = 1.0 - first.distance
    return first, similarity


def _llm_match(
    word: str,
    translation: str,
    source: LiterarySource,
    language: str,
    config: LiteraryContextSettings,
) -> tuple[Optional[LiteraryFragment], float]:
    """Tier C: LLM-based matching with top candidates."""
    fragments = list(
        LiteraryFragment.objects
        .filter(anchor__source=source, text__language=language)
        .select_related('anchor')[:10]
    )

    if not fragments:
        return None, 0.0

    # Build candidate list for LLM
    candidates = []
    for i, frag in enumerate(fragments):
        preview = frag.content[:200]
        candidates.append(f"{i}. [{', '.join(frag.key_words[:5])}] {preview}")

    candidates_text = '\n'.join(candidates)

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=config.matching_model,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are a word-to-scene matching assistant. '
                        'Given a word and its translation, select the most relevant '
                        'literary fragment from the candidates. '
                        'Return JSON: {"index": <number>, "confidence": <0.0-1.0>}. '
                        'If no fragment is relevant, return {"index": -1, "confidence": 0}.'
                    ),
                },
                {
                    'role': 'user',
                    'content': (
                        f'Word: {word}\nTranslation: {translation}\n\n'
                        f'Candidates:\n{candidates_text}'
                    ),
                },
            ],
            temperature=config.matching_temperature,
            max_tokens=50,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith('```'):
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
        try:
            result = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f'LLM match JSON parse error for "{word}": {e}, raw: {raw[:100]}')
            return None, 0.0

        idx = int(result.get('index', -1))
        confidence = float(result.get('confidence', 0))

        if 0 <= idx < len(fragments) and confidence > 0:
            return fragments[idx], confidence

    except Exception as e:
        logger.warning(f'LLM matching failed for "{word}": {e}')

    return None, 0.0
