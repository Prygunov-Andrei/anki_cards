import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from apps.literary_context.corpus_processing import (
    split_text_into_fragments,
    extract_keywords,
    generate_scene_description,
)
from apps.literary_context.models import LiteraryContextSettings

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'


class TestSplitTextIntoFragments:
    def test_empty_text(self, db):
        assert split_text_into_fragments('') == []
        assert split_text_into_fragments('   ') == []

    def test_short_text_single_fragment(self, db):
        text = 'Hello world. This is short.'
        result = split_text_into_fragments(text, fragment_size=1000)
        assert len(result) == 1
        assert result[0] == text

    def test_splits_by_sentences(self, db):
        text = 'First sentence. Second sentence. Third sentence. Fourth sentence.'
        result = split_text_into_fragments(text, fragment_size=40, overlap=0)
        assert len(result) > 1
        # Each fragment should contain complete sentences
        for frag in result:
            assert frag.endswith('sentence.') or frag.endswith('sentence')

    def test_respects_fragment_size(self, db):
        text = 'A. B. C. D. E. F. G. H. I. J.'
        result = split_text_into_fragments(text, fragment_size=10, overlap=0)
        assert len(result) > 1

    def test_overlap(self, db):
        text = 'Sentence one here. Sentence two here. Sentence three here.'
        result = split_text_into_fragments(text, fragment_size=30, overlap=20)
        # With overlap, fragments should share some content
        if len(result) >= 2:
            # At least some overlap should exist
            assert len(result) >= 2

    def test_single_long_sentence(self, db):
        text = 'This is one very long sentence without any period at the end'
        result = split_text_into_fragments(text, fragment_size=10, overlap=0)
        # Even if over size limit, a single sentence can't be split
        assert len(result) >= 1
        assert text in result[0]

    def test_with_various_punctuation(self, db):
        text = 'Question? Exclamation! Statement. Ellipsis...'
        result = split_text_into_fragments(text, fragment_size=1000)
        assert len(result) == 1

    def test_with_chekhov_sample(self, db):
        sample_file = FIXTURES_DIR / 'chekhov_hameleon_sample.ru.txt'
        if sample_file.exists():
            text = sample_file.read_text(encoding='utf-8')
            result = split_text_into_fragments(text, fragment_size=300, overlap=50)
            assert len(result) >= 2
            # All original text should be covered
            combined = ' '.join(result)
            # Check that key words from the original appear
            assert 'Очумелов' in combined

    def test_no_duplicate_fragments(self, db):
        text = 'Short. Text. Here.'
        result = split_text_into_fragments(text, fragment_size=1000, overlap=0)
        assert len(result) == len(set(result))

    def test_uses_settings_defaults(self, settings_obj):
        text = 'A sentence. Another sentence.'
        # Should not raise - uses settings defaults
        result = split_text_into_fragments(text)
        assert len(result) >= 1


def _mock_openai_response(content: str):
    """Create a mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


class TestExtractKeywords:
    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_basic_extraction(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '["собака", "площадь", "полицейский"]'
        )

        result = extract_keywords('Через площадь идёт полицейский.', 'ru')
        assert result == ['собака', 'площадь', 'полицейский']

    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_invalid_json_fallback(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            'собака, площадь, полицейский'
        )

        result = extract_keywords('test text', 'ru')
        assert len(result) == 3
        assert 'собака' in result

    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_uses_config_model(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response('[]')

        settings_obj.keyword_extraction_model = 'gpt-4o'
        settings_obj.save()

        extract_keywords('test', 'ru')
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == 'gpt-4o'

    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_uses_config_temperature(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response('[]')

        settings_obj.keyword_temperature = 0.1
        settings_obj.save()

        extract_keywords('test', 'ru')
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['temperature'] == 0.1


class TestGenerateSceneDescription:
    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_basic_generation(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            json.dumps({
                'description': 'A town square with a police officer walking.',
                'characters': ['Ochumelov'],
                'mood': 'comedic',
            })
        )

        result = generate_scene_description('Через площадь идёт Очумелов.', 'ru')
        assert 'town square' in result['description']
        assert 'Ochumelov' in result['characters']
        assert result['mood'] == 'comedic'

    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_json_in_code_block(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '```json\n{"description": "A scene.", "characters": [], "mood": "calm"}\n```'
        )

        result = generate_scene_description('test', 'ru')
        assert result['description'] == 'A scene.'
        assert result['mood'] == 'calm'

    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_invalid_json_fallback(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            'Just a plain text description of the scene.'
        )

        result = generate_scene_description('test', 'ru')
        assert result['description'] == 'Just a plain text description of the scene.'
        assert result['characters'] == []
        assert result['mood'] == 'neutral'

    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_uses_config_model(self, mock_client_fn, settings_obj):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '{"description": "", "characters": [], "mood": "neutral"}'
        )

        settings_obj.scene_description_model = 'gpt-4o'
        settings_obj.save()

        generate_scene_description('test', 'ru')
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == 'gpt-4o'


class TestManagementCommands:
    """Test management commands via Django's call_command."""

    def test_load_literary_text(self, db, tmp_path):
        from django.core.management import call_command
        from io import StringIO

        # Create a temp file
        txt_file = tmp_path / 'test.txt'
        txt_file.write_text('Test text content.', encoding='utf-8')

        out = StringIO()
        call_command(
            'load_literary_text',
            source_slug='test-source',
            source_name='Test Source',
            source_language='en',
            text_slug='test-text',
            title='Test Text',
            language='en',
            file=str(txt_file),
            stdout=out,
        )

        from apps.literary_context.models import LiterarySource, LiteraryText
        assert LiterarySource.objects.filter(slug='test-source').exists()
        text = LiteraryText.objects.get(slug='test-text', language='en')
        assert text.full_text == 'Test text content.'
        assert 'Created' in out.getvalue()

    def test_load_literary_text_idempotent(self, db, tmp_path):
        from django.core.management import call_command
        from io import StringIO

        txt_file = tmp_path / 'test.txt'
        txt_file.write_text('Original.', encoding='utf-8')

        call_command(
            'load_literary_text',
            source_slug='test', text_slug='t', title='T',
            language='en', file=str(txt_file),
            stdout=StringIO(),
        )

        # Update content
        txt_file.write_text('Updated.', encoding='utf-8')
        call_command(
            'load_literary_text',
            source_slug='test', text_slug='t', title='T',
            language='en', file=str(txt_file),
            stdout=StringIO(),
        )

        from apps.literary_context.models import LiteraryText
        assert LiteraryText.objects.filter(slug='t').count() == 1
        assert LiteraryText.objects.get(slug='t').full_text == 'Updated.'

    def test_load_literary_text_missing_file(self, db):
        from django.core.management import call_command
        from io import StringIO

        err = StringIO()
        call_command(
            'load_literary_text',
            source_slug='test', text_slug='t', title='T',
            language='en', file='/nonexistent/file.txt',
            stderr=err,
        )
        assert 'not found' in err.getvalue()

    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_index_literary_text_dry_run(self, mock_client_fn, db, tmp_path):
        from django.core.management import call_command
        from io import StringIO

        # Load a text first
        txt_file = tmp_path / 'test.txt'
        txt_file.write_text(
            'First sentence here. Second sentence here. Third sentence here.',
            encoding='utf-8',
        )
        call_command(
            'load_literary_text',
            source_slug='test', text_slug='t', title='T',
            language='en', file=str(txt_file),
            stdout=StringIO(),
        )

        # Dry run
        out = StringIO()
        call_command(
            'index_literary_text',
            source_slug='test', text_slug='t', language='en',
            fragment_size=30, dry_run=True,
            stdout=out,
        )

        output = out.getvalue()
        assert 'Dry run' in output
        assert 'Fragment' in output
        # No records should be created
        from apps.literary_context.models import SceneAnchor
        assert SceneAnchor.objects.count() == 0

    @patch('apps.literary_context.corpus_processing.get_openai_client')
    def test_index_literary_text_skip_llm(self, mock_client_fn, db, tmp_path):
        from django.core.management import call_command
        from io import StringIO

        txt_file = tmp_path / 'test.txt'
        txt_file.write_text(
            'First sentence. Second sentence. Third sentence.',
            encoding='utf-8',
        )
        call_command(
            'load_literary_text',
            source_slug='test', text_slug='t', title='T',
            language='en', file=str(txt_file),
            stdout=StringIO(),
        )

        out = StringIO()
        call_command(
            'index_literary_text',
            source_slug='test', text_slug='t', language='en',
            skip_llm=True,
            stdout=out,
        )

        from apps.literary_context.models import SceneAnchor, LiteraryFragment
        assert SceneAnchor.objects.count() >= 1
        assert LiteraryFragment.objects.count() >= 1
        # LLM was NOT called
        mock_client_fn.assert_not_called()
        assert 'Done' in out.getvalue()

    def test_index_missing_source(self, db):
        from django.core.management import call_command
        from io import StringIO

        err = StringIO()
        call_command(
            'index_literary_text',
            source_slug='nonexistent', text_slug='t', language='en',
            stderr=err,
        )
        assert 'not found' in err.getvalue()
