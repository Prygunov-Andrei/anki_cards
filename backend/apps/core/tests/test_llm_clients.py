"""Tests for core LLM clients."""
import pytest
from unittest.mock import patch

from apps.core.llm.clients import get_openai_client, get_gemini_client


class TestGetOpenAIClient:
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_returns_client(self):
        client = get_openai_client()
        assert client is not None

    @patch.dict('os.environ', {}, clear=True)
    def test_raises_without_key(self):
        with pytest.raises(ValueError, match='OPENAI_API_KEY'):
            get_openai_client()


class TestGetGeminiClient:
    @patch.dict('os.environ', {}, clear=True)
    def test_raises_without_key(self):
        with pytest.raises(ValueError, match='GEMINI_API_KEY'):
            get_gemini_client()

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'})
    @patch('apps.core.llm.clients.genai')
    @patch('apps.core.llm.clients.GEMINI_AVAILABLE', True)
    def test_returns_client_with_key(self, mock_genai):
        result = get_gemini_client()
        mock_genai.configure.assert_called_once_with(api_key='test-key')
        assert result == mock_genai

    @patch('apps.core.llm.clients.GEMINI_AVAILABLE', False)
    def test_raises_when_not_available(self):
        with pytest.raises(ValueError, match='не установлен'):
            get_gemini_client()
