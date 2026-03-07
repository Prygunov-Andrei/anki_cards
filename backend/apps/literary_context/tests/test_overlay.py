"""Tests for literary context overlay in WordSerializer and user context switching."""
import pytest
from rest_framework.test import APIClient

from apps.literary_context.models import WordContextMedia


@pytest.fixture
def api_client(test_user):
    client = APIClient()
    client.force_authenticate(user=test_user)
    return client


class TestWordSerializerOverlay:
    def test_no_context_no_overlay(self, api_client, word_marktplatz):
        response = api_client.get(f'/api/words/{word_marktplatz.id}/')
        assert response.status_code == 200
        assert response.data['literary_context'] is None

    def test_with_context_and_media(
        self, api_client, test_user, chekhov_source, scene_anchor,
        fragment_de, word_marktplatz
    ):
        # Set active source
        test_user.active_literary_source = chekhov_source
        test_user.save()

        # Create context media
        WordContextMedia.objects.create(
            word=word_marktplatz, source=chekhov_source,
            anchor=scene_anchor, fragment=fragment_de,
            hint_text='Auf dem Platz...', match_method='keyword',
            match_score=1.0, is_fallback=False,
            sentences=[{'text': 'Auf dem Marktplatz.', 'source': 'chekhov'}],
        )

        response = api_client.get(f'/api/words/{word_marktplatz.id}/')
        assert response.status_code == 200

        # Literary context should be present
        ctx = response.data['literary_context']
        assert ctx is not None
        assert ctx['source_slug'] == 'chekhov'
        assert ctx['match_method'] == 'keyword'

        # Fields should be overlaid
        assert response.data['hint_text'] == 'Auf dem Platz...'
        assert response.data['sentences'] == [{'text': 'Auf dem Marktplatz.', 'source': 'chekhov'}]

    def test_fallback_no_overlay(
        self, api_client, test_user, chekhov_source, word_hund
    ):
        test_user.active_literary_source = chekhov_source
        test_user.save()

        WordContextMedia.objects.create(
            word=word_hund, source=chekhov_source,
            is_fallback=True, match_method='none', match_score=0,
        )

        response = api_client.get(f'/api/words/{word_hund.id}/')
        assert response.status_code == 200
        # Fallback -> no overlay
        assert response.data['literary_context'] is None

    def test_no_media_no_overlay(
        self, api_client, test_user, chekhov_source, word_hund
    ):
        test_user.active_literary_source = chekhov_source
        test_user.save()

        response = api_client.get(f'/api/words/{word_hund.id}/')
        assert response.status_code == 200
        assert response.data['literary_context'] is None


class TestContextSwitching:
    def test_switch_to_source(self, api_client, test_user, chekhov_source):
        response = api_client.patch('/api/auth/profile/', {
            'active_literary_source': 'chekhov'
        }, format='json')
        assert response.status_code == 200
        assert response.data['active_literary_source'] == 'chekhov'

        test_user.refresh_from_db()
        assert test_user.active_literary_source == chekhov_source

    def test_switch_to_null(self, api_client, test_user, chekhov_source):
        test_user.active_literary_source = chekhov_source
        test_user.save()

        response = api_client.patch('/api/auth/profile/', {
            'active_literary_source': None
        }, format='json')
        assert response.status_code == 200
        assert response.data['active_literary_source'] is None

        test_user.refresh_from_db()
        assert test_user.active_literary_source is None

    def test_switch_to_invalid_source(self, api_client, test_user):
        response = api_client.patch('/api/auth/profile/', {
            'active_literary_source': 'nonexistent'
        }, format='json')
        assert response.status_code == 400

    def test_get_profile_shows_source(self, api_client, test_user, chekhov_source):
        test_user.active_literary_source = chekhov_source
        test_user.save()

        response = api_client.get('/api/auth/profile/')
        assert response.status_code == 200
        assert response.data['active_literary_source'] == 'chekhov'
