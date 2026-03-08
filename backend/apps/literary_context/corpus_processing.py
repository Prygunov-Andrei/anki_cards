"""
Corpus processing: text splitting, keyword extraction, scene description generation.
"""
import json
import re
import logging
from typing import Optional

from apps.core.llm import get_openai_client
from .models import LiteraryContextSettings

logger = logging.getLogger(__name__)


def split_text_into_fragments(
    text: str,
    fragment_size: Optional[int] = None,
    overlap: Optional[int] = None,
) -> list[str]:
    """
    Split text into fragments by sentences, respecting fragment_size.

    Args:
        text: Full text to split.
        fragment_size: Target size in characters (from settings if None).
        overlap: Overlap in characters between fragments (from settings if None).

    Returns:
        List of text fragments.
    """
    if not text or not text.strip():
        return []

    config = LiteraryContextSettings.get()
    fragment_size = fragment_size or config.default_fragment_size
    overlap = overlap or config.fragment_overlap

    # Split into sentences (handles ., !, ?, ... followed by space or newline)
    sentence_pattern = re.compile(r'(?<=[.!?…])\s+')
    sentences = sentence_pattern.split(text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [text.strip()] if text.strip() else []

    fragments = []
    current_fragment = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        # If adding this sentence exceeds target size and we have content
        if current_length + sentence_len > fragment_size and current_fragment:
            fragments.append(' '.join(current_fragment))

            # Handle overlap: keep last sentences that fit within overlap size
            if overlap > 0:
                overlap_fragment = []
                overlap_length = 0
                for s in reversed(current_fragment):
                    if overlap_length + len(s) <= overlap:
                        overlap_fragment.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break
                current_fragment = overlap_fragment
                current_length = overlap_length
            else:
                current_fragment = []
                current_length = 0

        current_fragment.append(sentence)
        current_length += sentence_len

    # Don't forget the last fragment
    if current_fragment:
        last = ' '.join(current_fragment)
        # Avoid duplicate if identical to the previous fragment
        if not fragments or last != fragments[-1]:
            fragments.append(last)

    return fragments


def extract_keywords(
    fragment_text: str,
    language: str,
    config: Optional[LiteraryContextSettings] = None,
) -> list[str]:
    """
    Extract key words from a text fragment using LLM.

    Args:
        fragment_text: Text passage to extract keywords from.
        language: Language code of the text.
        config: Settings (loaded from DB if None).

    Returns:
        List of key words.
    """
    config = config or LiteraryContextSettings.get()
    client = get_openai_client()

    prompt = config.keyword_extraction_prompt.format(
        fragment_content=fragment_text
    )

    response = client.chat.completions.create(
        model=config.keyword_extraction_model,
        messages=[
            {
                'role': 'system',
                'content': (
                    f'You are a keyword extraction assistant. '
                    f'The text is in language code "{language}". '
                    f'Return a JSON array of strings, nothing else.'
                ),
            },
            {'role': 'user', 'content': prompt},
        ],
        temperature=config.keyword_temperature,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)

    try:
        keywords = json.loads(raw)
        if isinstance(keywords, list):
            return [str(kw).strip() for kw in keywords if kw]
    except json.JSONDecodeError:
        logger.warning(f'Failed to parse keywords JSON: {raw[:100]}')
        # Fallback: split by commas or newlines
        keywords = re.split(r'[,\n]', raw)
        return [kw.strip().strip('"\'') for kw in keywords if kw.strip()]

    return []


def extract_keywords_batch(
    texts: list[str],
    language: str,
    config: Optional[LiteraryContextSettings] = None,
) -> list[list[str]]:
    """
    Extract keywords from multiple text fragments.

    Args:
        texts: List of text passages.
        language: Language code of the texts.
        config: Settings (loaded from DB if None).

    Returns:
        List of keyword lists, one per input text.
    """
    config = config or LiteraryContextSettings.get()
    results = []
    for text in texts:
        try:
            keywords = extract_keywords(text, language, config)
        except Exception as e:
            logger.error(f'Keyword extraction failed for fragment: {e}')
            keywords = []
        results.append(keywords)
    return results


def generate_scene_description(
    fragment_text: str,
    language: str,
    config: Optional[LiteraryContextSettings] = None,
) -> dict:
    """
    Generate a visual scene description in English from a literary fragment.

    Args:
        fragment_text: Text passage to describe visually.
        language: Language code of the original text.
        config: Settings (loaded from DB if None).

    Returns:
        Dict with keys: description (str), characters (list[str]), mood (str).
    """
    config = config or LiteraryContextSettings.get()
    client = get_openai_client()

    prompt = config.scene_description_prompt.format(
        fragment_content=fragment_text
    )

    response = client.chat.completions.create(
        model=config.scene_description_model,
        messages=[
            {
                'role': 'system',
                'content': (
                    f'You are a scene description assistant. '
                    f'The text is in language code "{language}". '
                    f'Always respond in English with valid JSON.'
                ),
            },
            {'role': 'user', 'content': prompt},
        ],
        temperature=config.scene_description_temperature,
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()

    # Try to extract JSON from response (may be wrapped in ```json ... ```)
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
            return {
                'description': str(result.get('description', '')),
                'characters': list(result.get('characters', [])),
                'mood': str(result.get('mood', 'neutral')),
            }
        except json.JSONDecodeError:
            pass

    logger.warning(f'Failed to parse scene description JSON: {raw[:100]}')
    return {
        'description': raw[:500],
        'characters': [],
        'mood': 'neutral',
    }
