"""End-to-end integration tests for the literary context pipeline."""
from unittest.mock import patch, MagicMock

import pytest
from rest_framework.test import APIClient

from apps.literary_context.models import (
    LiterarySource, LiteraryText, SceneAnchor, LiteraryFragment,
    WordContextMedia, LiteraryContextSettings,
)
from apps.literary_context.corpus_processing import split_text_into_fragments
from apps.literary_context.generation import generate_word_context
from apps.words.models import Word


SAMPLE_TEXT = (
    "Cherez bazarnuyu ploshchad idyot politseiskii nadziratel Ochumelov "
    "v novoi shineli. Za nim shagaet gorodovoi s reshetom. "
    "Vokrug tishina. Na ploshchadi ni dushi. "
    "Otkrytye dveri lavok i kabakov gliadiat na svet bozhii unylo. "
    "U dveri lavki kupca Pichuginа stoit Hund i skorbit."
)


@pytest.fixture
def full_setup(db):
    """Set up a complete literary context pipeline."""
    settings = LiteraryContextSettings.get()
    settings.llm_match_enabled = False
    settings.save()

    source = LiterarySource.objects.create(
        slug='chekhov-test', name='Chekhov Test',
        source_language='ru', available_languages=['ru', 'de'],
    )
    text = LiteraryText.objects.create(
        source=source, slug='hameleon', title='Hameleon',
        language='de', full_text=SAMPLE_TEXT,
    )

    # Split into fragments
    fragments_data = split_text_into_fragments(SAMPLE_TEXT, fragment_size=200, overlap=20)

    anchors = []
    fragments = []
    for i, frag_text in enumerate(fragments_data):
        anchor = SceneAnchor.objects.create(
            source=source, text_slug='hameleon', fragment_index=i,
            scene_description=f'Scene {i}', mood='neutral',
        )
        fragment = LiteraryFragment.objects.create(
            anchor=anchor, text=text, content=frag_text,
            key_words=['Hund', 'ploshchad', 'Ochumelov'],
        )
        anchors.append(anchor)
        fragments.append(fragment)

    return {
        'source': source, 'text': text,
        'anchors': anchors, 'fragments': fragments,
        'settings': settings,
    }


class TestEndToEnd:
    def test_search_and_generate(self, full_setup, test_user):
        """Word search -> fragment match -> context media creation."""
        source = full_setup['source']
        word = Word.objects.create(
            user=test_user, original_word='Hund',
            translation='dog', language='de',
        )

        ctx = generate_word_context(word, source, skip_hint=True)

        assert not ctx.is_fallback
        assert ctx.match_method == 'keyword'
        assert ctx.match_score > 0
        assert ctx.fragment is not None
        assert ctx.anchor is not None

    def test_fallback_for_unknown_word(self, full_setup, test_user):
        """Unknown word -> fallback context."""
        source = full_setup['source']
        word = Word.objects.create(
            user=test_user, original_word='Schmetterling',
            translation='butterfly', language='de',
        )

        ctx = generate_word_context(word, source, skip_hint=True)

        assert ctx.is_fallback
        assert ctx.match_method == 'none'

    def test_context_switching_via_api(self, full_setup, test_user):
        """User switches context -> word API returns overlaid data."""
        source = full_setup['source']
        word = Word.objects.create(
            user=test_user, original_word='Hund',
            translation='dog', language='de',
        )
        ctx = generate_word_context(word, source, skip_hint=True)

        client = APIClient()
        client.force_authenticate(user=test_user)

        # Without context -- no overlay
        response = client.get(f'/api/words/{word.id}/')
        assert response.status_code == 200
        assert response.data.get('literary_context') is None

        # Activate context
        test_user.active_literary_source = source
        test_user.save()

        # With context -- overlay applied
        response = client.get(f'/api/words/{word.id}/')
        assert response.status_code == 200
        lc = response.data.get('literary_context')
        assert lc is not None
        assert lc['source_slug'] == 'chekhov-test'
        assert not lc['is_fallback']

        # Deactivate context
        test_user.active_literary_source = None
        test_user.save()

        response = client.get(f'/api/words/{word.id}/')
        assert response.data.get('literary_context') is None

    def test_no_duplicate_on_regenerate(self, full_setup, test_user):
        """Regenerating context updates existing record, not creating a new one."""
        source = full_setup['source']
        word = Word.objects.create(
            user=test_user, original_word='Hund',
            translation='dog', language='de',
        )

        ctx1 = generate_word_context(word, source, skip_hint=True)
        ctx2 = generate_word_context(word, source, skip_hint=True)

        assert ctx1.id == ctx2.id
        assert WordContextMedia.objects.filter(word=word, source=source).count() == 1

    def test_cross_language_image_sharing(self, db, test_user):
        """Two fragments (ru, de) on same anchor share one image."""
        source = LiterarySource.objects.create(
            slug='test-sharing', name='Test Sharing',
            source_language='ru', available_languages=['ru', 'de'],
        )
        text_ru = LiteraryText.objects.create(
            source=source, slug='story', title='Story RU',
            language='ru', full_text='Sobaka bezhit po ploshchadi.',
        )
        text_de = LiteraryText.objects.create(
            source=source, slug='story', title='Story DE',
            language='de', full_text='Der Hund rennt über den Platz.',
        )
        anchor = SceneAnchor.objects.create(
            source=source, text_slug='story', fragment_index=0,
            scene_description='A dog runs across the square.',
            mood='neutral', is_generated=True,
            image_file='literary_scenes/test.jpg',
        )
        LiteraryFragment.objects.create(
            anchor=anchor, text=text_ru,
            content='Sobaka bezhit po ploshchadi.',
            key_words=['sobaka', 'ploshchad'],
        )
        LiteraryFragment.objects.create(
            anchor=anchor, text=text_de,
            content='Der Hund rennt über den Platz.',
            key_words=['Hund', 'Platz'],
        )

        word_ru = Word.objects.create(
            user=test_user, original_word='sobaka',
            translation='dog', language='ru',
        )
        word_de = Word.objects.create(
            user=test_user, original_word='Hund',
            translation='dog', language='de',
        )

        settings = LiteraryContextSettings.get()
        settings.llm_match_enabled = False
        settings.save()

        ctx_ru = generate_word_context(word_ru, source, skip_hint=True)
        ctx_de = generate_word_context(word_de, source, skip_hint=True)

        # Both contexts point to the same anchor -> same image
        assert ctx_ru.anchor.id == ctx_de.anchor.id
        assert ctx_ru.anchor.image_file == ctx_de.anchor.image_file
