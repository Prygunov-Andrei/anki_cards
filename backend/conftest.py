"""
Общие fixtures для тестов всего проекта.

Эти fixtures доступны во всех тестовых файлах без дополнительного импорта.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token as AuthToken

from apps.cards.models import Deck, Card
from apps.words.models import Word
from apps.cards.token_utils import get_or_create_token

User = get_user_model()


@pytest.fixture
def user(db):
    """Базовый тестовый пользователь."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com',
        learning_language='de',
        native_language='ru',
    )


@pytest.fixture
def user2(db):
    """Второй пользователь для тестов изоляции."""
    return User.objects.create_user(
        username='testuser2',
        password='testpass123',
        email='test2@example.com',
        learning_language='de',
        native_language='ru',
    )


@pytest.fixture
def auth_token(user):
    """Auth token для пользователя."""
    token, _ = AuthToken.objects.get_or_create(user=user)
    return token


@pytest.fixture
def api_client():
    """Неаутентифицированный API клиент."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Аутентифицированный API клиент."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {auth_token.key}')
    return api_client


@pytest.fixture
def user_with_tokens(user):
    """Пользователь с балансом токенов."""
    token = get_or_create_token(user)
    token.balance = 100
    token.save()
    return user


@pytest.fixture
def deck(user):
    """Тестовая колода."""
    return Deck.objects.create(
        user=user,
        name='Тестовая колода',
        target_lang='de',
        source_lang='ru',
    )


@pytest.fixture
def word(user):
    """Тестовое слово."""
    return Word.objects.create(
        user=user,
        original_word='Hund',
        translation='собака',
        language='de',
    )


@pytest.fixture
def card(user, word):
    """Тестовая карточка."""
    return Card.objects.create(
        user=user,
        word=word,
        card_type='normal',
    )


@pytest.fixture
def deck_with_words(user, deck):
    """Колода с несколькими словами."""
    words = []
    for original, translation in [('Hund', 'собака'), ('Katze', 'кошка'), ('Haus', 'дом')]:
        w = Word.objects.create(
            user=user,
            original_word=original,
            translation=translation,
            language='de',
        )
        deck.words.add(w)
        words.append(w)
    return deck, words
