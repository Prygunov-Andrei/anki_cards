"""
Django signals для автоматического обновления статуса слов
"""
import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .utils import update_word_learning_status

logger = logging.getLogger(__name__)


@receiver(post_save, sender='cards.Card')
@receiver(post_delete, sender='cards.Card')
def update_word_status_on_card_change(sender, instance, **kwargs):
    """
    Обновляет learning_status слова при изменении его карточек.
    
    Вызывается при:
    - Создании новой карточки
    - Обновлении карточки (например, изменение is_in_learning_mode, next_review)
    - Удалении карточки
    """
    if instance.word:
        try:
            update_word_learning_status(instance.word)
        except Exception:
            logger.exception(
                "Failed to update learning status for word id=%s",
                instance.word_id
            )
