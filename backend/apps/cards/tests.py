"""
Tests for cards app
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.words.models import Word
from .models import GeneratedDeck, UserPrompt, PartOfSpeechCache
from .utils import create_card_model, create_deck, generate_apkg
from .prompt_utils import get_user_prompt, get_or_create_user_prompt, reset_user_prompt_to_default
from .default_prompts import get_default_prompt, format_prompt, get_image_prompt_for_style, IMAGE_PROMPTS
from .llm_utils import detect_part_of_speech

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
            'deck_name': 'Тестовая колода',
            'image_style': 'balanced'
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


@pytest.mark.django_db
class TestUserPrompts:
    """Тесты для этапа 9 - Редактирование промптов"""

    def test_get_user_prompts_unauthenticated(self):
        """Тест получения промптов без авторизации"""
        client = APIClient()
        response = client.get('/api/user/prompts/')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_get_user_prompts_authenticated(self):
        """Тест получения всех промптов"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/user/prompts/')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 7  # Все типы промптов
        
        # Проверяем наличие всех типов
        prompt_types = [p['prompt_type'] for p in response.data]
        assert 'image' in prompt_types
        assert 'audio' in prompt_types
        assert 'word_analysis' in prompt_types
        assert 'translation' in prompt_types
        assert 'deck_name' in prompt_types
        assert 'part_of_speech' in prompt_types
        assert 'category' in prompt_types

    def test_get_user_prompts_creates_defaults(self):
        """Тест что промпты создаются с заводскими значениями"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/user/prompts/')
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем, что все промпты имеют is_custom: false
        for prompt in response.data:
            assert prompt['is_custom'] is False
            # Промпт не пустой (кроме part_of_speech, который мы убрали)
            if prompt['prompt_type'] != 'part_of_speech':
                assert prompt['custom_prompt']  # Промпт не пустой

    def test_get_specific_prompt(self):
        """Тест получения конкретного промпта"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/user/prompts/image/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['prompt_type'] == 'image'
        assert 'custom_prompt' in response.data
        assert 'is_custom' in response.data

    def test_get_prompt_invalid_type(self):
        """Тест получения промпта с неверным типом"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/user/prompts/invalid_type/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_prompt(self):
        """Тест обновления промпта"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        new_prompt = "Новый промпт для изображения слова '{word}' с переводом '{translation}'."
        response = client.patch('/api/user/prompts/image/update/', {
            'custom_prompt': new_prompt
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['custom_prompt'] == new_prompt
        assert response.data['is_custom'] is True
        
        # Проверяем в БД
        user_prompt = UserPrompt.objects.get(user=user, prompt_type='image')
        assert user_prompt.custom_prompt == new_prompt
        assert user_prompt.is_custom is True

    def test_update_prompt_missing_placeholders(self):
        """Тест обновления промпта без обязательных плейсхолдеров"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Промпт без обязательного плейсхолдера {word}
        invalid_prompt = "Просто изображение с переводом '{translation}'."
        response = client.patch('/api/user/prompts/image/update/', {
            'custom_prompt': invalid_prompt
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data or 'custom_prompt' in response.data

    def test_reset_prompt(self):
        """Тест сброса промпта до заводских настроек"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Сначала изменяем промпт
        custom_prompt = "Кастомный промпт для '{word}' и '{translation}'."
        client.patch('/api/user/prompts/image/update/', {
            'custom_prompt': custom_prompt
        }, format='json')
        
        # Затем сбрасываем
        response = client.post('/api/user/prompts/image/reset/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_custom'] is False
        assert response.data['custom_prompt'] == get_default_prompt('image')
        
        # Проверяем в БД
        user_prompt = UserPrompt.objects.get(user=user, prompt_type='image')
        assert user_prompt.is_custom is False
        assert user_prompt.custom_prompt == get_default_prompt('image')

    def test_prompt_isolation_between_users(self):
        """Тест что промпты разных пользователей изолированы"""
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
        
        client1 = APIClient()
        client1.force_authenticate(user=user1)
        
        client2 = APIClient()
        client2.force_authenticate(user=user2)
        
        # User1 изменяет промпт
        custom_prompt = "Промпт пользователя 1 для '{word}' и '{translation}'."
        client1.patch('/api/user/prompts/image/update/', {
            'custom_prompt': custom_prompt
        }, format='json')
        
        # User2 получает свой промпт (должен быть заводской)
        response = client2.get('/api/user/prompts/image/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_custom'] is False
        assert response.data['custom_prompt'] != custom_prompt


@pytest.mark.django_db
class TestPartOfSpeechDetection:
    """Тесты для этапа 10 - Определение части речи"""

    @patch('apps.cards.llm_utils.get_openai_client')
    def test_detect_part_of_speech_success(self, mock_client):
        """Тест успешного определения части речи"""
        # Мокаем ответ OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"part_of_speech": "noun", "article": null}'
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        result = detect_part_of_speech('casa', 'pt', user)
        
        assert result['part_of_speech'] == 'noun'
        assert result['article'] is None
        
        # Кэширование отключено - результат не сохраняется в кэш

    @patch('apps.cards.llm_utils.get_openai_client')
    def test_detect_part_of_speech_german_with_article(self, mock_client):
        """Тест определения части речи для немецкого с артиклем"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"part_of_speech": "noun", "article": "das"}'
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        result = detect_part_of_speech('haus', 'de', user)
        
        assert result['part_of_speech'] == 'noun'
        assert result['article'] == 'das'
        
        # Кэширование отключено - результат не сохраняется в кэш

    @patch('apps.cards.llm_utils.get_openai_client')
    def test_detect_part_of_speech_uses_cache(self, mock_client):
        """Тест что кэш больше не используется - всегда запрашиваем у LLM"""
        # Кэширование отключено, поэтому даже если есть запись в кэше, 
        # функция все равно будет запрашивать у LLM
        
        # Создаем запись в кэше (для совместимости, но она не используется)
        PartOfSpeechCache.objects.create(
            word='casa',
            language='pt',
            part_of_speech='noun',
            article=None
        )
        
        # Мокаем ответ OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"part_of_speech": "noun", "article": null}'
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Вызываем функцию - должна запросить у LLM, несмотря на наличие кэша
        result = detect_part_of_speech('casa', 'pt', user)
        
        # Проверяем, что OpenAI был вызван (кэш не используется)
        mock_client.assert_called()
        
        assert result['part_of_speech'] == 'noun'



@pytest.mark.django_db
class TestPromptFormatting:
    """Тесты для форматирования промптов"""

    def test_format_prompt_basic(self):
        """Тест базового форматирования промпта"""
        template = "Слово: {word}, Перевод: {translation}"
        result = format_prompt(template, word='casa', translation='дом')
        assert result == "Слово: casa, Перевод: дом"

    def test_format_prompt_all_placeholders(self):
        """Тест форматирования со всеми плейсхолдерами"""
        template = "{word} {translation} {language} {native_language} {learning_language} {english_translation}"
        result = format_prompt(
            template,
            word='casa',
            translation='дом',
            language='pt',
            native_language='русском',
            learning_language='португальском',
            english_translation='house'
        )
        assert 'casa' in result
        assert 'дом' in result
        assert 'pt' in result
        assert 'русском' in result
        assert 'португальском' in result
        assert 'house' in result


@pytest.mark.django_db
class TestDefaultPrompts:
    """Тесты для заводских промптов"""

    def test_get_default_prompt_image(self):
        """Тест получения заводского промпта для изображений"""
        prompt = get_default_prompt('image')
        assert prompt
        assert '{translation}' in prompt

    def test_get_default_prompt_image_with_style(self):
        """Тест получения промпта для изображения с указанным стилем"""
        minimalistic = get_default_prompt('image', 'minimalistic')
        balanced = get_default_prompt('image', 'balanced')
        creative = get_default_prompt('image', 'creative')
        
        assert minimalistic is not None
        assert balanced is not None
        assert creative is not None
        assert '{translation}' in minimalistic
        assert '{translation}' in balanced
        assert '{translation}' in creative
        # Промпты должны отличаться
        assert minimalistic != balanced
        assert balanced != creative
        assert minimalistic != creative

    def test_get_image_prompt_for_style(self):
        """Тест получения промпта для конкретного стиля"""
        minimalistic = get_image_prompt_for_style('minimalistic')
        balanced = get_image_prompt_for_style('balanced')
        creative = get_image_prompt_for_style('creative')
        default = get_image_prompt_for_style('invalid_style')  # Должен вернуть balanced
        
        assert minimalistic == IMAGE_PROMPTS['minimalistic']
        assert balanced == IMAGE_PROMPTS['balanced']
        assert creative == IMAGE_PROMPTS['creative']
        assert default == IMAGE_PROMPTS['balanced']  # По умолчанию

    def test_get_default_prompt_audio(self):
        """Тест получения заводского промпта для аудио"""
        prompt = get_default_prompt('audio')
        assert prompt
        assert '{word}' in prompt

    def test_get_default_prompt_all_types(self):
        """Тест что все типы промптов имеют заводские значения"""
        types = ['image', 'audio', 'word_analysis', 'translation', 'deck_name', 'category']
        for prompt_type in types:
            prompt = get_default_prompt(prompt_type)
            assert prompt, f"Промпт для типа {prompt_type} не найден"


@pytest.mark.django_db
class TestPartOfSpeechCacheModel:
    """Тесты для модели PartOfSpeechCache"""

    def test_create_cache_entry(self):
        """Тест создания записи в кэше"""
        cache_entry = PartOfSpeechCache.objects.create(
            word='casa',
            language='pt',
            part_of_speech='noun',
            article=None
        )
        assert cache_entry.word == 'casa'
        assert cache_entry.language == 'pt'
        assert cache_entry.part_of_speech == 'noun'

    def test_cache_unique_constraint(self):
        """Тест уникальности по word + language"""
        PartOfSpeechCache.objects.create(
            word='casa',
            language='pt',
            part_of_speech='noun'
        )
        
        # Попытка создать дубликат должна вызвать ошибку
        with pytest.raises(Exception):  # IntegrityError или подобное
            PartOfSpeechCache.objects.create(
                word='casa',
                language='pt',
                part_of_speech='verb'  # Другая часть речи, но та же комбинация word+language
            )

    def test_cache_different_languages(self):
        """Тест что одно слово может быть в кэше для разных языков"""
        PartOfSpeechCache.objects.create(
            word='casa',
            language='pt',
            part_of_speech='noun'
        )
        
        PartOfSpeechCache.objects.create(
            word='casa',
            language='es',  # Испанский
            part_of_speech='noun'
        )
        
        assert PartOfSpeechCache.objects.filter(word='casa').count() == 2
