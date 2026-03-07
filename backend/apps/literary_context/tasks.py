"""
Celery-ready task functions for literary context generation.

These functions can be wrapped with @shared_task when Celery is added.
For now, they are called synchronously from views and management commands.

Usage (future):
    from celery import shared_task

    @shared_task
    def generate_word_context_task(word_id, source_slug):
        return _generate_word_context_task(word_id, source_slug)
"""
import logging

from .models import LiterarySource, WordContextMedia, LiteraryContextSettings

logger = logging.getLogger(__name__)


def generate_word_context_task(word_id: int, source_slug: str) -> dict:
    """Generate literary context for a single word (Celery-ready)."""
    from apps.words.models import Word
    from .generation import generate_word_context

    word = Word.objects.get(id=word_id)
    source = LiterarySource.objects.get(slug=source_slug)

    ctx = generate_word_context(word, source)
    return {
        'word_id': word_id,
        'is_fallback': ctx.is_fallback,
        'match_method': ctx.match_method,
    }


def generate_batch_context_task(
    word_ids: list[int],
    source_slug: str,
    skip_existing: bool = True,
) -> dict:
    """Generate literary context for multiple words (Celery-ready)."""
    from apps.words.models import Word
    from .generation import generate_batch_context

    source = LiterarySource.objects.get(slug=source_slug)
    words = Word.objects.filter(id__in=word_ids)

    return generate_batch_context(words, source, skip_existing=skip_existing)


def generate_scene_image_task(anchor_id: int) -> dict:
    """Generate a scene image for an anchor (Celery-ready)."""
    from .models import SceneAnchor
    from .image_generation import generate_scene_image

    anchor = SceneAnchor.objects.get(id=anchor_id)
    generate_scene_image(anchor)
    return {'anchor_id': anchor_id, 'success': True}
