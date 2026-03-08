"""
Session service: building card queues, processing answers, learning mode transitions.
"""
import uuid
import logging

from django.utils import timezone

from apps.cards.models import Card, Deck
from apps.cards.serializers import CardListSerializer
from apps.words.models import Word
from ..models import UserTrainingSettings
from ..session_utils import build_card_queue
from ..sm2 import SM2Algorithm

logger = logging.getLogger(__name__)

DEFAULT_AGE_GROUP = 'adult'


def _resolve_word_fields(word, user):
    """
    Для инвертированных слов возвращает скорректированные поля.

    При legacy-инвертировании original_word и translation меняются местами,
    а language становится родным языком. Эта функция восстанавливает
    правильные значения для AI-генерации.

    Returns:
        tuple: (target_word, target_translation, target_language)
    """
    if word.card_type == 'inverted':
        target_word = word.translation
        target_translation = word.original_word
        target_language = getattr(user, 'learning_language', word.language)
        return target_word, target_translation, target_language
    return word.original_word, word.translation, word.language


def get_or_create_settings(user):
    """Get or create training settings for user."""
    settings, _ = UserTrainingSettings.objects.get_or_create(
        user=user,
        defaults={'age_group': DEFAULT_AGE_GROUP}
    )
    return settings


def build_training_session(user, deck_id=None, category_id=None,
                           duration=None, new_cards=True, request=None):
    """
    Build a training session with card queue.

    Returns:
        dict with session_id, cards, estimated_time, counts.
    """
    settings = get_or_create_settings(user)

    if duration is None:
        duration = settings.default_session_duration

    queue_result = build_card_queue(
        user=user,
        deck_id=deck_id,
        category_id=category_id,
        duration_minutes=duration,
        include_new_cards=new_cards,
        settings=settings
    )

    session_id = uuid.uuid4()
    cards_data = CardListSerializer(
        queue_result['cards'], many=True,
        context={'request': request}
    ).data

    return {
        'session_id': session_id,
        'cards': cards_data,
        'estimated_time': queue_result['estimated_time'],
        'new_count': queue_result['new_count'],
        'review_count': queue_result['review_count'],
        'learning_count': queue_result['learning_count'],
        'total_count': queue_result['total_count'],
    }


def process_answer(user, card_id, answer, time_spent=None, request=None):
    """
    Process user answer on a card via SM2 algorithm.

    Returns:
        dict with card_id, new_interval, new_ease_factor, next_review, etc.
    Raises:
        Card.DoesNotExist if card not found.
    """
    card = Card.objects.select_related('word').get(id=card_id, user=user)
    settings = get_or_create_settings(user)

    was_in_learning_before = card.is_in_learning_mode
    was_calibrated_before = settings.last_calibration_at is not None

    result = SM2Algorithm.process_answer(
        card=card, answer=answer, settings=settings, time_spent=time_spent
    )

    card.refresh_from_db()
    settings.refresh_from_db()

    is_in_learning_after = card.is_in_learning_mode
    exited_learning_mode = was_in_learning_before and not is_in_learning_after
    calibrated = (settings.last_calibration_at is not None) and not was_calibrated_before

    card_data = CardListSerializer(card, context={'request': request}).data

    return {
        'card_id': card.id,
        'new_interval': result['new_interval'],
        'new_ease_factor': result['new_ease_factor'],
        'next_review': result['next_review'],
        'entered_learning_mode': result['entered_learning_mode'],
        'exited_learning_mode': exited_learning_mode,
        'learning_step': result['learning_step'],
        'calibrated': calibrated,
        'card': card_data,
    }


def enter_learning_mode(user, card_id, request=None):
    """
    Manually enter learning mode for a card.

    Returns:
        dict with card_id, message, card data.
    Raises:
        Card.DoesNotExist if card not found.
    """
    card = Card.objects.select_related('word').get(id=card_id, user=user)
    card.enter_learning_mode()
    card.save()

    card_data = CardListSerializer(card, context={'request': request}).data
    return {
        'card_id': card.id,
        'message': 'Карточка переведена в режим изучения',
        'card': card_data,
    }


def exit_learning_mode(user, card_id, request=None):
    """
    Manually exit learning mode for a card.

    Returns:
        dict with card_id, message, card data.
    Raises:
        Card.DoesNotExist if card not found.
    """
    card = Card.objects.select_related('word').get(id=card_id, user=user)
    card.exit_learning_mode()
    card.save()

    card_data = CardListSerializer(card, context={'request': request}).data
    return {
        'card_id': card.id,
        'message': 'Карточка выведена из режима изучения',
        'card': card_data,
    }
