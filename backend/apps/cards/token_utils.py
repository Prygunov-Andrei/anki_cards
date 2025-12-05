"""
Утилиты для работы с токенами
"""
import logging
from typing import Optional, Tuple
from django.contrib.auth import get_user_model
from .models import Token, TokenTransaction

User = get_user_model()
logger = logging.getLogger(__name__)

# Стоимость операций
IMAGE_GENERATION_COST = 1  # По умолчанию (для OpenAI и Gemini Pro)
AUDIO_GENERATION_COST = 1

# Стоимость для разных моделей Gemini
GEMINI_FLASH_COST = 0.5  # Быстрая модель (gemini-2.5-flash-image)
GEMINI_PRO_COST = 1.0    # Новая модель (nano-banana-pro-preview)


def get_image_generation_cost(provider: str = 'openai', gemini_model: str = None) -> float:
    """
    Возвращает стоимость генерации изображения в зависимости от провайдера и модели
    
    Args:
        provider: Провайдер ('openai' или 'gemini')
        gemini_model: Модель Gemini (если provider='gemini')
    
    Returns:
        Стоимость в токенах (float)
    """
    if provider == 'openai':
        return float(IMAGE_GENERATION_COST)
    elif provider == 'gemini':
        if gemini_model == 'gemini-2.5-flash-image':
            return GEMINI_FLASH_COST
        elif gemini_model == 'nano-banana-pro-preview':
            return GEMINI_PRO_COST
        else:
            # По умолчанию для Gemini - быстрая модель
            return GEMINI_FLASH_COST
    else:
        return float(IMAGE_GENERATION_COST)


def get_or_create_token(user) -> Token:
    """
    Получает или создает токен для пользователя
    
    Args:
        user: Пользователь
    
    Returns:
        Объект Token
    """
    token, created = Token.objects.get_or_create(user=user)
    return token


def add_tokens(user, amount: int, description: str = "") -> Token:
    """
    Начисляет токены пользователю
    
    Args:
        user: Пользователь
        amount: Количество токенов для начисления (в реальных токенах)
        description: Описание операции
    
    Returns:
        Обновленный объект Token
    """
    if amount <= 0:
        raise ValueError("Количество токенов должно быть положительным")
    
    token = get_or_create_token(user)
    # Конвертируем токены в внутренний формат (1 токен = 2 единицы в БД)
    amount_internal = amount * 2
    token.balance += amount_internal
    token.save()
    
    # Создаем транзакцию
    TokenTransaction.objects.create(
        user=user,
        transaction_type='earned',
        amount=amount,
        description=description or f"Начислено {amount} токенов"
    )
    
    balance_display = token.balance / 2.0
    logger.info(f"Начислено {amount} токенов пользователю {user.username} (ID: {user.id}). Баланс: {balance_display}")
    return token


def spend_tokens(user, amount: int, description: str = "") -> Tuple[Token, bool]:
    """
    Списывает токены у пользователя
    
    Args:
        user: Пользователь
        amount: Количество токенов для списания
        description: Описание операции
    
    Returns:
        Tuple[Token, bool]: (обновленный объект Token, успех операции)
    """
    if amount <= 0:
        raise ValueError("Количество токенов должно быть положительным")
    
    token = get_or_create_token(user)
    
    if token.balance < amount:
        logger.warning(f"Недостаточно токенов у пользователя {user.username}. Баланс: {token.balance}, требуется: {amount}")
        return token, False
    
    token.balance -= amount
    token.save()
    
    # Создаем транзакцию
    TokenTransaction.objects.create(
        user=user,
        transaction_type='spent',
        amount=amount,
        description=description or f"Потрачено {amount} токенов"
    )
    
    balance_display = token.balance / 2.0
    logger.info(f"Списано {amount} единиц у пользователя {user.username} (ID: {user.id}). Баланс: {balance_display} токенов")
    return token, True


def refund_tokens(user, amount: int, description: str = "") -> Token:
    """
    Возвращает токены пользователю (refund)
    
    Args:
        user: Пользователь
        amount: Количество токенов для возврата
        description: Описание операции
    
    Returns:
        Обновленный объект Token
    """
    if amount <= 0:
        raise ValueError("Количество токенов должно быть положительным")
    
    token = get_or_create_token(user)
    token.balance += amount
    token.save()
    
    # Создаем транзакцию
    TokenTransaction.objects.create(
        user=user,
        transaction_type='refund',
        amount=amount,
        description=description or f"Возвращено {amount} токенов"
    )
    
    balance_display = token.balance / 2.0
    logger.info(f"Возвращено {amount} единиц пользователю {user.username} (ID: {user.id}). Баланс: {balance_display} токенов")
    return token


def check_balance(user) -> int:
    """
    Проверяет баланс токенов пользователя
    
    Args:
        user: Пользователь
    
    Returns:
        Текущий баланс токенов (целое число)
    """
    token = get_or_create_token(user)
    return token.balance

