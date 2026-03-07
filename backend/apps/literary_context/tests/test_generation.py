from unittest.mock import patch, MagicMock

import pytest

from apps.literary_context.generation import (
    generate_word_context,
    generate_batch_context,
    _extract_sentences,
    _generate_hint,
)
from apps.literary_context.models import WordContextMedia


class TestExtractSentences:
    def test_finds_matching_sentences(self):
        content = 'Der Hund lief. Die Katze schlief. Der Hund bellte.'
        result = _extract_sentences(content, 'Hund')
        assert len(result) == 2
        assert 'Hund lief' in result[0]
        assert 'Hund bellte' in result[1]

    def test_case_insensitive(self):
        content = 'Ein hund war da. Die Katze schlief.'
        result = _extract_sentences(content, 'Hund')
        assert len(result) == 1

    def test_no_match_returns_first_sentences(self):
        content = 'Erste Satz. Zweite Satz. Dritte Satz.'
        result = _extract_sentences(content, 'Elefant')
        assert len(result) == 2
        assert 'Erste' in result[0]

    def test_empty_content(self):
        result = _extract_sentences('', 'word')
        assert len(result) <= 2


class TestGenerateHint:
    @patch('apps.literary_context.generation.get_openai_client')
    def test_generates_hint(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'Ein Tier auf dem Marktplatz'
        mock_client.chat.completions.create.return_value = mock_response

        result = _generate_hint('Hund', 'dog', 'Der Hund lief.', 'de', settings_obj)
        assert result == 'Ein Tier auf dem Marktplatz'

    @patch('apps.literary_context.generation.get_openai_client')
    def test_uses_config_model(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'hint'
        mock_client.chat.completions.create.return_value = mock_response

        settings_obj.hint_generation_model = 'gpt-4o'
        settings_obj.save()

        _generate_hint('Hund', 'dog', 'text', 'de', settings_obj)
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == 'gpt-4o'


class TestGenerateWordContext:
    @patch('apps.literary_context.generation.get_openai_client')
    def test_keyword_match_creates_context(
        self, mock_client_fn, chekhov_source, fragment_de, word_marktplatz, settings_obj
    ):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'Generated hint'
        mock_client.chat.completions.create.return_value = mock_response

        ctx = generate_word_context(word_marktplatz, chekhov_source, settings_obj)

        assert ctx.word == word_marktplatz
        assert ctx.source == chekhov_source
        assert ctx.fragment == fragment_de
        assert ctx.anchor == fragment_de.anchor
        assert ctx.match_method == 'keyword'
        assert ctx.match_score == 1.0
        assert not ctx.is_fallback
        assert ctx.hint_text == 'Generated hint'
        assert len(ctx.sentences) >= 1

    def test_no_match_creates_fallback(
        self, chekhov_source, fragment_de, word_hund, settings_obj
    ):
        settings_obj.llm_match_enabled = False
        settings_obj.save()

        ctx = generate_word_context(word_hund, chekhov_source, settings_obj)

        assert ctx.is_fallback
        assert ctx.match_method == 'none'
        assert ctx.fragment is None
        assert ctx.anchor is None

    @patch('apps.literary_context.generation.get_openai_client')
    def test_skip_hint(
        self, mock_client_fn, chekhov_source, fragment_de, word_marktplatz, settings_obj
    ):
        ctx = generate_word_context(
            word_marktplatz, chekhov_source, settings_obj, skip_hint=True
        )
        assert ctx.hint_text == ''
        mock_client_fn.assert_not_called()

    @patch('apps.literary_context.generation.get_openai_client')
    def test_update_or_create_idempotent(
        self, mock_client_fn, chekhov_source, fragment_de, word_marktplatz, settings_obj
    ):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'hint1'
        mock_client.chat.completions.create.return_value = mock_response

        ctx1 = generate_word_context(word_marktplatz, chekhov_source, settings_obj)

        mock_response.choices[0].message.content = 'hint2'
        ctx2 = generate_word_context(word_marktplatz, chekhov_source, settings_obj)

        assert ctx1.id == ctx2.id
        assert WordContextMedia.objects.filter(
            word=word_marktplatz, source=chekhov_source
        ).count() == 1


class TestGenerateBatchContext:
    def test_batch_generation(
        self, chekhov_source, fragment_de, word_marktplatz, word_hund, settings_obj
    ):
        settings_obj.llm_match_enabled = False
        settings_obj.save()

        words = [word_marktplatz, word_hund]
        stats = generate_batch_context(
            words, chekhov_source, settings_obj, skip_hint=True
        )

        assert stats['total'] == 2
        assert stats['generated'] == 2
        assert stats['fallback'] == 1  # word_hund has no match
        assert stats['errors'] == 0

    def test_skip_existing(
        self, chekhov_source, fragment_de, word_marktplatz, settings_obj
    ):
        settings_obj.llm_match_enabled = False
        settings_obj.save()

        # Generate first time
        generate_batch_context(
            [word_marktplatz], chekhov_source, settings_obj, skip_hint=True
        )

        # Generate again with skip_existing=True
        stats = generate_batch_context(
            [word_marktplatz], chekhov_source, settings_obj,
            skip_existing=True, skip_hint=True,
        )
        assert stats['skipped'] == 1
        assert stats['generated'] == 0

    def test_no_skip_existing(
        self, chekhov_source, fragment_de, word_marktplatz, settings_obj
    ):
        settings_obj.llm_match_enabled = False
        settings_obj.save()

        generate_batch_context(
            [word_marktplatz], chekhov_source, settings_obj, skip_hint=True
        )

        stats = generate_batch_context(
            [word_marktplatz], chekhov_source, settings_obj,
            skip_existing=False, skip_hint=True,
        )
        assert stats['skipped'] == 0
        assert stats['generated'] == 1
