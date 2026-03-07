import json
from unittest.mock import patch, MagicMock

import pytest

from apps.literary_context.search import (
    find_matching_fragment,
    _keyword_match,
    _llm_match,
    HAS_PGVECTOR,
)
from apps.literary_context.models import LiteraryFragment


class TestKeywordMatch:
    def test_exact_match_on_word(self, chekhov_source, fragment_de):
        frag, score = _keyword_match('Marktplatz', 'площадь', chekhov_source, 'de')
        assert frag == fragment_de
        assert score == 1.0

    def test_exact_match_case_insensitive(self, chekhov_source, fragment_de):
        frag, score = _keyword_match('marktplatz', 'площадь', chekhov_source, 'de')
        assert frag == fragment_de
        assert score == 1.0

    def test_partial_match(self, chekhov_source, fragment_de):
        # 'Markt' is contained in 'Marktplatz'
        frag, score = _keyword_match('Markt', 'рынок', chekhov_source, 'de')
        assert frag == fragment_de
        assert score == 0.8

    def test_translation_match(self, chekhov_source, fragment_ru):
        # fragment_ru has key_words=['ploshchad', 'politseiskii', 'nadziratel', 'shinel']
        frag, score = _keyword_match('Platz', 'ploshchad', chekhov_source, 'ru')
        assert frag == fragment_ru
        assert score == 0.7

    def test_content_match(self, chekhov_source, fragment_ru):
        # 'Ochumelov' appears in content but not in key_words
        frag, score = _keyword_match('Ochumelov', 'Очумелов', chekhov_source, 'ru')
        assert frag == fragment_ru
        assert score == 0.6

    def test_no_match(self, chekhov_source, fragment_ru):
        frag, score = _keyword_match('Elefant', 'слон', chekhov_source, 'ru')
        assert frag is None
        assert score == 0.0

    def test_no_fragments(self, chekhov_source):
        frag, score = _keyword_match('Hund', 'собака', chekhov_source, 'de')
        assert frag is None
        assert score == 0.0


class TestLLMMatch:
    @patch('apps.literary_context.search.get_openai_client')
    def test_successful_match(self, mock_client_fn, chekhov_source, fragment_de, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"index": 0, "confidence": 0.85}'
        mock_client.chat.completions.create.return_value = mock_response

        frag, score = _llm_match('Hund', 'dog', chekhov_source, 'de', settings_obj)
        assert frag == fragment_de
        assert score == 0.85

    @patch('apps.literary_context.search.get_openai_client')
    def test_no_match(self, mock_client_fn, chekhov_source, fragment_de, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"index": -1, "confidence": 0}'
        mock_client.chat.completions.create.return_value = mock_response

        frag, score = _llm_match('Elefant', 'elephant', chekhov_source, 'de', settings_obj)
        assert frag is None

    @patch('apps.literary_context.search.get_openai_client')
    def test_api_error_returns_none(self, mock_client_fn, chekhov_source, fragment_de, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception('API error')

        frag, score = _llm_match('Hund', 'dog', chekhov_source, 'de', settings_obj)
        assert frag is None
        assert score == 0.0

    def test_no_fragments_returns_none(self, chekhov_source, settings_obj):
        frag, score = _llm_match('Hund', 'dog', chekhov_source, 'de', settings_obj)
        assert frag is None


class TestFindMatchingFragment:
    def test_keyword_match_returns_first(self, chekhov_source, fragment_de, settings_obj):
        frag, method, score = find_matching_fragment(
            'Marktplatz', 'площадь', chekhov_source, 'de', settings_obj
        )
        assert frag == fragment_de
        assert method == 'keyword'
        assert score == 1.0

    @patch('apps.literary_context.search._llm_match')
    def test_falls_through_to_llm(self, mock_llm, chekhov_source, fragment_de, settings_obj):
        mock_llm.return_value = (fragment_de, 0.9)

        frag, method, score = find_matching_fragment(
            'Elefant', 'слон', chekhov_source, 'de', settings_obj
        )
        assert method == 'llm'
        assert score == 0.9

    @patch('apps.literary_context.search._llm_match')
    def test_no_match_at_all(self, mock_llm, chekhov_source, fragment_de, settings_obj):
        mock_llm.return_value = (None, 0.0)

        frag, method, score = find_matching_fragment(
            'xyz', 'xyz', chekhov_source, 'de', settings_obj
        )
        assert frag is None
        assert method == 'none'
        assert score == 0.0

    def test_llm_disabled(self, chekhov_source, fragment_de, settings_obj):
        settings_obj.llm_match_enabled = False
        settings_obj.save()

        frag, method, score = find_matching_fragment(
            'xyz', 'xyz', chekhov_source, 'de', settings_obj
        )
        assert frag is None
        assert method == 'none'


class TestEmbeddingUtils:
    @patch('apps.literary_context.embedding_utils.get_openai_client')
    def test_generate_embedding(self, mock_client_fn, settings_obj):
        from apps.literary_context.embedding_utils import generate_embedding

        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        mock_response = MagicMock()
        mock_data = MagicMock()
        mock_data.embedding = [0.1] * 1536
        mock_response.data = [mock_data]
        mock_client.embeddings.create.return_value = mock_response

        result = generate_embedding('test text', settings_obj)
        assert len(result) == 1536
        assert result[0] == 0.1

        call_args = mock_client.embeddings.create.call_args
        assert call_args.kwargs['model'] == 'text-embedding-3-small'
        assert call_args.kwargs['dimensions'] == 1536

    @patch('apps.literary_context.embedding_utils.get_openai_client')
    def test_generate_embeddings_batch(self, mock_client_fn, settings_obj):
        from apps.literary_context.embedding_utils import generate_embeddings_batch

        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        mock_data_0 = MagicMock()
        mock_data_0.embedding = [0.1] * 10
        mock_data_0.index = 0
        mock_data_1 = MagicMock()
        mock_data_1.embedding = [0.2] * 10
        mock_data_1.index = 1

        mock_response = MagicMock()
        mock_response.data = [mock_data_1, mock_data_0]  # out of order
        mock_client.embeddings.create.return_value = mock_response

        settings_obj.embedding_dimensions = 10
        settings_obj.save()

        result = generate_embeddings_batch(['text1', 'text2'], settings_obj)
        assert len(result) == 2
        assert result[0] == [0.1] * 10  # sorted by index
        assert result[1] == [0.2] * 10

    @patch('apps.literary_context.embedding_utils.get_openai_client')
    def test_batch_empty_input(self, mock_client_fn, settings_obj):
        from apps.literary_context.embedding_utils import generate_embeddings_batch

        result = generate_embeddings_batch([], settings_obj)
        assert result == []
        mock_client_fn.assert_not_called()


class TestGenerateEmbeddingsCommand:
    @patch('apps.literary_context.embedding_utils.get_openai_client')
    def test_generates_embeddings(self, mock_client_fn, chekhov_source, fragment_de, settings_obj):
        from django.core.management import call_command
        from io import StringIO

        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        mock_data = MagicMock()
        mock_data.embedding = [0.5] * 1536
        mock_data.index = 0
        mock_response = MagicMock()
        mock_response.data = [mock_data]
        mock_client.embeddings.create.return_value = mock_response

        out = StringIO()
        call_command('generate_embeddings', source_slug='chekhov', stdout=out)

        fragment_de.refresh_from_db()
        assert fragment_de.embedding is not None
        assert len(fragment_de.embedding) == 1536
        assert 'Done' in out.getvalue()

    def test_missing_source(self, db):
        from django.core.management import call_command
        from io import StringIO

        err = StringIO()
        call_command('generate_embeddings', source_slug='nonexistent', stderr=err)
        assert 'not found' in err.getvalue()

    @patch('apps.literary_context.embedding_utils.get_openai_client')
    def test_skips_existing_embeddings(self, mock_client_fn, chekhov_source, fragment_de, settings_obj):
        from django.core.management import call_command
        from io import StringIO

        # Set existing embedding
        fragment_de.embedding = [0.1] * 1536
        fragment_de.save()

        out = StringIO()
        call_command('generate_embeddings', source_slug='chekhov', stdout=out)
        assert 'No fragments' in out.getvalue()
        mock_client_fn.assert_not_called()

    @patch('apps.literary_context.embedding_utils.get_openai_client')
    def test_force_regenerates(self, mock_client_fn, chekhov_source, fragment_de, settings_obj):
        from django.core.management import call_command
        from io import StringIO

        fragment_de.embedding = [0.1] * 1536
        fragment_de.save()

        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        mock_data = MagicMock()
        mock_data.embedding = [0.9] * 1536
        mock_data.index = 0
        mock_response = MagicMock()
        mock_response.data = [mock_data]
        mock_client.embeddings.create.return_value = mock_response

        out = StringIO()
        call_command('generate_embeddings', source_slug='chekhov', force=True, stdout=out)

        fragment_de.refresh_from_db()
        assert fragment_de.embedding[0] == 0.9
        assert 'Done' in out.getvalue()
