import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserTrainingSettings

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_training_settings_for_new_user(sender, instance, created, **kwargs):
    """
    При создании нового пользователя автоматически создаём настройки тренировки.
    
    Использует age_group из атрибутов пользователя, если он был передан
    при создании (например, через сигнал регистрации).
    """
    if created:
        # Пытаемся получить age_group из атрибутов пользователя
        # (устанавливается в процессе регистрации)
        age_group = getattr(instance, '_age_group', 'adult')
        UserTrainingSettings.create_for_user(instance, age_group)


@receiver(post_save, sender='words.Word')
def auto_generate_etymology(sender, instance, created, **kwargs):
    """
    Автоматически генерирует этимологию при создании нового слова
    
    Условия:
    - Слово только что создано (created=True)
    - У пользователя достаточно токенов (>= 1 токен = 2 единицы)
    - Этимология ещё не заполнена
    - Пользователь не отключил автоматическую генерацию (опционально, через атрибут)
    """
    if not created:
        return
    
    # Проверяем, что этимология не заполнена
    if instance.etymology:
        return  # Этимология уже есть
    
    # Проверка, отключена ли автоматическая генерация (через атрибут)
    if getattr(instance, '_skip_etymology_generation', False):
        return
    
    # Проверка баланса
    from apps.cards.token_utils import check_balance
    balance = check_balance(instance.user)
    if balance < 1:  # Минимум 1 токен
        logger.info(
            "Insufficient tokens for auto-etymology, word id=%s, balance=%s",
            instance.id, balance
        )
        return
    
    try:
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from .ai_generation import generate_etymology
        
        etymology = generate_etymology(
            word=instance.original_word,
            translation=instance.translation,
            language=instance.language,
            user=instance.user
        )
        
        # Обновляем этимологию (используем update для избежания повторного сигнала)
        sender.objects.filter(id=instance.id).update(etymology=etymology)
        
        logger.info(
            "Auto-generated etymology for word id=%s ('%s')",
            instance.id, instance.original_word
        )
    except Exception:
        logger.exception(
            "Failed to auto-generate etymology for word id=%s ('%s')",
            instance.id, instance.original_word
        )
