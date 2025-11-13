"""
Tests for words app
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Word

User = get_user_model()


@pytest.mark.django_db
class TestWordModel:
    """Тесты для модели Word"""

    def test_word_creation(self):
        """Тест создания слова"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        word = Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        assert word.original_word == 'casa'
        assert word.translation == 'дом'
        assert word.language == 'pt'
        assert word.user == user

    def test_word_unique_constraint(self):
        """Тест уникального ограничения для слова"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        # Попытка создать дубликат должна вызвать ошибку
        with pytest.raises(Exception):
            Word.objects.create(
                user=user,
                original_word='casa',
                translation='дом',
                language='pt'
            )


@pytest.mark.django_db
class TestWordsAPI:
    """Тесты для API слов"""

    def test_words_list_authenticated(self):
        """Тест получения списка слов (аутентифицированный пользователь)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/words/list/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['original_word'] == 'casa'

    def test_words_list_unauthenticated(self):
        """Тест получения списка слов (неаутентифицированный пользователь)"""
        client = APIClient()
        response = client.get('/api/words/list/')
        # DRF возвращает 403 для неаутентифицированных пользователей
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_words_list_filter_by_language(self):
        """Тест фильтрации слов по языку"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        Word.objects.create(
            user=user,
            original_word='haus',
            translation='дом',
            language='de'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/words/list/?language=pt')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['language'] == 'pt'

    def test_words_list_search(self):
        """Тест поиска слов"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Word.objects.create(
            user=user,
            original_word='casa',
            translation='дом',
            language='pt'
        )
        Word.objects.create(
            user=user,
            original_word='livro',
            translation='книга',
            language='pt'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/words/list/?search=casa')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['original_word'] == 'casa'
