"""
Утилиты для работы с промптами пользователей
"""
from typing import Optional
from django.contrib.auth import get_user_model
from .models import UserPrompt
from .default_prompts import get_default_prompt, format_prompt

User = get_user_model()


def get_user_prompt(
    user,
    prompt_type: str,
    use_default_if_not_exists: bool = True
) -> str:
    """
    Получает промпт пользователя или заводской промпт
    
    Args:
        user: Пользователь
        prompt_type: Тип промпта
        use_default_if_not_exists: Использовать заводской промпт, если пользовательский не найден
    
    Returns:
        Промпт (пользовательский или заводской)
    """
    try:
        user_prompt = UserPrompt.objects.get(user=user, prompt_type=prompt_type)
        return user_prompt.custom_prompt
    except UserPrompt.DoesNotExist:
        if use_default_if_not_exists:
            return get_default_prompt(prompt_type)
        return ''
    except Exception:
        # В случае ошибки возвращаем заводской промпт
        return get_default_prompt(prompt_type)


def get_or_create_user_prompt(user, prompt_type: str) -> UserPrompt:
    """
    Получает или создает промпт пользователя с заводским значением
    
    Args:
        user: Пользователь
        prompt_type: Тип промпта
    
    Returns:
        UserPrompt объект
    """
    user_prompt, created = UserPrompt.objects.get_or_create(
        user=user,
        prompt_type=prompt_type,
        defaults={
            'custom_prompt': get_default_prompt(prompt_type),
            'is_custom': False,
        }
    )
    return user_prompt


def reset_user_prompt_to_default(user, prompt_type: str) -> UserPrompt:
    """
    Сбрасывает промпт пользователя до заводских настроек
    
    Args:
        user: Пользователь
        prompt_type: Тип промпта
    
    Returns:
        UserPrompt объект
    """
    user_prompt = get_or_create_user_prompt(user, prompt_type)
    user_prompt.custom_prompt = get_default_prompt(prompt_type)
    user_prompt.is_custom = False
    user_prompt.save()
    return user_prompt

