"""Tests for ai_service.py — etymology, hints, sentences, synonyms."""
import pytest
from unittest.mock import patch, MagicMock

from apps.words.models import Word
from apps.cards.token_utils import add_tokens, check_balance
from apps.training.services.ai_service import (
    generate_etymology_for_word,
    generate_hint_for_word,
    generate_sentences_for_word,
    generate_synonym_for_word,
)


@pytest.mark.django_db
class TestGenerateEtymology:
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generates_etymology(self, mock_client, user):
        add_tokens(user, 10)
        word = Word.objects.create(
            user=user, original_word='Hund', translation='собака', language='de')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'Hund comes from Old High German hund.'
        mock_client.return_value.chat.completions.create.return_value = mock_response

        result = generate_etymology_for_word(user, word.id)
        assert result['word_id'] == word.id
        assert 'etymology' in result
        assert result['tokens_spent'] == 1

    def test_existing_etymology_raises(self, user):
        word = Word.objects.create(
            user=user, original_word='Hund', translation='собака',
            language='de', etymology='existing')

        with pytest.raises(ValueError, match='уже существует'):
            generate_etymology_for_word(user, word.id)

    @patch('apps.training.ai_generation.get_openai_client')
    def test_force_regenerate(self, mock_client, user):
        add_tokens(user, 10)
        word = Word.objects.create(
            user=user, original_word='Hund', translation='собака',
            language='de', etymology='old')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'New etymology for Hund.'
        mock_client.return_value.chat.completions.create.return_value = mock_response

        result = generate_etymology_for_word(user, word.id, force_regenerate=True)
        assert result['etymology'] != 'old'

    def test_nonexistent_word_raises(self, user):
        with pytest.raises(Word.DoesNotExist):
            generate_etymology_for_word(user, 99999)


@pytest.mark.django_db
class TestGenerateHint:
    def test_returns_existing_hint(self, user):
        word = Word.objects.create(
            user=user, original_word='Hund', translation='собака',
            language='de', hint_text='existing hint')

        result = generate_hint_for_word(user, word.id)
        assert result['hint_text'] == 'existing hint'
        assert result['tokens_spent'] == 0

    @patch('apps.training.ai_generation.get_openai_client')
    def test_generates_hint(self, mock_client, user):
        add_tokens(user, 10)
        word = Word.objects.create(
            user=user, original_word='Hund', translation='собака', language='de')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'A loyal companion with four legs.'
        mock_client.return_value.chat.completions.create.return_value = mock_response

        # Mock audio generation
        mock_audio = MagicMock()
        mock_audio.content = b'fake audio'
        mock_client.return_value.audio.speech.create.return_value = mock_audio

        result = generate_hint_for_word(user, word.id, generate_audio=False)
        assert result['word_id'] == word.id
        assert result['hint_text'] is not None
        assert result['tokens_spent'] == 1


@pytest.mark.django_db
class TestGenerateSentences:
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generates_sentence(self, mock_client, user):
        add_tokens(user, 10)
        word = Word.objects.create(
            user=user, original_word='Hund', translation='собака', language='de')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'Der Hund ist groß.'
        mock_client.return_value.chat.completions.create.return_value = mock_response

        result = generate_sentences_for_word(user, word.id, count=1)
        assert result['word_id'] == word.id
        assert len(result['sentences']) >= 1
        assert result['tokens_spent'] == 1

    def test_nonexistent_word_raises(self, user):
        with pytest.raises(Word.DoesNotExist):
            generate_sentences_for_word(user, 99999)


@pytest.mark.django_db
class TestGenerateSynonym:
    @patch('apps.training.ai_generation.generate_etymology', return_value='etymology text')
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generates_synonym(self, mock_client, mock_etymology, user):
        add_tokens(user, 10)
        w = Word(
            user=user, original_word='Hund', translation='собака', language='de')
        w._skip_etymology_generation = True
        w.save()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'Köter|дворняга'
        mock_client.return_value.chat.completions.create.return_value = mock_response

        result = generate_synonym_for_word(user, w.id)
        assert result['original_word_id'] == w.id
        assert result['relation_created'] is True
        assert result['tokens_spent'] == 2

    def test_nonexistent_word_raises(self, user):
        with pytest.raises(Word.DoesNotExist):
            generate_synonym_for_word(user, 99999)
