"""
Утилиты для работы со словами
"""
from typing import Optional, Dict, Any
from django.utils import timezone
from django.db.models import Min, Count, Q

from .models import Word
from apps.cards.models import Card


def get_word_learning_status(word: Word) -> str:
    """
    Определяет статус обучения слова на основе его карточек.
    
    Логика:
    1. Если нет карточек → 'new'
    2. Если есть карточки в режиме изучения → 'learning'
    3. Если есть карточки на повторении (next_review <= now) → 'reviewing'
    4. Если все карточки освоены (next_review > now, interval >= 30) → 'mastered'
    5. Иначе → 'reviewing'
    
    Args:
        word: Объект Word
    
    Returns:
        'new' | 'learning' | 'reviewing' | 'mastered'
    """
    cards = Card.objects.filter(word=word, user=word.user)
    
    # Если нет карточек
    if not cards.exists():
        return 'new'
    
    now = timezone.now()
    
    # Проверяем, есть ли карточки в режиме изучения
    learning_cards = cards.filter(is_in_learning_mode=True)
    if learning_cards.exists():
        return 'learning'
    
    # Проверяем, есть ли карточки на повторении
    review_cards = cards.filter(
        is_in_learning_mode=False,
        next_review__lte=now
    )
    if review_cards.exists():
        return 'reviewing'
    
    # Проверяем, все ли карточки освоены
    # Освоенная карточка: is_in_learning_mode=False, next_review > now, interval >= 30
    mastered_cards = cards.filter(
        is_in_learning_mode=False,
        next_review__gt=now,
        interval__gte=30
    )
    
    # Если все карточки освоены
    if mastered_cards.count() == cards.count() and cards.count() > 0:
        return 'mastered'
    
    # Иначе - на повторении (есть карточки, но не все освоены)
    return 'reviewing'


def update_word_learning_status(word: Word) -> Word:
    """
    Обновляет learning_status слова на основе его карточек.
    
    Args:
        word: Объект Word
    
    Returns:
        Обновлённый объект Word
    """
    new_status = get_word_learning_status(word)
    
    if word.learning_status != new_status:
        word.learning_status = new_status
        word.save(update_fields=['learning_status'])
    
    return word


def get_word_next_review(word: Word):
    """
    Возвращает ближайшую дату следующего повторения среди всех карточек слова.
    
    Args:
        word: Объект Word
    
    Returns:
        datetime или None, если нет карточек на повторении
    """
    cards = Card.objects.filter(
        word=word,
        user=word.user,
        next_review__isnull=False
    ).order_by('next_review')
    
    if cards.exists():
        return cards.first().next_review
    
    return None


def get_word_cards_stats(word: Word) -> Dict[str, Any]:
    """
    Возвращает статистику по карточкам слова.
    
    Args:
        word: Объект Word
    
    Returns:
        {
            'total_cards': int,
            'normal_cards': int,
            'inverted_cards': int,
            'empty_cards': int,
            'cloze_cards': int,
            'in_learning_mode': int,
            'due_for_review': int,
            'mastered': int,
            'next_review': Optional[str],  # ISO format string
        }
    """
    cards = Card.objects.filter(word=word, user=word.user)
    now = timezone.now()
    
    total_cards = cards.count()
    
    # По типам карточек
    normal_cards = cards.filter(card_type='normal').count()
    inverted_cards = cards.filter(card_type='inverted').count()
    empty_cards = cards.filter(card_type='empty').count()
    cloze_cards = cards.filter(card_type='cloze').count()
    
    # По статусам
    in_learning_mode = cards.filter(is_in_learning_mode=True).count()
    due_for_review = cards.filter(
        is_in_learning_mode=False,
        next_review__lte=now
    ).count()
    mastered = cards.filter(
        is_in_learning_mode=False,
        next_review__gt=now,
        interval__gte=30
    ).count()
    
    # Ближайшая дата повторения
    next_review = get_word_next_review(word)
    
    return {
        'total_cards': total_cards,
        'normal_cards': normal_cards,
        'inverted_cards': inverted_cards,
        'empty_cards': empty_cards,
        'cloze_cards': cloze_cards,
        'in_learning_mode': in_learning_mode,
        'due_for_review': due_for_review,
        'mastered': mastered,
        'next_review': next_review.isoformat() if next_review else None,
    }
