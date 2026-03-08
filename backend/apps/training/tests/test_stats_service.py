"""Tests for stats_service.py — streak, card counts, dashboard, forgetting curve."""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.cards.models import Card, Deck
from apps.words.models import Word, Category
from apps.training.models import UserTrainingSettings
from apps.training.services.stats_service import (
    calculate_streak_days,
    get_cards_by_status,
    get_card_counts_for_queryset,
    get_training_stats,
    get_dashboard_data,
    activate_deck,
    deactivate_deck,
    activate_category,
    deactivate_category,
    get_forgetting_curve_data,
    check_notification,
)


@pytest.fixture
def training_settings(user):
    settings, _ = UserTrainingSettings.objects.get_or_create(
        user=user, defaults={'age_group': 'adult'}
    )
    return settings


def _create_card(user, original, translation='перевод', **kwargs):
    w = Word.objects.create(
        user=user, original_word=original, translation=translation, language='de')
    # Signal auto-creates a Card; update it instead of creating a duplicate
    card = Card.objects.get(user=user, word=w, card_type='normal')
    for key, value in kwargs.items():
        setattr(card, key, value)
    if 'is_in_learning_mode' not in kwargs:
        card.is_in_learning_mode = True
    if 'interval' not in kwargs:
        card.interval = 0
    card.save()
    return card


@pytest.mark.django_db
class TestCalculateStreakDays:
    def test_no_reviews_returns_zero(self, user):
        assert calculate_streak_days(user) == 0

    def test_today_review_returns_one(self, user):
        card = _create_card(user, 'Hund')
        card.last_review = timezone.now()
        card.save()
        assert calculate_streak_days(user) == 1

    def test_two_consecutive_days(self, user):
        now = timezone.now()
        c1 = _create_card(user, 'Hund')
        c1.last_review = now
        c1.save()

        c2 = _create_card(user, 'Katze')
        c2.last_review = now - timedelta(days=1)
        c2.save()

        assert calculate_streak_days(user) == 2

    def test_gap_breaks_streak(self, user):
        now = timezone.now()
        c1 = _create_card(user, 'Hund')
        c1.last_review = now
        c1.save()

        c2 = _create_card(user, 'Katze')
        c2.last_review = now - timedelta(days=3)  # gap
        c2.save()

        assert calculate_streak_days(user) == 1


@pytest.mark.django_db
class TestGetCardsByStatus:
    def test_empty_user(self, user):
        result = get_cards_by_status(user)
        assert result == {'new': 0, 'learning': 0, 'review': 0, 'mastered': 0}

    def test_new_card(self, user):
        _create_card(user, 'Hund', is_in_learning_mode=True, interval=0)
        result = get_cards_by_status(user)
        assert result['new'] == 1

    def test_learning_card(self, user):
        _create_card(user, 'Hund', is_in_learning_mode=True, interval=1, repetitions=1)
        result = get_cards_by_status(user)
        assert result['learning'] == 1

    def test_review_card(self, user):
        _create_card(
            user, 'Hund',
            is_in_learning_mode=False,
            next_review=timezone.now() - timedelta(hours=1),
        )
        result = get_cards_by_status(user)
        assert result['review'] == 1

    def test_mastered_card(self, user):
        _create_card(
            user, 'Hund',
            is_in_learning_mode=False,
            next_review=timezone.now() + timedelta(days=60),
            interval=30,
        )
        result = get_cards_by_status(user)
        assert result['mastered'] == 1


@pytest.mark.django_db
class TestGetCardCountsForQueryset:
    def test_empty_queryset(self, user):
        qs = Card.objects.none()
        result = get_card_counts_for_queryset(qs)
        assert result['total'] == 0
        assert result['due'] == 0

    def test_mixed_cards(self, user):
        _create_card(user, 'Hund', is_in_learning_mode=True, interval=0)  # new
        _create_card(  # review
            user, 'Katze', is_in_learning_mode=False,
            next_review=timezone.now() - timedelta(hours=1),
        )

        qs = Card.objects.for_user(user)
        result = get_card_counts_for_queryset(qs)
        assert result['total'] == 2
        assert result['new'] == 1
        assert result['review'] == 1
        assert result['due'] == 2


@pytest.mark.django_db
class TestGetTrainingStats:
    def test_returns_all_fields(self, user, training_settings):
        result = get_training_stats(user, 'all')
        assert 'period' in result
        assert 'total_reviews' in result
        assert 'streak_days' in result
        assert 'cards_by_status' in result
        assert 'reviews_by_day' in result

    def test_period_filter(self, user, training_settings):
        result = get_training_stats(user, 'day')
        assert result['period'] == 'day'


@pytest.mark.django_db
class TestGetDashboardData:
    def test_returns_structure(self, user, training_settings):
        result = get_dashboard_data(user)
        assert 'quick_stats' in result
        assert 'decks' in result
        assert 'categories' in result
        assert 'orphans' in result

    def test_includes_deck(self, user, deck, training_settings):
        w = Word.objects.create(
            user=user, original_word='Test', translation='тест', language='de')
        deck.words.add(w)
        # Card auto-created by signal

        result = get_dashboard_data(user)
        assert len(result['decks']) == 1
        assert result['decks'][0]['name'] == deck.name


@pytest.mark.django_db
class TestActivateDeactivate:
    def test_activate_deck(self, user, deck):
        deck.is_learning_active = False
        deck.save()

        result = activate_deck(user, deck.id)
        deck.refresh_from_db()
        assert result['is_learning_active'] is True
        assert deck.is_learning_active is True

    def test_deactivate_deck(self, user, deck):
        result = deactivate_deck(user, deck.id)
        deck.refresh_from_db()
        assert result['is_learning_active'] is False

    def test_activate_nonexistent_deck_raises(self, user):
        with pytest.raises(Deck.DoesNotExist):
            activate_deck(user, 99999)

    def test_activate_category(self, user):
        cat = Category.objects.create(user=user, name='Test')
        cat.is_learning_active = False
        cat.save()

        result = activate_category(user, cat.id)
        cat.refresh_from_db()
        assert cat.is_learning_active is True

    def test_deactivate_category(self, user):
        cat = Category.objects.create(user=user, name='Test', is_learning_active=True)

        result = deactivate_category(user, cat.id)
        cat.refresh_from_db()
        assert cat.is_learning_active is False


@pytest.mark.django_db
class TestForgettingCurve:
    def test_empty_returns_empty(self, user):
        result = get_forgetting_curve_data(user)
        assert result['points'] == []
        assert result['theoretical_curve'] == []
        assert result['summary']['total_reviews'] == 0

    def test_with_reviewed_cards(self, user):
        c = _create_card(
            user, 'Hund', is_in_learning_mode=False,
            interval=5, ease_factor=2.5,
        )
        c.repetitions = 3
        c.consecutive_lapses = 0
        c.save()

        result = get_forgetting_curve_data(user)
        assert len(result['points']) > 0
        assert len(result['theoretical_curve']) > 0
        assert result['summary']['total_reviews'] == 1


@pytest.mark.django_db
class TestCheckNotification:
    def test_no_due_cards(self, user):
        result = check_notification(user)
        assert result['cards_due'] == 0

    def test_returns_structure(self, user):
        result = check_notification(user)
        assert 'should_notify' in result
        assert 'cards_due' in result
        assert 'streak_at_risk' in result
        assert 'notification_type' in result
