"""Tests for async deck context generation endpoints."""
import uuid
from unittest.mock import patch, MagicMock

import pytest
from rest_framework.test import APIClient

from apps.literary_context.models import DeckContextJob


@pytest.fixture
def api_client(test_user):
    client = APIClient()
    client.force_authenticate(user=test_user)
    return client


class TestGenerateDeckContextAsync:
    @patch('apps.literary_context.views.threading.Thread')
    def test_creates_job_and_returns_id(
        self, mock_thread_cls, api_client, deck_with_words, chekhov_source
    ):
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        deck, words = deck_with_words
        response = api_client.post(
            '/api/literary-context/generate-deck-context-async/',
            {'deck_id': deck.id, 'source_slug': 'chekhov'},
            format='json',
        )

        assert response.status_code == 202
        assert 'job_id' in response.data
        job = DeckContextJob.objects.get(id=response.data['job_id'])
        assert job.status == 'pending'
        assert job.deck_id == deck.id
        mock_thread.start.assert_called_once()

    def test_missing_params(self, api_client):
        response = api_client.post(
            '/api/literary-context/generate-deck-context-async/',
            {},
            format='json',
        )
        assert response.status_code == 400

    def test_invalid_source_slug(self, api_client, deck_with_words):
        deck, _ = deck_with_words
        response = api_client.post(
            '/api/literary-context/generate-deck-context-async/',
            {'deck_id': deck.id, 'source_slug': 'nonexistent'},
            format='json',
        )
        assert response.status_code == 404

    @patch('apps.literary_context.views.threading.Thread')
    def test_returns_existing_running_job(
        self, mock_thread_cls, api_client, deck_with_words, chekhov_source
    ):
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        deck, _ = deck_with_words

        # First call creates job
        response1 = api_client.post(
            '/api/literary-context/generate-deck-context-async/',
            {'deck_id': deck.id, 'source_slug': 'chekhov'},
            format='json',
        )
        job_id = response1.data['job_id']

        # Second call returns same job
        response2 = api_client.post(
            '/api/literary-context/generate-deck-context-async/',
            {'deck_id': deck.id, 'source_slug': 'chekhov'},
            format='json',
        )
        assert response2.data['job_id'] == job_id


class TestJobStatusView:
    def test_pending_status(self, api_client, deck_with_words, chekhov_source):
        deck, _ = deck_with_words
        job = DeckContextJob.objects.create(
            deck=deck, source=chekhov_source, user=deck.user,
        )

        response = api_client.get(f'/api/literary-context/job/{job.id}/status/')
        assert response.status_code == 200
        assert response.data['status'] == 'pending'
        assert response.data['progress'] == 0

    def test_completed_status(self, api_client, deck_with_words, chekhov_source):
        deck, _ = deck_with_words
        stats = {'total': 3, 'generated': 2, 'skipped': 1, 'errors': 0}
        job = DeckContextJob.objects.create(
            deck=deck, source=chekhov_source, user=deck.user,
            status='completed', progress=100, stats=stats,
        )

        response = api_client.get(f'/api/literary-context/job/{job.id}/status/')
        assert response.status_code == 200
        assert response.data['status'] == 'completed'
        assert response.data['stats']['generated'] == 2

    def test_nonexistent_job_404(self, api_client):
        fake_id = uuid.uuid4()
        response = api_client.get(f'/api/literary-context/job/{fake_id}/status/')
        assert response.status_code == 404

    def test_other_user_job_denied(self, db, deck_with_words, chekhov_source):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        deck, _ = deck_with_words
        job = DeckContextJob.objects.create(
            deck=deck, source=chekhov_source, user=deck.user,
        )

        # Authenticate as different user
        other_user = User.objects.create_user(username='other', password='pass123')
        client = APIClient()
        client.force_authenticate(user=other_user)

        response = client.get(f'/api/literary-context/job/{job.id}/status/')
        assert response.status_code == 404
