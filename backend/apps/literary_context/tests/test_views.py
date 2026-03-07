from unittest.mock import patch, MagicMock

import pytest
from django.test import TestCase
from rest_framework.test import APIClient

from apps.literary_context.models import LiterarySource, WordContextMedia


@pytest.fixture
def api_client(test_user):
    client = APIClient()
    client.force_authenticate(user=test_user)
    return client


class TestSourcesListView:
    def test_list_active_sources(self, api_client, chekhov_source, bible_source):
        response = api_client.get('/api/literary-context/sources/')
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_inactive_source_excluded(self, api_client, chekhov_source):
        chekhov_source.is_active = False
        chekhov_source.save()

        response = api_client.get('/api/literary-context/sources/')
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_unauthenticated(self, db):
        client = APIClient()
        response = client.get('/api/literary-context/sources/')
        assert response.status_code == 401


class TestGenerateContextView:
    @patch('apps.literary_context.generation.get_openai_client')
    def test_generate_context(
        self, mock_client_fn, api_client, chekhov_source, fragment_de,
        word_marktplatz, settings_obj
    ):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'A hint'
        mock_client.chat.completions.create.return_value = mock_response

        response = api_client.post('/api/literary-context/generate/', {
            'word_id': word_marktplatz.id,
            'source_slug': 'chekhov',
        }, format='json')

        assert response.status_code == 201
        assert response.data['match_method'] == 'keyword'
        assert not response.data['is_fallback']

    def test_missing_params(self, api_client):
        response = api_client.post('/api/literary-context/generate/', {}, format='json')
        assert response.status_code == 400

    def test_wrong_user_word(self, api_client, chekhov_source, db):
        from django.contrib.auth import get_user_model
        from apps.words.models import Word
        User = get_user_model()
        other_user = User.objects.create_user(username='other', password='pass123')
        other_word = Word.objects.create(
            user=other_user, original_word='Hund', translation='dog', language='de'
        )
        response = api_client.post('/api/literary-context/generate/', {
            'word_id': other_word.id,
            'source_slug': 'chekhov',
        }, format='json')
        assert response.status_code == 404


class TestGenerateBatchContextView:
    def test_batch_generate(
        self, api_client, chekhov_source, fragment_de,
        word_marktplatz, word_hund, settings_obj
    ):
        settings_obj.llm_match_enabled = False
        settings_obj.save()

        response = api_client.post('/api/literary-context/generate-batch/', {
            'word_ids': [word_marktplatz.id, word_hund.id],
            'source_slug': 'chekhov',
        }, format='json')

        assert response.status_code == 200
        assert response.data['total'] == 2
        assert response.data['generated'] == 2

    def test_missing_params(self, api_client):
        response = api_client.post('/api/literary-context/generate-batch/', {}, format='json')
        assert response.status_code == 400


class TestWordContextMediaView:
    def test_get_media(
        self, api_client, chekhov_source, fragment_de, scene_anchor,
        word_marktplatz, settings_obj
    ):
        WordContextMedia.objects.create(
            word=word_marktplatz, source=chekhov_source,
            anchor=scene_anchor, fragment=fragment_de,
            hint_text='A hint', match_method='keyword', match_score=1.0,
        )

        response = api_client.get(
            f'/api/literary-context/word/{word_marktplatz.id}/media/'
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['hint_text'] == 'A hint'

    def test_no_media(self, api_client, word_hund):
        response = api_client.get(f'/api/literary-context/word/{word_hund.id}/media/')
        assert response.status_code == 200
        assert len(response.data) == 0
