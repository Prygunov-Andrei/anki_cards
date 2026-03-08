"""Tests for media_service.py — path normalization, file upload, media generation."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.test import override_settings

from apps.cards.services.media_service import (
    normalize_media_path,
    get_relative_media_path,
    get_media_url,
    resolve_word_media,
    save_uploaded_file,
    generate_image_for_word,
    generate_audio_for_word,
    edit_image_for_word,
    extract_words_from_photo_service,
)
from apps.words.models import Word
from apps.cards.token_utils import add_tokens, check_balance


MEDIA_ROOT = settings.MEDIA_ROOT


class TestNormalizeMediaPath:
    """Tests for normalize_media_path — the critical path normalization function."""

    def test_empty_path_returns_none(self):
        assert normalize_media_path('') is None
        assert normalize_media_path(None) is None

    def test_full_url_with_media_subdir(self):
        result = normalize_media_path(
            'https://example.com/media/audio/test.mp3', media_subdir='audio')
        assert result == Path(MEDIA_ROOT) / 'audio' / 'test.mp3'

    def test_full_url_with_media_images(self):
        result = normalize_media_path(
            'https://example.com/media/images/pic.jpg', media_subdir='images')
        assert result == Path(MEDIA_ROOT) / 'images' / 'pic.jpg'

    def test_full_url_with_generic_media(self):
        result = normalize_media_path(
            'https://example.com/media/audio/test.mp3')
        assert result == Path(MEDIA_ROOT) / 'audio' / 'test.mp3'

    def test_full_url_without_media_marker(self):
        result = normalize_media_path(
            'https://example.com/other/test.mp3', media_subdir='audio')
        assert result == Path(MEDIA_ROOT) / 'audio' / 'test.mp3'

    def test_full_url_without_media_no_subdir(self):
        result = normalize_media_path('https://example.com/other/test.mp3')
        assert result is None

    def test_media_prefixed_path(self):
        result = normalize_media_path('/media/audio/test.mp3')
        assert result == Path(MEDIA_ROOT) / 'audio' / 'test.mp3'

    def test_media_prefixed_path_images(self):
        result = normalize_media_path('/media/images/pic.jpg')
        assert result == Path(MEDIA_ROOT) / 'images' / 'pic.jpg'

    def test_absolute_path(self):
        abs_path = '/var/www/media/audio/test.mp3'
        result = normalize_media_path(abs_path)
        assert result == Path(abs_path)

    def test_relative_path(self):
        result = normalize_media_path('audio/test.mp3')
        assert result == Path(MEDIA_ROOT) / 'audio' / 'test.mp3'

    def test_relative_path_just_filename(self):
        result = normalize_media_path('test.mp3')
        assert result == Path(MEDIA_ROOT) / 'test.mp3'

    def test_url_with_nested_path(self):
        result = normalize_media_path(
            'https://cdn.example.com/v1/media/images/2024/01/pic.jpg',
            media_subdir='images')
        assert result == Path(MEDIA_ROOT) / 'images' / '2024/01/pic.jpg'

    def test_http_url(self):
        result = normalize_media_path(
            'http://localhost:8000/media/audio/test.mp3', media_subdir='audio')
        assert result == Path(MEDIA_ROOT) / 'audio' / 'test.mp3'


class TestGetRelativeMediaPath:
    def test_relative_from_media_root(self):
        abs_path = Path(MEDIA_ROOT) / 'images' / 'test.jpg'
        assert get_relative_media_path(abs_path) == 'images/test.jpg'


class TestGetMediaUrl:
    def test_builds_url(self):
        url = get_media_url('images/test.jpg')
        assert url == f'{settings.MEDIA_URL}images/test.jpg'


@pytest.mark.django_db
class TestResolveWordMedia:
    def test_exact_match(self, user, tmp_path):
        word_obj = Word.objects.create(
            user=user, original_word='Hund', translation='dog', language='de')

        audio_file = tmp_path / 'test.mp3'
        audio_file.touch()

        media_dict = {'Hund': str(audio_file)}
        path, is_new = resolve_word_media('Hund', media_dict, word_obj, 'audio')
        assert path == audio_file
        assert is_new is True

    def test_normalized_match(self, user, tmp_path):
        word_obj = Word.objects.create(
            user=user, original_word='Hund.', translation='dog', language='de')

        audio_file = tmp_path / 'test.mp3'
        audio_file.touch()

        media_dict = {'Hund': str(audio_file)}
        path, is_new = resolve_word_media('Hund.', media_dict, word_obj, 'audio')
        assert path == audio_file
        assert is_new is True

    def test_no_match_no_db(self, user):
        word_obj = Word.objects.create(
            user=user, original_word='Hund', translation='dog', language='de')

        path, is_new = resolve_word_media('Hund', {}, word_obj, 'audio')
        assert path is None
        assert is_new is False


@pytest.mark.django_db
class TestGenerateImageForWord:
    @patch('apps.cards.services.media_service.generate_image')
    def test_generates_and_returns_data(self, mock_gen, user):
        add_tokens(user, 10)
        test_path = Path(MEDIA_ROOT) / 'images' / 'test.jpg'
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.touch()

        mock_gen.return_value = (test_path, 'test prompt')

        result = generate_image_for_word(
            user=user, word='Hund', translation='dog', language='de')

        assert 'image_url' in result
        assert 'prompt' in result
        assert result['prompt'] == 'test prompt'

    def test_insufficient_tokens_raises(self, user):
        with pytest.raises(ValueError, match='Недостаточно токенов'):
            generate_image_for_word(
                user=user, word='Hund', translation='dog', language='de')

    @patch('apps.cards.services.media_service.generate_image')
    def test_refunds_on_error(self, mock_gen, user):
        add_tokens(user, 10)
        initial = check_balance(user)
        mock_gen.side_effect = RuntimeError('API error')

        with pytest.raises(RuntimeError):
            generate_image_for_word(
                user=user, word='Hund', translation='dog', language='de')

        assert check_balance(user) == initial


@pytest.mark.django_db
class TestGenerateAudioForWord:
    @patch('apps.cards.services.media_service.generate_audio_with_tts')
    def test_generates_audio(self, mock_gen, user):
        add_tokens(user, 10)
        test_path = Path(MEDIA_ROOT) / 'audio' / 'test.mp3'
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.touch()

        mock_gen.return_value = test_path

        result = generate_audio_for_word(user=user, word='Hund', language='de')
        assert 'audio_url' in result
        assert 'audio_id' in result

    def test_insufficient_tokens_raises(self, user):
        with pytest.raises(ValueError, match='Недостаточно токенов'):
            generate_audio_for_word(user=user, word='Hund', language='de')

    @patch('apps.cards.services.media_service.generate_audio_with_tts')
    def test_gtts_is_free(self, mock_gen, user):
        """gTTS doesn't cost tokens."""
        test_path = Path(MEDIA_ROOT) / 'audio' / 'test.mp3'
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.touch()
        mock_gen.return_value = test_path

        result = generate_audio_for_word(
            user=user, word='Hund', language='de', provider='gtts')
        assert 'audio_url' in result

    @patch('apps.cards.services.media_service.generate_audio_with_tts')
    def test_refunds_on_error(self, mock_gen, user):
        add_tokens(user, 10)
        initial = check_balance(user)
        mock_gen.side_effect = RuntimeError('TTS API error')

        with pytest.raises(RuntimeError):
            generate_audio_for_word(
                user=user, word='Hund', language='de', provider='openai')

        assert check_balance(user) == initial


@pytest.mark.django_db
class TestEditImageForWord:
    @patch('apps.cards.services.media_service.edit_image_with_gemini')
    def test_edits_image(self, mock_edit, user):
        add_tokens(user, 10)
        word_obj = Word.objects.create(
            user=user, original_word='Hund', translation='dog', language='de')

        # Create source image
        source_path = Path(MEDIA_ROOT) / 'images' / 'source.jpg'
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.touch()
        word_obj.image_file.name = 'images/source.jpg'
        word_obj.save()

        new_path = Path(MEDIA_ROOT) / 'images' / 'edited.jpg'
        new_path.touch()
        mock_edit.return_value = (new_path, 'edit prompt')

        result = edit_image_for_word(user=user, word_id=word_obj.id, mixin='add hat')
        assert result['mixin'] == 'add hat'
        assert 'image_url' in result

    def test_no_image_raises(self, user):
        word_obj = Word.objects.create(
            user=user, original_word='Hund', translation='dog', language='de')

        with pytest.raises(ValueError, match='нет изображения'):
            edit_image_for_word(user=user, word_id=word_obj.id, mixin='add hat')


@pytest.mark.django_db
class TestExtractWordsFromPhoto:
    @patch('apps.cards.services.media_service.extract_words_from_photo')
    def test_extracts_words(self, mock_extract, user):
        add_tokens(user, 10)
        mock_extract.return_value = ['Hund', 'Katze']

        result = extract_words_from_photo_service(
            user=user, image_data=b'fake-image', target_lang='de', source_lang='ru')
        assert result == ['Hund', 'Katze']

    def test_insufficient_tokens(self, user):
        with pytest.raises(ValueError, match='Недостаточно токенов'):
            extract_words_from_photo_service(
                user=user, image_data=b'fake', target_lang='de', source_lang='ru')

    @patch('apps.cards.services.media_service.extract_words_from_photo')
    def test_refunds_on_error(self, mock_extract, user):
        add_tokens(user, 10)
        initial = check_balance(user)
        mock_extract.side_effect = RuntimeError('Vision API error')

        with pytest.raises(RuntimeError):
            extract_words_from_photo_service(
                user=user, image_data=b'fake', target_lang='de', source_lang='ru')

        assert check_balance(user) == initial
