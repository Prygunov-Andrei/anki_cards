"""Tests for session_service.py — session building, answer processing, learning mode."""
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.cards.models import Card, Deck
from apps.words.models import Word
from apps.training.models import UserTrainingSettings
from apps.training.services.session_service import (
    _resolve_word_fields,
    get_or_create_settings,
    build_training_session,
    process_answer,
    enter_learning_mode,
    exit_learning_mode,
)


@pytest.fixture
def training_settings(user):
    settings, _ = UserTrainingSettings.objects.get_or_create(
        user=user, defaults={'age_group': 'adult'}
    )
    return settings


@pytest.fixture
def review_card(user):
    w = Word.objects.create(
        user=user, original_word='Haus', translation='дом', language='de')
    card = Card.objects.get(user=user, word=w, card_type='normal')
    card.is_in_learning_mode = True
    card.learning_step = 0
    card.interval = 0
    card.ease_factor = 2.5
    card.next_review = timezone.now() - timedelta(hours=1)
    card.save()
    return card


class TestResolveWordFields:
    def test_normal_word(self, user, word):
        result = _resolve_word_fields(word, user)
        assert result == (word.original_word, word.translation, word.language)

    def test_inverted_word(self, user):
        w = Word(
            user=user, original_word='собака', translation='Hund',
            language='ru', card_type='inverted',
        )
        user.learning_language = 'de'
        target_word, target_translation, target_language = _resolve_word_fields(w, user)
        assert target_word == 'Hund'
        assert target_translation == 'собака'
        assert target_language == 'de'


@pytest.mark.django_db
class TestGetOrCreateSettings:
    def test_creates_settings(self, user):
        UserTrainingSettings.objects.filter(user=user).delete()
        settings = get_or_create_settings(user)
        assert settings.user == user
        assert settings.age_group == 'adult'

    def test_returns_existing(self, user, training_settings):
        settings = get_or_create_settings(user)
        assert settings.id == training_settings.id


@pytest.mark.django_db
class TestBuildTrainingSession:
    def test_empty_session(self, user, training_settings):
        result = build_training_session(user)
        assert 'session_id' in result
        assert 'cards' in result
        assert result['total_count'] == 0

    def test_with_cards(self, user, deck, training_settings):
        w = Word.objects.create(
            user=user, original_word='Test', translation='тест', language='de')
        deck.words.add(w)
        deck.is_learning_active = True
        deck.save()
        card = Card.objects.get(user=user, word=w, card_type='normal')
        card.is_in_learning_mode = True
        card.next_review = timezone.now() - timedelta(hours=1)
        card.save()

        result = build_training_session(user)
        assert result['total_count'] >= 1

    def test_with_deck_filter(self, user, deck, training_settings):
        w = Word.objects.create(
            user=user, original_word='Test', translation='тест', language='de')
        deck.words.add(w)
        card = Card.objects.get(user=user, word=w, card_type='normal')
        card.is_in_learning_mode = True
        card.next_review = timezone.now() - timedelta(hours=1)
        card.save()

        result = build_training_session(user, deck_id=deck.id)
        assert result['total_count'] >= 1

    def test_custom_duration(self, user, training_settings):
        result = build_training_session(user, duration=5)
        assert 'estimated_time' in result


@pytest.mark.django_db
class TestProcessAnswer:
    def test_good_answer(self, user, review_card, training_settings):
        result = process_answer(user, review_card.id, 2)
        assert 'card_id' in result
        assert result['card_id'] == review_card.id
        assert 'new_interval' in result
        assert 'card' in result

    def test_again_answer(self, user, review_card, training_settings):
        result = process_answer(user, review_card.id, 0)
        assert result['card_id'] == review_card.id

    def test_nonexistent_card_raises(self, user, training_settings):
        with pytest.raises(Card.DoesNotExist):
            process_answer(user, 99999, 2)

    def test_time_spent_accepted(self, user, review_card, training_settings):
        result = process_answer(user, review_card.id, 2, time_spent=5.0)
        assert result['card_id'] == review_card.id


@pytest.mark.django_db
class TestEnterExitLearningMode:
    def test_enter_learning(self, user, training_settings):
        w = Word.objects.create(
            user=user, original_word='Haus2', translation='дом', language='de')
        card = Card.objects.get(user=user, word=w, card_type='normal')
        card.is_in_learning_mode = False
        card.save()

        result = enter_learning_mode(user, card.id)
        card.refresh_from_db()
        assert card.is_in_learning_mode is True
        assert result['message'] == 'Карточка переведена в режим изучения'

    def test_exit_learning(self, user, review_card, training_settings):
        result = exit_learning_mode(user, review_card.id)
        review_card.refresh_from_db()
        assert review_card.is_in_learning_mode is False
        assert result['message'] == 'Карточка выведена из режима изучения'

    def test_enter_nonexistent_card(self, user, training_settings):
        with pytest.raises(Card.DoesNotExist):
            enter_learning_mode(user, 99999)

    def test_exit_nonexistent_card(self, user, training_settings):
        with pytest.raises(Card.DoesNotExist):
            exit_learning_mode(user, 99999)
