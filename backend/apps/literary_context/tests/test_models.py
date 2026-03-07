import pytest
from django.db import IntegrityError
from django.core.cache import cache

from apps.literary_context.models import (
    LiterarySource, LiteraryText, SceneAnchor, LiteraryFragment,
    WordContextMedia, LiteraryContextSettings,
    SETTINGS_CACHE_KEY,
)


class TestLiterarySource:
    def test_create(self, chekhov_source):
        assert chekhov_source.slug == 'chekhov'
        assert chekhov_source.is_active is True
        assert chekhov_source.available_languages == ['ru', 'de', 'en']

    def test_str(self, chekhov_source):
        assert str(chekhov_source) == 'Chekhov Stories'

    def test_slug_unique(self, chekhov_source):
        with pytest.raises(IntegrityError):
            LiterarySource.objects.create(
                slug='chekhov', name='Duplicate', source_language='ru'
            )

    def test_ordering(self, chekhov_source, bible_source):
        sources = list(LiterarySource.objects.values_list('slug', flat=True))
        assert sources == ['bible', 'chekhov']  # alphabetical by name


class TestLiteraryText:
    def test_create(self, hameleon_text_ru):
        assert hameleon_text_ru.slug == 'hameleon'
        assert hameleon_text_ru.language == 'ru'

    def test_str(self, hameleon_text_ru):
        assert '(ru)' in str(hameleon_text_ru)

    def test_unique_together(self, hameleon_text_ru):
        with pytest.raises(IntegrityError):
            LiteraryText.objects.create(
                source=hameleon_text_ru.source,
                slug='hameleon',
                title='Duplicate',
                language='ru',
                full_text='test',
            )

    def test_same_slug_different_language(self, hameleon_text_ru, hameleon_text_de):
        assert hameleon_text_ru.slug == hameleon_text_de.slug
        assert hameleon_text_ru.language != hameleon_text_de.language

    def test_metadata_default(self, hameleon_text_ru):
        assert hameleon_text_ru.metadata == {}


class TestSceneAnchor:
    def test_create(self, scene_anchor):
        assert scene_anchor.text_slug == 'hameleon'
        assert scene_anchor.fragment_index == 0
        assert scene_anchor.mood == 'comedic'
        assert scene_anchor.is_generated is False

    def test_str(self, scene_anchor):
        assert 'chekhov/hameleon #0' in str(scene_anchor)

    def test_unique_together(self, scene_anchor):
        with pytest.raises(IntegrityError):
            SceneAnchor.objects.create(
                source=scene_anchor.source,
                text_slug='hameleon',
                fragment_index=0,
                scene_description='Duplicate',
            )

    def test_different_fragment_index(self, chekhov_source):
        a1 = SceneAnchor.objects.create(
            source=chekhov_source, text_slug='hameleon',
            fragment_index=0, scene_description='Scene 1',
        )
        a2 = SceneAnchor.objects.create(
            source=chekhov_source, text_slug='hameleon',
            fragment_index=1, scene_description='Scene 2',
        )
        assert a1.pk != a2.pk

    def test_characters_json(self, scene_anchor):
        assert scene_anchor.characters == ['Ochumelov']

    def test_image_file_nullable(self, scene_anchor):
        assert not scene_anchor.image_file


class TestLiteraryFragment:
    def test_create(self, fragment_ru):
        assert len(fragment_ru.content) > 0
        assert 'ploshchad' in fragment_ru.key_words

    def test_str(self, fragment_ru):
        s = str(fragment_ru)
        assert '(ru)' in s

    def test_unique_together(self, fragment_ru):
        with pytest.raises(IntegrityError):
            LiteraryFragment.objects.create(
                anchor=fragment_ru.anchor,
                text=fragment_ru.text,
                content='Duplicate',
                key_words=[],
            )

    def test_same_anchor_different_languages(self, fragment_ru, fragment_de):
        assert fragment_ru.anchor == fragment_de.anchor
        assert fragment_ru.text.language == 'ru'
        assert fragment_de.text.language == 'de'

    def test_key_words_default(self, db, scene_anchor, hameleon_text_ru):
        frag = LiteraryFragment.objects.create(
            anchor=scene_anchor, text=hameleon_text_ru,
            content='Test',
        )
        assert frag.key_words == []


class TestWordContextMedia:
    @pytest.fixture
    def user(self, db):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username='testuser', password='testpass123'
        )

    @pytest.fixture
    def word(self, db, user):
        from apps.words.models import Word
        return Word.objects.create(
            user=user,
            original_word='Hund',
            translation='dog',
            language='de',
        )

    def test_create(self, word, chekhov_source, scene_anchor, fragment_de):
        wcm = WordContextMedia.objects.create(
            word=word,
            source=chekhov_source,
            anchor=scene_anchor,
            fragment=fragment_de,
            hint_text='The animal in the scene',
            sentences=[{'text': 'Der Hund lief.', 'source': 'chekhov'}],
            match_method='keyword',
            match_score=1.0,
        )
        assert wcm.is_fallback is False
        assert wcm.match_method == 'keyword'

    def test_str(self, word, chekhov_source):
        wcm = WordContextMedia.objects.create(
            word=word, source=chekhov_source,
            is_fallback=True, match_method='fallback',
        )
        assert 'fallback' in str(wcm)

    def test_unique_together(self, word, chekhov_source):
        WordContextMedia.objects.create(
            word=word, source=chekhov_source, is_fallback=True,
        )
        with pytest.raises(IntegrityError):
            WordContextMedia.objects.create(
                word=word, source=chekhov_source, is_fallback=True,
            )

    def test_nullable_anchor_and_fragment(self, word, chekhov_source):
        wcm = WordContextMedia.objects.create(
            word=word, source=chekhov_source,
            is_fallback=True,
        )
        assert wcm.anchor is None
        assert wcm.fragment is None

    def test_different_sources_same_word(self, word, chekhov_source, bible_source):
        wcm1 = WordContextMedia.objects.create(
            word=word, source=chekhov_source, is_fallback=True,
        )
        wcm2 = WordContextMedia.objects.create(
            word=word, source=bible_source, is_fallback=True,
        )
        assert wcm1.pk != wcm2.pk


class TestLiteraryContextSettings:
    def test_singleton_get(self, db):
        s = LiteraryContextSettings.get()
        assert s.pk == 1

    def test_singleton_always_same(self, db):
        s1 = LiteraryContextSettings.get()
        s2 = LiteraryContextSettings.get()
        assert s1.pk == s2.pk

    def test_defaults(self, db):
        LiteraryContextSettings.objects.all().delete()
        cache.delete(SETTINGS_CACHE_KEY)
        fresh = LiteraryContextSettings.get()
        assert fresh.semantic_match_min_score == 0.7
        assert fresh.llm_match_enabled is True
        assert fresh.hint_generation_model == 'gpt-4o-mini'
        assert fresh.matching_model == 'gpt-4o'
        assert fresh.default_fragment_size == 500

    def test_save_forces_pk_1(self, db):
        s = LiteraryContextSettings()
        s.pk = 999
        s.save()
        assert s.pk == 1
        assert LiteraryContextSettings.objects.count() == 1

    def test_cache_invalidation(self, settings_obj):
        cache.set(SETTINGS_CACHE_KEY, 'stale')
        settings_obj.semantic_match_min_score = 0.5
        settings_obj.save()
        assert cache.get(SETTINGS_CACHE_KEY) is None

    def test_cache_populated_on_get(self, db):
        cache.delete(SETTINGS_CACHE_KEY)
        s = LiteraryContextSettings.get()
        cached = cache.get(SETTINGS_CACHE_KEY)
        assert cached is not None
        assert cached.pk == s.pk

    def test_update_fields(self, settings_obj):
        settings_obj.hint_temperature = 0.5
        settings_obj.matching_model = 'gpt-5'
        settings_obj.save()
        refreshed = LiteraryContextSettings.get()
        assert refreshed.hint_temperature == 0.5
        assert refreshed.matching_model == 'gpt-5'


class TestCrossLanguageSceneSharing:
    """Test the key architectural feature: one SceneAnchor, multiple languages."""

    def test_one_anchor_multiple_fragments(
        self, scene_anchor, fragment_ru, fragment_de
    ):
        assert scene_anchor.fragments.count() == 2
        languages = set(
            scene_anchor.fragments.values_list('text__language', flat=True)
        )
        assert languages == {'ru', 'de'}

    def test_anchor_image_shared(
        self, scene_anchor, fragment_ru, fragment_de
    ):
        # Both fragments point to the same anchor (= same image)
        assert fragment_ru.anchor_id == fragment_de.anchor_id
        assert fragment_ru.anchor.image_file == fragment_de.anchor.image_file

    def test_different_keywords_per_language(self, fragment_ru, fragment_de):
        assert 'ploshchad' in fragment_ru.key_words
        assert 'Marktplatz' in fragment_de.key_words
        # Keywords are language-specific
        assert fragment_ru.key_words != fragment_de.key_words
