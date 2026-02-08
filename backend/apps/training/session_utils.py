"""
Утилиты для формирования очереди карточек для тренировочных сессий.
"""
from typing import Dict, List, Optional
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from apps.cards.models import Card, Deck
from apps.words.models import Category
from .models import UserTrainingSettings


# Константы времени на карточку (в минутах)
TIME_PER_LEARNING_CARD = 2.5
TIME_PER_REVIEW_CARD = 0.25
TIME_PER_NEW_CARD = 2.5


def estimate_session_time(
    learning_count: int,
    review_count: int,
    new_count: int
) -> int:
    """
    Оценивает время сессии в минутах.
    
    Args:
        learning_count: Количество карточек в режиме обучения
        review_count: Количество карточек на повторение
        new_count: Количество новых карточек
    
    Returns:
        int: Оценка времени в минутах
    """
    total_minutes = (
        learning_count * TIME_PER_LEARNING_CARD +
        review_count * TIME_PER_REVIEW_CARD +
        new_count * TIME_PER_NEW_CARD
    )
    return int(total_minutes)


def limit_cards_by_time(
    learning_cards: List[Card],
    review_cards: List[Card],
    new_cards: List[Card],
    duration_minutes: int
) -> List[Card]:
    """
    Ограничивает количество карточек по времени.
    
    Возвращает подмножество карточек, которое помещается в указанное время.
    Приоритет: learning → review → new
    
    Args:
        learning_cards: Карточки в режиме обучения
        review_cards: Карточки на повторение
        new_cards: Новые карточки
        duration_minutes: Доступное время в минутах
    
    Returns:
        List[Card]: Ограниченный список карточек
    """
    result = []
    remaining_time = duration_minutes
    
    # 1. Добавляем карточки в режиме обучения
    for card in learning_cards:
        if remaining_time >= TIME_PER_LEARNING_CARD:
            result.append(card)
            remaining_time -= TIME_PER_LEARNING_CARD
        else:
            break
    
    # 2. Добавляем карточки на повторение
    for card in review_cards:
        if remaining_time >= TIME_PER_REVIEW_CARD:
            result.append(card)
            remaining_time -= TIME_PER_REVIEW_CARD
        else:
            break
    
    # 3. Добавляем новые карточки
    for card in new_cards:
        if remaining_time >= TIME_PER_NEW_CARD:
            result.append(card)
            remaining_time -= TIME_PER_NEW_CARD
        else:
            break
    
    return result


def _empty_queue() -> Dict:
    """Возвращает пустую очередь карточек."""
    return {
        'cards': [],
        'new_count': 0,
        'review_count': 0,
        'learning_count': 0,
        'estimated_time': 0,
        'total_count': 0
    }


def build_card_queue(
    user,
    deck_id: Optional[int] = None,
    category_id: Optional[int] = None,
    duration_minutes: int = 20,
    include_new_cards: bool = True,
    settings: Optional[UserTrainingSettings] = None
) -> Dict:
    """
    Формирует очередь карточек для тренировочной сессии.
    
    Логика выбора карточек:
    - Если deck_id указан: карточки только из этой колоды.
      Колода авто-активируется при первом использовании.
    - Если category_id указан: карточки только из этой категории.
      Категория авто-активируется при первом использовании.
    - Если ничего не указано (общая тренировка): карточки из
      активных колод + активных категорий + сирот (если включено).
    
    Args:
        user: Пользователь
        deck_id: ID колоды (опционально)
        category_id: ID категории (опционально)
        duration_minutes: Длительность сессии в минутах
        include_new_cards: Включать ли новые карточки
        settings: Настройки тренировки (если None, получаем автоматически)
    
    Returns:
        dict:
        {
            'cards': List[Card],
            'new_count': int,
            'review_count': int,
            'learning_count': int,
            'estimated_time': int (минуты),
            'total_count': int
        }
    """
    # Получаем настройки если не переданы
    if settings is None:
        settings, _ = UserTrainingSettings.objects.get_or_create(
            user=user,
            defaults={'age_group': 'adult'}
        )
    
    # Базовый queryset карточек пользователя (select_related для CardListSerializer)
    base_queryset = Card.objects.for_user(user).select_related('word')
    
    # Фильтрация по колоде
    if deck_id is not None:
        try:
            deck = Deck.objects.get(id=deck_id, user=user)
            # Авто-активация при первом использовании
            if not deck.is_learning_active:
                deck.is_learning_active = True
                deck.save(update_fields=['is_learning_active', 'updated_at'])
            base_queryset = Card.objects.by_deck(deck).select_related('word')
        except Deck.DoesNotExist:
            return _empty_queue()
    
    # Фильтрация по категории
    elif category_id is not None:
        try:
            category = Category.objects.get(id=category_id, user=user)
            # Авто-активация при первом использовании
            if not category.is_learning_active:
                category.is_learning_active = True
                category.save(update_fields=['is_learning_active'])
            base_queryset = base_queryset.filter(
                word__categories=category
            ).distinct()
        except Category.DoesNotExist:
            return _empty_queue()
    
    # Общая тренировка: только карточки из активных колод/категорий + сироты
    else:
        active_filter = (
            Q(word__decks__is_learning_active=True) |
            Q(word__categories__is_learning_active=True)
        )
        if settings.include_orphan_words:
            active_filter |= Q(word__decks__isnull=True)
        base_queryset = base_queryset.filter(active_filter).distinct()
    
    # 1. Карточки в режиме обучения (которые уже начали тренировать)
    # Это карточки с is_in_learning_mode=True и next_review <= now
    learning_cards = list(
        base_queryset.filter(
            is_in_learning_mode=True,
            next_review__lte=timezone.now()
        ).order_by('next_review', 'learning_step')
    )
    
    # 2. Карточки на повторение (прошли режим обучения)
    review_cards = list(
        base_queryset.filter(
            is_in_learning_mode=False,
            next_review__lte=timezone.now()
        ).order_by('next_review')
    )
    
    # 3. Новые карточки (если нужно)
    # Это карточки в режиме обучения, но еще не показанные (next_review в будущем)
    new_cards = []
    if include_new_cards:
        new_cards = list(
            base_queryset.filter(
                is_in_learning_mode=True,
                next_review__gt=timezone.now()
            ).order_by('created_at')
        )
    
    # Ограничиваем по времени
    limited_cards = limit_cards_by_time(
        learning_cards,
        review_cards,
        new_cards,
        duration_minutes
    )
    
    # Подсчитываем статистику
    learning_ids = {c.id for c in learning_cards}
    review_ids = {c.id for c in review_cards}
    new_ids = {c.id for c in new_cards}
    
    learning_count = sum(1 for c in limited_cards if c.id in learning_ids)
    review_count = sum(1 for c in limited_cards if c.id in review_ids)
    new_count = sum(1 for c in limited_cards if c.id in new_ids)
    
    # Оценка времени
    estimated_time = estimate_session_time(learning_count, review_count, new_count)
    
    return {
        'cards': limited_cards,
        'new_count': new_count,
        'review_count': review_count,
        'learning_count': learning_count,
        'estimated_time': estimated_time,
        'total_count': len(limited_cards)
    }
