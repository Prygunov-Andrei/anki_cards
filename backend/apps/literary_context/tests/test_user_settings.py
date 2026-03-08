"""Tests for per-user LLM settings with fallback to LiteraryContextSettings."""
from unittest.mock import patch, MagicMock

import pytest

from apps.literary_context.generation import (
    _build_effective_config,
    _generate_hint,
    generate_word_context,
)
from apps.literary_context.models import LiteraryContextSettings


class TestBuildEffectiveConfig:
    def test_no_user_returns_config_unchanged(self, settings_obj):
        original_model = settings_obj.hint_generation_model
        result = _build_effective_config(settings_obj, user=None)
        assert result.hint_generation_model == original_model

    def test_user_overrides_model(self, settings_obj, test_user_with_settings):
        result = _build_effective_config(settings_obj, user=test_user_with_settings)
        assert result.hint_generation_model == 'gpt-4o'

    def test_user_overrides_temperature(self, settings_obj, test_user_with_settings):
        result = _build_effective_config(settings_obj, user=test_user_with_settings)
        assert result.hint_temperature == 0.5

    def test_empty_prompt_uses_default(self, settings_obj, test_user):
        """User with empty prompt template -> config default is used."""
        original_template = settings_obj.hint_prompt_template
        result = _build_effective_config(settings_obj, user=test_user)
        assert result.hint_prompt_template == original_template

    def test_user_custom_prompt_overrides(self, settings_obj, test_user_with_settings):
        result = _build_effective_config(settings_obj, user=test_user_with_settings)
        assert 'Custom hint' in result.hint_prompt_template


class TestGenerateHintWithUserSettings:
    @patch('apps.literary_context.generation.get_openai_client')
    def test_uses_user_model(self, mock_client_fn, settings_obj, test_user_with_settings):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'hint'
        mock_client.chat.completions.create.return_value = mock_response

        config = _build_effective_config(settings_obj, user=test_user_with_settings)
        _generate_hint('Hund', 'dog', 'text', 'de', config)

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == 'gpt-4o'

    @patch('apps.literary_context.generation.get_openai_client')
    def test_uses_user_temperature(self, mock_client_fn, settings_obj, test_user_with_settings):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'hint'
        mock_client.chat.completions.create.return_value = mock_response

        config = _build_effective_config(settings_obj, user=test_user_with_settings)
        _generate_hint('Hund', 'dog', 'text', 'de', config)

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['temperature'] == 0.5


class TestGenerateWordContextWithUser:
    @patch('apps.literary_context.generation.get_openai_client')
    def test_user_settings_passed_through(
        self, mock_client_fn, chekhov_source, fragment_de,
        word_marktplatz, settings_obj, test_user_with_settings
    ):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'hint'
        mock_client.chat.completions.create.return_value = mock_response

        ctx = generate_word_context(
            word_marktplatz, chekhov_source, settings_obj,
            user=test_user_with_settings,
        )

        assert ctx.hint_text == 'hint'
        # Verify the LLM was called with user's model
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == 'gpt-4o'
