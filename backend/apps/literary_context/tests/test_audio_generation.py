import io
from unittest.mock import patch, MagicMock

import pytest

from apps.literary_context.audio_generation import (
    generate_literary_audio,
    generate_audio_elevenlabs,
    generate_audio_openai,
    generate_audio_gtts,
    _save_audio_bytes,
)


class TestSaveAudioBytes:
    def test_saves_file(self, tmp_path):
        from django.conf import settings
        original = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = str(tmp_path)
        try:
            result = _save_audio_bytes(b'fake audio data', 'test_audio')
            assert result.startswith('test_audio/')
            assert result.endswith('.mp3')
            full_path = tmp_path / result
            assert full_path.exists()
            assert full_path.read_bytes() == b'fake audio data'
        finally:
            settings.MEDIA_ROOT = original


class TestElevenLabsAudio:
    @patch.dict('os.environ', {'ELEVENLABS_API_KEY': 'test-key'})
    @patch('apps.literary_context.audio_generation.HAS_ELEVENLABS', True)
    @patch('apps.literary_context.audio_generation.ElevenLabs', create=True)
    def test_success(self, mock_elevenlabs_cls):
        mock_client = MagicMock()
        mock_elevenlabs_cls.return_value = mock_client
        mock_client.text_to_speech.convert.return_value = iter([b'audio', b'data'])

        result = generate_audio_elevenlabs('Hallo Welt', 'de')
        assert result == b'audiodata'

    @patch('apps.literary_context.audio_generation.HAS_ELEVENLABS', False)
    def test_not_installed(self):
        result = generate_audio_elevenlabs('test', 'de')
        assert result is None

    @patch.dict('os.environ', {}, clear=True)
    @patch('apps.literary_context.audio_generation.HAS_ELEVENLABS', True)
    def test_no_api_key(self):
        import os
        os.environ.pop('ELEVENLABS_API_KEY', None)
        result = generate_audio_elevenlabs('test', 'de')
        assert result is None


class TestOpenAIAudio:
    @patch('apps.core.llm.get_openai_client')
    def test_success(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.audio.speech.create.return_value = MagicMock(content=b'openai audio')

        result = generate_audio_openai('Hallo', 'de')
        assert result == b'openai audio'

    @patch('apps.core.llm.get_openai_client')
    def test_failure(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.audio.speech.create.side_effect = Exception('API error')

        result = generate_audio_openai('test', 'de')
        assert result is None


class TestGenerateLiteraryAudio:
    @patch('apps.literary_context.audio_generation.generate_audio_gtts')
    @patch('apps.literary_context.audio_generation.generate_audio_openai')
    @patch('apps.literary_context.audio_generation.generate_audio_elevenlabs')
    def test_elevenlabs_first(self, mock_el, mock_openai, mock_gtts, tmp_path):
        from django.conf import settings
        original = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = str(tmp_path)
        try:
            mock_el.return_value = b'elevenlabs audio'

            result = generate_literary_audio('test', 'de')
            assert result is not None
            assert result.endswith('.mp3')
            mock_openai.assert_not_called()
            mock_gtts.assert_not_called()
        finally:
            settings.MEDIA_ROOT = original

    @patch('apps.literary_context.audio_generation.generate_audio_gtts')
    @patch('apps.literary_context.audio_generation.generate_audio_openai')
    @patch('apps.literary_context.audio_generation.generate_audio_elevenlabs')
    def test_fallback_to_openai(self, mock_el, mock_openai, mock_gtts, tmp_path):
        from django.conf import settings
        original = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = str(tmp_path)
        try:
            mock_el.return_value = None
            mock_openai.return_value = b'openai audio'

            result = generate_literary_audio('test', 'de')
            assert result is not None
            mock_gtts.assert_not_called()
        finally:
            settings.MEDIA_ROOT = original

    @patch('apps.literary_context.audio_generation.generate_audio_gtts')
    @patch('apps.literary_context.audio_generation.generate_audio_openai')
    @patch('apps.literary_context.audio_generation.generate_audio_elevenlabs')
    def test_fallback_to_gtts(self, mock_el, mock_openai, mock_gtts, tmp_path):
        from django.conf import settings
        original = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = str(tmp_path)
        try:
            mock_el.return_value = None
            mock_openai.return_value = None
            mock_gtts.return_value = b'gtts audio'

            result = generate_literary_audio('test', 'de')
            assert result is not None
        finally:
            settings.MEDIA_ROOT = original

    @patch('apps.literary_context.audio_generation.generate_audio_gtts')
    @patch('apps.literary_context.audio_generation.generate_audio_openai')
    @patch('apps.literary_context.audio_generation.generate_audio_elevenlabs')
    def test_all_fail(self, mock_el, mock_openai, mock_gtts):
        mock_el.return_value = None
        mock_openai.return_value = None
        mock_gtts.return_value = None

        result = generate_literary_audio('test', 'de')
        assert result is None
