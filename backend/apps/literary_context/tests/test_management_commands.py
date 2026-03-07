"""Tests for Phase 10 management commands."""
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest
from django.core.management import call_command, CommandError

from apps.literary_context.models import (
    LiterarySource, LiteraryText, SceneAnchor,
    LiteraryFragment, WordContextMedia, LiteraryContextSettings,
)
from apps.words.models import Word


class TestGenerateBatchContextCommand:
    def test_no_words(self, chekhov_source, settings_obj):
        out = StringIO()
        call_command('generate_batch_context', source_slug='chekhov', stdout=out)
        assert 'No words to process' in out.getvalue()

    def test_invalid_source(self, db):
        with pytest.raises(CommandError, match='not found'):
            call_command('generate_batch_context', source_slug='nonexistent')

    @patch('apps.literary_context.generation.find_matching_fragment')
    def test_generates_for_user_words(
        self, mock_find, chekhov_source, fragment_de,
        word_marktplatz, word_hund, settings_obj
    ):
        mock_find.return_value = (fragment_de, 'keyword', 1.0)
        out = StringIO()
        call_command(
            'generate_batch_context',
            source_slug='chekhov',
            user_id=word_marktplatz.user_id,
            skip_hint=True,
            stdout=out, stderr=StringIO(),
        )
        output = out.getvalue()
        assert '2 generated' in output
        assert WordContextMedia.objects.filter(source=chekhov_source).count() == 2

    @patch('apps.literary_context.generation.find_matching_fragment')
    def test_skip_existing(
        self, mock_find, chekhov_source, fragment_de,
        word_marktplatz, word_hund, settings_obj
    ):
        mock_find.return_value = (fragment_de, 'keyword', 1.0)
        # Pre-create context for one word
        WordContextMedia.objects.create(
            word=word_marktplatz, source=chekhov_source,
            match_method='keyword', match_score=1.0,
        )
        out = StringIO()
        call_command(
            'generate_batch_context',
            source_slug='chekhov',
            skip_hint=True,
            stdout=out, stderr=StringIO(),
        )
        # Should only process word_hund (word_marktplatz skipped)
        assert '1 generated' in out.getvalue()

    @patch('apps.literary_context.generation.find_matching_fragment')
    def test_force_regenerates(
        self, mock_find, chekhov_source, fragment_de,
        word_marktplatz, settings_obj
    ):
        mock_find.return_value = (fragment_de, 'keyword', 1.0)
        WordContextMedia.objects.create(
            word=word_marktplatz, source=chekhov_source,
            match_method='keyword', match_score=0.5,
        )
        out = StringIO()
        call_command(
            'generate_batch_context',
            source_slug='chekhov',
            force=True,
            skip_hint=True,
            stdout=out, stderr=StringIO(),
        )
        assert '1 generated' in out.getvalue()

    @patch('apps.literary_context.generation.find_matching_fragment')
    def test_limit(
        self, mock_find, chekhov_source, fragment_de,
        word_marktplatz, word_hund, settings_obj
    ):
        mock_find.return_value = (fragment_de, 'keyword', 1.0)
        out = StringIO()
        call_command(
            'generate_batch_context',
            source_slug='chekhov',
            limit=1,
            skip_hint=True,
            stdout=out, stderr=StringIO(),
        )
        assert '1 generated' in out.getvalue()

    @patch('apps.literary_context.generation.find_matching_fragment')
    def test_language_filter(
        self, mock_find, chekhov_source, fragment_de,
        test_user, settings_obj
    ):
        mock_find.return_value = (fragment_de, 'keyword', 1.0)
        word_de = Word.objects.create(
            user=test_user, original_word='Hund', translation='dog', language='de'
        )
        word_ru = Word.objects.create(
            user=test_user, original_word='собака', translation='dog', language='ru'
        )
        out = StringIO()
        call_command(
            'generate_batch_context',
            source_slug='chekhov',
            language='de',
            skip_hint=True,
            stdout=out, stderr=StringIO(),
        )
        assert '1 generated' in out.getvalue()


class TestLiteraryContextStatsCommand:
    def test_no_sources(self, db):
        out = StringIO()
        call_command('literary_context_stats', stdout=out)
        assert 'No literary sources found' in out.getvalue()

    def test_basic_stats(self, chekhov_source, hameleon_text_ru,
                         scene_anchor, fragment_ru):
        out = StringIO()
        call_command('literary_context_stats', stdout=out)
        output = out.getvalue()
        assert 'Chekhov Stories' in output
        assert 'Texts: 1' in output
        assert 'Scene Anchors: 1' in output
        assert 'Fragments: 1' in output

    def test_filter_by_source(self, chekhov_source, bible_source):
        out = StringIO()
        call_command('literary_context_stats', source_slug='chekhov', stdout=out)
        output = out.getvalue()
        assert 'Chekhov Stories' in output
        assert 'Bible' not in output

    def test_word_context_media_stats(
        self, chekhov_source, fragment_de, scene_anchor,
        word_marktplatz, word_hund
    ):
        WordContextMedia.objects.create(
            word=word_marktplatz, source=chekhov_source,
            anchor=scene_anchor, fragment=fragment_de,
            hint_text='hint', match_method='keyword', match_score=1.0,
        )
        WordContextMedia.objects.create(
            word=word_hund, source=chekhov_source,
            is_fallback=True, match_method='fallback', match_score=0.0,
        )
        out = StringIO()
        call_command('literary_context_stats', stdout=out)
        output = out.getvalue()
        assert 'Word Context Media: 2' in output
        assert 'Fallback: 1' in output

    def test_totals(self, chekhov_source, bible_source):
        out = StringIO()
        call_command('literary_context_stats', stdout=out)
        output = out.getvalue()
        assert 'TOTALS' in output
        assert 'Sources: 2' in output
