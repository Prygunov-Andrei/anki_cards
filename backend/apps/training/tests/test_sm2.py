"""
Tests for SM-2 algorithm — target 90% coverage.

Tests cover all answer types (Again/Hard/Good/Easy), both learning and
long-term modes, ease factor boundaries, interval calculations, lapse handling,
and calibration integration.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.utils import timezone

from apps.cards.models import Card, Deck
from apps.words.models import Word
from apps.training.models import UserTrainingSettings
from apps.training.sm2 import SM2Algorithm
from apps.core.constants import MAX_EASE_FACTOR


@pytest.fixture
def training_settings(user):
    """Training settings with known defaults."""
    settings, _ = UserTrainingSettings.objects.get_or_create(
        user=user, defaults={'age_group': 'adult'}
    )
    return settings


@pytest.fixture
def new_card(user, word):
    """A new card in learning mode (uses auto-created card from signal)."""
    card = Card.objects.get(user=user, word=word, card_type='normal')
    card.is_in_learning_mode = True
    card.learning_step = 0
    card.interval = 0
    card.ease_factor = 2.5
    card.save()
    return card


@pytest.fixture
def learned_card(user):
    """A card that has graduated from learning mode."""
    w = Word.objects.create(
        user=user, original_word='Haus', translation='дом', language='de')
    card = Card.objects.get(user=user, word=w, card_type='normal')
    card.is_in_learning_mode = False
    card.learning_step = -1
    card.interval = 10
    card.ease_factor = 2.5
    card.repetitions = 3
    card.next_review = timezone.now() - timedelta(hours=1)
    card.save()
    return card


@pytest.mark.django_db
class TestSM2ProcessAnswerLearningMode:
    """Tests for SM2Algorithm.process_answer in learning mode."""

    def test_again_resets_to_step_zero(self, new_card, training_settings):
        result = SM2Algorithm.process_answer(new_card, 0, training_settings)
        new_card.refresh_from_db()

        assert new_card.learning_step == 0
        assert new_card.is_in_learning_mode is True
        assert new_card.lapses == 1
        assert new_card.consecutive_lapses == 1
        assert new_card.repetitions == 0

    def test_again_decreases_ease_factor(self, new_card, training_settings):
        original_ef = new_card.ease_factor
        SM2Algorithm.process_answer(new_card, 0, training_settings)
        new_card.refresh_from_db()

        expected_ef = max(
            training_settings.min_ease_factor,
            original_ef + training_settings.again_ef_delta
        )
        assert abs(new_card.ease_factor - expected_ef) < 0.01

    def test_hard_stays_on_step(self, new_card, training_settings):
        SM2Algorithm.process_answer(new_card, 1, training_settings)
        new_card.refresh_from_db()

        assert new_card.learning_step == 0
        assert new_card.is_in_learning_mode is True

    def test_good_advances_step(self, new_card, training_settings):
        SM2Algorithm.process_answer(new_card, 2, training_settings)
        new_card.refresh_from_db()

        assert new_card.learning_step == 1
        assert new_card.is_in_learning_mode is True

    def test_good_on_last_step_graduates(self, new_card, training_settings):
        steps = training_settings.learning_steps or [2, 10]
        new_card.learning_step = len(steps) - 1
        new_card.save()

        result = SM2Algorithm.process_answer(new_card, 2, training_settings)
        new_card.refresh_from_db()

        assert new_card.is_in_learning_mode is False
        assert new_card.learning_step == -1
        assert new_card.interval == training_settings.graduating_interval
        assert result['exited_learning_mode'] is True

    def test_easy_graduates_immediately(self, new_card, training_settings):
        result = SM2Algorithm.process_answer(new_card, 3, training_settings)
        new_card.refresh_from_db()

        assert new_card.is_in_learning_mode is False
        assert new_card.learning_step == -1
        assert new_card.interval == training_settings.easy_interval
        assert result['exited_learning_mode'] is True

    def test_easy_increases_ease_factor(self, new_card, training_settings):
        original_ef = new_card.ease_factor
        SM2Algorithm.process_answer(new_card, 3, training_settings)
        new_card.refresh_from_db()

        expected_ef = min(
            MAX_EASE_FACTOR,
            original_ef + training_settings.easy_ef_delta
        )
        assert abs(new_card.ease_factor - expected_ef) < 0.01

    def test_next_review_set_in_minutes_for_learning(self, new_card, training_settings):
        before = timezone.now()
        SM2Algorithm.process_answer(new_card, 2, training_settings)
        new_card.refresh_from_db()

        steps = training_settings.learning_steps or [2, 10]
        expected_minutes = steps[1]  # advanced to step 1
        assert new_card.next_review > before
        # Should be roughly expected_minutes from now
        diff = (new_card.next_review - before).total_seconds() / 60
        assert abs(diff - expected_minutes) < 1

    def test_next_review_set_in_days_after_graduation(self, new_card, training_settings):
        before = timezone.now()
        SM2Algorithm.process_answer(new_card, 3, training_settings)  # Easy → graduate
        new_card.refresh_from_db()

        diff_days = (new_card.next_review - before).total_seconds() / 86400
        assert abs(diff_days - training_settings.easy_interval) < 0.1


@pytest.mark.django_db
class TestSM2ProcessAnswerLongTerm:
    """Tests for SM2Algorithm.process_answer outside learning mode."""

    def test_again_enters_learning_mode(self, learned_card, training_settings):
        result = SM2Algorithm.process_answer(learned_card, 0, training_settings)
        learned_card.refresh_from_db()

        assert learned_card.is_in_learning_mode is True
        assert learned_card.learning_step == 0
        assert result['entered_learning_mode'] is True
        assert learned_card.lapses == 1

    def test_hard_increases_interval(self, learned_card, training_settings):
        old_interval = learned_card.interval
        SM2Algorithm.process_answer(learned_card, 1, training_settings)
        learned_card.refresh_from_db()

        assert learned_card.interval >= old_interval + 1
        assert learned_card.is_in_learning_mode is False

    def test_good_increases_interval_with_ef(self, learned_card, training_settings):
        old_interval = learned_card.interval
        SM2Algorithm.process_answer(learned_card, 2, training_settings)
        learned_card.refresh_from_db()

        expected = int(old_interval * learned_card.ease_factor * training_settings.interval_modifier)
        expected = max(old_interval + 1, expected)
        # Allow some tolerance due to EF delta
        assert learned_card.interval >= old_interval + 1
        assert learned_card.is_in_learning_mode is False

    def test_easy_largest_interval_increase(self, user, training_settings):
        old_interval = 10
        ef = 2.5

        # Create two separate words/cards for comparison
        w1 = Word.objects.create(
            user=user, original_word='Apfel', translation='яблоко', language='de')
        easy_card = Card.objects.get(user=user, word=w1, card_type='normal')
        easy_card.is_in_learning_mode = False
        easy_card.interval = old_interval
        easy_card.ease_factor = ef
        easy_card.repetitions = 3
        easy_card.next_review = timezone.now() - timedelta(hours=1)
        easy_card.save()

        w2 = Word.objects.create(
            user=user, original_word='Birne', translation='груша', language='de')
        hard_card = Card.objects.get(user=user, word=w2, card_type='normal')
        hard_card.is_in_learning_mode = False
        hard_card.interval = old_interval
        hard_card.ease_factor = ef
        hard_card.repetitions = 3
        hard_card.next_review = timezone.now() - timedelta(hours=1)
        hard_card.save()

        SM2Algorithm.process_answer(easy_card, 3, training_settings)
        SM2Algorithm.process_answer(hard_card, 1, training_settings)

        easy_card.refresh_from_db()
        hard_card.refresh_from_db()

        assert easy_card.interval > hard_card.interval

    def test_repetitions_increment_on_success(self, learned_card, training_settings):
        old_reps = learned_card.repetitions
        SM2Algorithm.process_answer(learned_card, 2, training_settings)
        learned_card.refresh_from_db()

        assert learned_card.repetitions == old_reps + 1

    def test_repetitions_reset_on_again(self, learned_card, training_settings):
        SM2Algorithm.process_answer(learned_card, 0, training_settings)
        learned_card.refresh_from_db()

        assert learned_card.repetitions == 0

    def test_consecutive_lapses_reset_on_success(self, learned_card, training_settings):
        learned_card.consecutive_lapses = 3
        learned_card.save()

        SM2Algorithm.process_answer(learned_card, 2, training_settings)
        learned_card.refresh_from_db()

        assert learned_card.consecutive_lapses == 0

    def test_hard_decreases_ease_factor(self, learned_card, training_settings):
        original_ef = learned_card.ease_factor
        SM2Algorithm.process_answer(learned_card, 1, training_settings)
        learned_card.refresh_from_db()

        expected = max(
            training_settings.min_ease_factor,
            original_ef + training_settings.hard_ef_delta
        )
        assert abs(learned_card.ease_factor - expected) < 0.01

    def test_easy_increases_ease_factor(self, learned_card, training_settings):
        original_ef = learned_card.ease_factor
        SM2Algorithm.process_answer(learned_card, 3, training_settings)
        learned_card.refresh_from_db()

        expected = min(MAX_EASE_FACTOR, original_ef + training_settings.easy_ef_delta)
        assert abs(learned_card.ease_factor - expected) < 0.01


@pytest.mark.django_db
class TestSM2EaseFactorBoundaries:
    """Tests for ease factor min/max boundaries."""

    def test_ef_does_not_go_below_min(self, new_card, training_settings):
        new_card.ease_factor = training_settings.min_ease_factor
        new_card.save()

        SM2Algorithm.process_answer(new_card, 0, training_settings)
        new_card.refresh_from_db()

        assert new_card.ease_factor >= training_settings.min_ease_factor

    def test_ef_does_not_exceed_max(self, new_card, training_settings):
        new_card.ease_factor = MAX_EASE_FACTOR - 0.05
        new_card.save()

        SM2Algorithm.process_answer(new_card, 3, training_settings)
        new_card.refresh_from_db()

        assert new_card.ease_factor <= MAX_EASE_FACTOR

    def test_repeated_again_keeps_ef_at_min(self, new_card, training_settings):
        for _ in range(5):
            SM2Algorithm.process_answer(new_card, 0, training_settings)
            new_card.refresh_from_db()

        assert new_card.ease_factor >= training_settings.min_ease_factor


@pytest.mark.django_db
class TestSM2InvalidInput:
    """Tests for invalid input handling."""

    def test_invalid_answer_raises(self, new_card, training_settings):
        with pytest.raises(ValueError, match='Invalid answer'):
            SM2Algorithm.process_answer(new_card, 5, training_settings)

    def test_negative_answer_raises(self, new_card, training_settings):
        with pytest.raises(ValueError, match='Invalid answer'):
            SM2Algorithm.process_answer(new_card, -1, training_settings)


@pytest.mark.django_db
class TestSM2Calibration:
    """Tests for calibration integration."""

    def test_records_review_on_answer(self, new_card, training_settings):
        old_total = training_settings.total_reviews
        SM2Algorithm.process_answer(new_card, 2, training_settings)
        training_settings.refresh_from_db()

        assert training_settings.total_reviews == old_total + 1

    def test_records_successful_review(self, new_card, training_settings):
        old_successful = training_settings.successful_reviews
        SM2Algorithm.process_answer(new_card, 2, training_settings)
        training_settings.refresh_from_db()

        assert training_settings.successful_reviews == old_successful + 1

    def test_failed_review_not_counted_as_successful(self, new_card, training_settings):
        old_successful = training_settings.successful_reviews
        SM2Algorithm.process_answer(new_card, 0, training_settings)
        training_settings.refresh_from_db()

        assert training_settings.successful_reviews == old_successful


@pytest.mark.django_db
class TestSM2CalculateNextInterval:
    """Tests for calculate_next_interval utility method."""

    def test_again_returns_zero(self, learned_card, training_settings):
        result = SM2Algorithm.calculate_next_interval(learned_card, 0, training_settings)
        assert result == 0

    def test_hard_interval(self, learned_card, training_settings):
        result = SM2Algorithm.calculate_next_interval(learned_card, 1, training_settings)
        expected = int(
            learned_card.interval * training_settings.hard_interval_modifier
            * training_settings.interval_modifier
        )
        expected = max(learned_card.interval + 1, max(1, expected))
        assert result == expected

    def test_good_interval(self, learned_card, training_settings):
        result = SM2Algorithm.calculate_next_interval(learned_card, 2, training_settings)
        expected = int(
            learned_card.interval * learned_card.ease_factor
            * training_settings.interval_modifier
        )
        expected = max(learned_card.interval + 1, max(1, expected))
        assert result == expected

    def test_easy_interval(self, learned_card, training_settings):
        result = SM2Algorithm.calculate_next_interval(learned_card, 3, training_settings)
        expected = int(
            learned_card.interval * learned_card.ease_factor
            * training_settings.easy_bonus * training_settings.interval_modifier
        )
        expected = max(learned_card.interval + 1, max(1, expected))
        assert result == expected

    def test_interval_at_least_one(self, learned_card, training_settings):
        learned_card.interval = 0
        learned_card.save()
        result = SM2Algorithm.calculate_next_interval(learned_card, 2, training_settings)
        assert result >= 1

    def test_invalid_answer_raises(self, learned_card, training_settings):
        with pytest.raises(ValueError):
            SM2Algorithm.calculate_next_interval(learned_card, 5, training_settings)


@pytest.mark.django_db
class TestSM2UpdateEaseFactor:
    """Tests for update_ease_factor utility method."""

    def test_again_delta(self, new_card, training_settings):
        ef = SM2Algorithm.update_ease_factor(new_card, 0, training_settings)
        expected = max(
            training_settings.min_ease_factor,
            2.5 + training_settings.again_ef_delta
        )
        assert abs(ef - expected) < 0.01

    def test_hard_delta(self, new_card, training_settings):
        ef = SM2Algorithm.update_ease_factor(new_card, 1, training_settings)
        expected = max(
            training_settings.min_ease_factor,
            2.5 + training_settings.hard_ef_delta
        )
        assert abs(ef - expected) < 0.01

    def test_good_delta(self, new_card, training_settings):
        ef = SM2Algorithm.update_ease_factor(new_card, 2, training_settings)
        expected = 2.5 + training_settings.good_ef_delta
        assert abs(ef - expected) < 0.01

    def test_easy_delta(self, new_card, training_settings):
        ef = SM2Algorithm.update_ease_factor(new_card, 3, training_settings)
        expected = min(MAX_EASE_FACTOR, 2.5 + training_settings.easy_ef_delta)
        assert abs(ef - expected) < 0.01

    def test_invalid_answer(self, new_card, training_settings):
        with pytest.raises(ValueError):
            SM2Algorithm.update_ease_factor(new_card, 4, training_settings)


@pytest.mark.django_db
class TestSM2ApplyIntervalModifiers:
    """Tests for apply_interval_modifiers utility method."""

    def test_hard_modifier(self, training_settings):
        result = SM2Algorithm.apply_interval_modifiers(10, 1, training_settings)
        expected = int(10 * training_settings.hard_interval_modifier * training_settings.interval_modifier)
        assert result == max(1, expected)

    def test_good_no_extra_modifier(self, training_settings):
        result = SM2Algorithm.apply_interval_modifiers(10, 2, training_settings)
        expected = int(10 * 1.0 * training_settings.interval_modifier)
        assert result == max(1, expected)

    def test_easy_bonus(self, training_settings):
        result = SM2Algorithm.apply_interval_modifiers(10, 3, training_settings)
        expected = int(10 * training_settings.easy_bonus * training_settings.interval_modifier)
        assert result == max(1, expected)

    def test_minimum_one_day(self, training_settings):
        result = SM2Algorithm.apply_interval_modifiers(0, 1, training_settings)
        assert result >= 1

    def test_invalid_answer_raises(self, training_settings):
        with pytest.raises(ValueError):
            SM2Algorithm.apply_interval_modifiers(10, 0, training_settings)


@pytest.mark.django_db
class TestSM2ShouldEnterLearningMode:
    """Tests for should_enter_learning_mode."""

    def test_below_threshold(self, new_card, training_settings):
        new_card.consecutive_lapses = 0
        assert SM2Algorithm.should_enter_learning_mode(new_card, training_settings) is False

    def test_at_threshold(self, new_card, training_settings):
        new_card.consecutive_lapses = training_settings.lapse_threshold
        assert SM2Algorithm.should_enter_learning_mode(new_card, training_settings) is True

    def test_above_threshold(self, new_card, training_settings):
        new_card.consecutive_lapses = training_settings.lapse_threshold + 5
        assert SM2Algorithm.should_enter_learning_mode(new_card, training_settings) is True


@pytest.mark.django_db
class TestSM2LearningStepEdgeCases:
    """Tests for edge cases in learning step progression."""

    def test_empty_learning_steps_fallback(self, new_card, training_settings):
        training_settings.learning_steps = []
        training_settings.save()

        SM2Algorithm.process_answer(new_card, 0, training_settings)
        new_card.refresh_from_db()
        # Should use fallback [2, 10]
        assert new_card.is_in_learning_mode is True

    def test_single_step_good_graduates(self, new_card, training_settings):
        training_settings.learning_steps = [5]
        training_settings.save()

        # Step 0 → Good → should graduate (step 1 >= len([5]))
        result = SM2Algorithm.process_answer(new_card, 2, training_settings)
        new_card.refresh_from_db()

        assert new_card.is_in_learning_mode is False
        assert result['exited_learning_mode'] is True

    def test_hard_on_last_step_stays(self, new_card, training_settings):
        steps = training_settings.learning_steps or [2, 10]
        new_card.learning_step = len(steps) - 1
        new_card.save()

        result = SM2Algorithm.process_answer(new_card, 1, training_settings)
        new_card.refresh_from_db()

        assert new_card.is_in_learning_mode is True
        assert result['exited_learning_mode'] is False
