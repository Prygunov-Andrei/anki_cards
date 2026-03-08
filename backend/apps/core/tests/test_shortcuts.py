"""Tests for core shortcuts."""
import pytest
from django.http import Http404

from apps.words.models import Word
from apps.core.shortcuts import get_user_object_or_404


@pytest.mark.django_db
class TestGetUserObjectOr404:
    def test_returns_object(self, user, word):
        result = get_user_object_or_404(Word, user, id=word.id)
        assert result == word

    def test_raises_404_for_wrong_user(self, user, user2, word):
        with pytest.raises(Http404):
            get_user_object_or_404(Word, user2, id=word.id)

    def test_raises_404_for_nonexistent(self, user):
        with pytest.raises(Http404):
            get_user_object_or_404(Word, user, id=99999)
