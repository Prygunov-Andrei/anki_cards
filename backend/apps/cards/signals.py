import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.words.models import Word
from .models import Card

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Word)
def create_card_for_new_word(sender, instance, created, **kwargs):
    """
    При создании нового слова автоматически создаём normal-карточку.
    
    Это гарантирует, что каждое слово имеет хотя бы одну карточку
    для тренировки сразу после добавления.
    """
    if created:
        try:
            Card.create_from_word(instance, 'normal')
        except Exception:
            logger.exception(
                "Failed to create card for word id=%s ('%s')",
                instance.id, instance.original_word
            )
