"""
Tests for cards app
"""
import pytest
import os
import tempfile
from pathlib import Path
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.words.models import Word
from .models import GeneratedDeck
from .utils import create_card_model, create_deck, generate_apkg

User = get_user_model()


@pytest.mark.django_db
class TestCardUtils:
    """Тесты для утилит генерации карточек"""

    def test_create_card_model(self):
        """Тест создания модели карточек"""
        model = create_card_model()
        assert model is not None
        assert len(model.fields) == 4
        assert len(model.templates) == 2

    def test_create_deck(self):
        """Тест создания колоды"""
        deck = create_deck("Тестовая колода")
        assert deck is not None
        assert deck.name == "Тестовая колода"

    def test_generate_apkg_simple(self):
        """Тест генерации простой колоды без медиа"""
        words_data = [
            {
                'original_word': 'casa',
                'translation': 'дом',
            },
            {
                'original_word': 'livro',
                'translation': 'книга',
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_deck.apkg"
            result_path = generate_apkg(
                words_data=words_data,
                deck_name="Тестовая колода",
                output_path=output_path
            )
            
            assert result_path.exists()
            assert result_path.suffix == '.apkg'


@pytest.mark.django_db
class TestCardsAPI:
    """Тесты для API генерации карточек"""

    def test_generate_cards_authenticated(self):
        """Тест генерации карточек (аутентифицированный пользователь)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.post('/api/cards/generate/', {
            'words': 'casa, livro',
            'language': 'pt',
            'translations': {
                'casa': 'дом',
                'livro': 'книга'
            },
            'deck_name': 'Тестовая колода'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'file_id' in response.data
        assert 'download_url' in response.data
        assert response.data['deck_name'] == 'Тестовая колода'
        assert response.data['cards_count'] == 4  # 2 слова * 2 карточки

    def test_generate_cards_unauthenticated(self):
        """Тест генерации карточек (неаутентифицированный пользователь)"""
        client = APIClient()
        response = client.post('/api/cards/generate/', {
            'words': 'casa',
            'language': 'pt',
            'translations': {'casa': 'дом'},
            'deck_name': 'Тестовая колода'
        }, format='json')
        
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_generate_cards_saves_words(self):
        """Тест что слова сохраняются в БД при генерации"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Проверяем, что слова еще нет
        assert Word.objects.filter(user=user, original_word='casa').count() == 0
        
        response = client.post('/api/cards/generate/', {
            'words': 'casa',
            'language': 'pt',
            'translations': {'casa': 'дом'},
            'deck_name': 'Тестовая колода'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        # Проверяем, что слово сохранилось
        assert Word.objects.filter(user=user, original_word='casa').count() == 1
        word = Word.objects.get(user=user, original_word='casa')
        assert word.translation == 'дом'
        assert word.language == 'pt'

    def test_generate_cards_duplicate_words(self):
        """Тест что дубликаты слов обрабатываются правильно"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем существующее слово
        Word.objects.create(
            user=user,
            original_word='casa',
            translation='старый перевод',
            language='pt'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.post('/api/cards/generate/', {
            'words': 'casa',
            'language': 'pt',
            'translations': {'casa': 'новый перевод'},
            'deck_name': 'Тестовая колода'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        # Проверяем, что перевод обновился
        word = Word.objects.get(user=user, original_word='casa')
        assert word.translation == 'новый перевод'

    def test_download_cards(self):
        """Тест скачивания карточек"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем сгенерированную колоду
        import uuid
        file_id = uuid.uuid4()
        
        # Создаем временный файл
        from django.conf import settings
        temp_dir = Path(settings.MEDIA_ROOT) / 'temp_files'
        temp_dir.mkdir(parents=True, exist_ok=True)
        test_file = temp_dir / f"{file_id}.apkg"
        test_file.write_bytes(b'test file content')
        
        generated_deck = GeneratedDeck.objects.create(
            id=file_id,
            user=user,
            deck_name='Тестовая колода',
            file_path=str(test_file),
            cards_count=2
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get(f'/api/cards/download/{file_id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/apkg'
        
        # Очистка
        if test_file.exists():
            test_file.unlink()

    def test_download_cards_wrong_user(self):
        """Тест что пользователь не может скачать чужую колоду"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        import uuid
        file_id = uuid.uuid4()
        
        from django.conf import settings
        temp_dir = Path(settings.MEDIA_ROOT) / 'temp_files'
        temp_dir.mkdir(parents=True, exist_ok=True)
        test_file = temp_dir / f"{file_id}.apkg"
        test_file.write_bytes(b'test file content')
        
        GeneratedDeck.objects.create(
            id=file_id,
            user=user1,
            deck_name='Колода user1',
            file_path=str(test_file),
            cards_count=2
        )
        
        client = APIClient()
        client.force_authenticate(user=user2)
        
        response = client.get(f'/api/cards/download/{file_id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Очистка
        if test_file.exists():
            test_file.unlink()
