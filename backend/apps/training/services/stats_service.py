"""
Stats service: streak calculation, card status counts, dashboard data, forgetting curve.
"""
import math
import logging
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone
from django.db.models import Avg, Count, Q

from apps.cards.models import Card, Deck
from apps.words.models import Category
from ..models import UserTrainingSettings, NotificationSettings

logger = logging.getLogger(__name__)

DEFAULT_AGE_GROUP = 'adult'


def calculate_streak_days(user):
    """
    Подсчитывает количество дней подряд с тренировками.

    Returns:
        int: Количество дней streak
    """
    cards = Card.objects.for_user(user).filter(
        last_review__isnull=False
    ).exclude(last_review__lt=timezone.now() - timedelta(days=365))

    if not cards.exists():
        return 0

    training_dates = set()
    for card in cards:
        if card.last_review:
            training_dates.add(card.last_review.date())

    if not training_dates:
        return 0

    sorted_dates = sorted(training_dates, reverse=True)
    streak = 0
    current_date = timezone.now().date()

    for date in sorted_dates:
        if date == current_date or date == current_date - timedelta(days=streak):
            streak += 1
            current_date = date
        else:
            break

    return streak


def get_cards_by_status(user):
    """
    Возвращает распределение карточек по статусам.

    Returns:
        dict: {'new': int, 'learning': int, 'review': int, 'mastered': int}
    """
    cards = Card.objects.for_user(user)
    now = timezone.now()

    new_count = cards.filter(
        is_in_learning_mode=True, repetitions=0, interval=0
    ).count()

    learning_count = cards.filter(
        is_in_learning_mode=True
    ).exclude(repetitions=0, interval=0).count()

    review_count = cards.filter(
        is_in_learning_mode=False, next_review__lte=now
    ).count()

    mastered_count = cards.filter(
        is_in_learning_mode=False, next_review__gt=now, interval__gte=30
    ).count()

    return {
        'new': new_count,
        'learning': learning_count,
        'review': review_count,
        'mastered': mastered_count,
    }


def get_card_counts_for_queryset(cards_qs):
    """
    Подсчитывает карточки по статусам для произвольного queryset.

    Returns:
        dict: {'new', 'learning', 'review', 'mastered', 'total', 'due'}
    """
    now = timezone.now()
    total = cards_qs.count()

    new_count = cards_qs.filter(
        is_in_learning_mode=True, repetitions=0, interval=0
    ).count()

    learning_count = cards_qs.filter(
        is_in_learning_mode=True
    ).exclude(repetitions=0, interval=0).count()

    review_count = cards_qs.filter(
        is_in_learning_mode=False, next_review__lte=now
    ).count()

    mastered_count = cards_qs.filter(
        is_in_learning_mode=False, next_review__gt=now, interval__gte=30
    ).count()

    due_count = new_count + learning_count + review_count

    return {
        'new': new_count,
        'learning': learning_count,
        'review': review_count,
        'mastered': mastered_count,
        'total': total,
        'due': due_count,
    }


def get_training_stats(user, period='all'):
    """
    Get training statistics for a given period.

    Returns:
        dict with period, total_reviews, successful_reviews, success_rate,
        streak_days, cards_by_status, reviews_by_day, average_time_per_card,
        total_time_spent.
    """
    now = timezone.now()
    if period == 'day':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    else:
        start_date = None

    settings, _ = UserTrainingSettings.objects.get_or_create(
        user=user, defaults={'age_group': DEFAULT_AGE_GROUP}
    )

    total_reviews = settings.total_reviews
    successful_reviews = settings.successful_reviews
    success_rate = (successful_reviews / total_reviews) if total_reviews > 0 else 0.0

    cards = Card.objects.for_user(user)
    cards_in_period = cards.filter(last_review__gte=start_date) if start_date else cards

    reviews_by_day_dict = defaultdict(lambda: {'total': 0, 'successful': 0})
    for card in cards_in_period:
        if card.last_review:
            day = card.last_review.date()
            reviews_by_day_dict[day]['total'] += 1
            if card.repetitions > 0 or card.ease_factor >= settings.starting_ease:
                reviews_by_day_dict[day]['successful'] += 1

    reviews_by_day = []
    for date, stats in sorted(reviews_by_day_dict.items()):
        rate = (stats['successful'] / stats['total']) if stats['total'] > 0 else 0.0
        reviews_by_day.append({
            'date': date,
            'total': stats['total'],
            'successful': stats['successful'],
            'success_rate': round(rate, 2),
        })

    streak_days = calculate_streak_days(user)
    cards_by_status = get_cards_by_status(user)

    total_time_spent = getattr(settings, 'total_time_spent', 0)
    average_time_per_card = (total_time_spent / total_reviews) if total_reviews > 0 else 0.0

    return {
        'period': period,
        'total_reviews': total_reviews,
        'successful_reviews': successful_reviews,
        'success_rate': round(success_rate, 2),
        'streak_days': streak_days,
        'cards_by_status': cards_by_status,
        'reviews_by_day': reviews_by_day,
        'average_time_per_card': round(average_time_per_card, 2),
        'total_time_spent': total_time_spent,
    }


def get_dashboard_data(user):
    """
    Build dashboard data: decks, categories, orphans with card counts.

    Returns:
        dict with quick_stats, decks, categories, orphans.
    """
    training_settings, _ = UserTrainingSettings.objects.get_or_create(
        user=user, defaults={'age_group': DEFAULT_AGE_GROUP}
    )

    streak_days = calculate_streak_days(user)
    total_reviews = training_settings.total_reviews
    successful_reviews = training_settings.successful_reviews
    success_rate = (successful_reviews / total_reviews) if total_reviews > 0 else 0.0

    all_user_cards = Card.objects.for_user(user)
    total_due = get_card_counts_for_queryset(all_user_cards)['due']

    decks_data = []
    for deck in Deck.objects.filter(user=user).order_by('-updated_at'):
        deck_cards = all_user_cards.filter(word__decks=deck)
        cards_info = get_card_counts_for_queryset(deck_cards)
        decks_data.append({
            'id': deck.id,
            'name': deck.name,
            'cover': deck.cover.url if deck.cover else None,
            'is_learning_active': deck.is_learning_active,
            'cards': cards_info,
        })

    categories_data = []
    for cat in Category.objects.filter(user=user).order_by('order', 'name'):
        cat_cards = all_user_cards.filter(word__categories=cat)
        cards_info = get_card_counts_for_queryset(cat_cards)
        categories_data.append({
            'id': cat.id,
            'name': cat.name,
            'icon': cat.icon,
            'parent_id': cat.parent_id,
            'is_learning_active': cat.is_learning_active,
            'cards': cards_info,
        })

    orphan_cards = all_user_cards.filter(word__decks__isnull=True)
    orphans_info = get_card_counts_for_queryset(orphan_cards)

    return {
        'quick_stats': {
            'streak_days': streak_days,
            'success_rate': round(success_rate, 2),
            'total_due': total_due,
        },
        'decks': decks_data,
        'categories': categories_data,
        'orphans': {
            'is_active': training_settings.include_orphan_words,
            'cards': orphans_info,
        },
    }


def activate_deck(user, deck_id):
    """Activate a deck for training."""
    deck = Deck.objects.get(id=deck_id, user=user)
    deck.is_learning_active = True
    deck.save(update_fields=['is_learning_active', 'updated_at'])
    return {'id': deck.id, 'is_learning_active': True}


def deactivate_deck(user, deck_id):
    """Deactivate a deck from training."""
    deck = Deck.objects.get(id=deck_id, user=user)
    deck.is_learning_active = False
    deck.save(update_fields=['is_learning_active', 'updated_at'])
    return {'id': deck.id, 'is_learning_active': False}


def activate_category(user, category_id):
    """Activate a category for training."""
    category = Category.objects.get(id=category_id, user=user)
    category.is_learning_active = True
    category.save(update_fields=['is_learning_active'])
    return {'id': category.id, 'is_learning_active': True}


def deactivate_category(user, category_id):
    """Deactivate a category from training."""
    category = Category.objects.get(id=category_id, user=user)
    category.is_learning_active = False
    category.save(update_fields=['is_learning_active'])
    return {'id': category.id, 'is_learning_active': False}


def get_forgetting_curve_data(user):
    """
    Get data for building the user's forgetting curve.

    Returns:
        dict with points, theoretical_curve, summary.
    """
    reviewed_cards = Card.objects.filter(user=user, repetitions__gt=0)

    if not reviewed_cards.exists():
        return {
            'points': [],
            'theoretical_curve': [],
            'summary': {
                'total_reviews': 0,
                'avg_retention': 0,
                'current_stability': 0,
            },
        }

    buckets = [
        (1, 1, '1'),
        (2, 3, '2-3'),
        (4, 7, '4-7'),
        (8, 14, '8-14'),
        (15, 30, '15-30'),
        (31, 60, '31-60'),
        (61, 90, '61-90'),
        (91, 365, '91+'),
    ]

    points = []
    for low, high, label in buckets:
        cards_in_bucket = reviewed_cards.filter(interval__gte=low, interval__lte=high)
        total = cards_in_bucket.count()
        if total == 0:
            continue

        successful = cards_in_bucket.filter(consecutive_lapses=0).count()
        retention = successful / total if total > 0 else 0

        mid_day = (low + high) / 2
        points.append({
            'interval_days': mid_day,
            'label': label,
            'retention_rate': round(retention * 100, 1),
            'total_cards': total,
            'successful': successful,
        })

    avg_interval = reviewed_cards.filter(
        consecutive_lapses=0
    ).aggregate(avg=Avg('interval'))['avg'] or 30

    theoretical = []
    for day in [1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90, 120, 180, 365]:
        retention = math.exp(-day / max(avg_interval, 1)) * 100
        theoretical.append({
            'day': day,
            'retention': round(retention, 1),
        })

    total_reviews = reviewed_cards.aggregate(total=Count('id'))['total'] or 0
    avg_ef = reviewed_cards.aggregate(avg_ef=Avg('ease_factor'))['avg_ef'] or 2.5

    return {
        'points': points,
        'theoretical_curve': theoretical,
        'summary': {
            'total_reviews': total_reviews,
            'avg_retention': round((avg_ef - 1.3) / (4.0 - 1.3) * 100, 1),
            'current_stability': round(avg_interval, 1),
        },
    }


def check_notification(user):
    """
    Check if a notification should be shown.

    Returns:
        dict with should_notify, cards_due, streak_at_risk, message, notification_type.
    """
    settings_obj, _ = NotificationSettings.objects.get_or_create(
        user=user,
        defaults={'notification_frequency': 'normal'}
    )

    now = timezone.now()
    cards_due = Card.objects.filter(user=user, next_review__lte=now).count()

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_reviews = Card.objects.filter(user=user, last_review__gte=today_start).count()
    streak_at_risk = today_reviews == 0

    should_notify = False
    message = ''
    notification_type = 'none'

    if not settings_obj.should_notify():
        return {
            'should_notify': False,
            'cards_due': cards_due,
            'streak_at_risk': streak_at_risk,
            'message': '',
            'notification_type': 'none',
        }

    if settings_obj.notify_cards_due and cards_due >= settings_obj.cards_due_threshold:
        should_notify = True
        message = f'У вас {cards_due} карточек для повторения!'
        notification_type = 'cards_due'
    elif settings_obj.notify_streak_warning and streak_at_risk and now.hour >= 18:
        should_notify = True
        message = 'Ваш стрик в опасности! Не забудьте позаниматься сегодня.'
        notification_type = 'streak_warning'

    if should_notify:
        settings_obj.last_notified_at = now
        settings_obj.save(update_fields=['last_notified_at'])

    return {
        'should_notify': should_notify,
        'cards_due': cards_due,
        'streak_at_risk': streak_at_risk,
        'message': message,
        'notification_type': notification_type,
    }
