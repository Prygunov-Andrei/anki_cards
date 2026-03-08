"""Tests for generation_service.py — card generation, auto-enrichment."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.conf import settings

from apps.words.models import Word
from apps.cards.models import Deck, GeneratedDeck
from apps.cards.services.generation_service import (
    generate_cards,
    auto_enrich_simple_mode,
    generate_apkg_from_deck,
    _find_translation,
)


class TestFindTranslation:
    def test_exact_match(self):
        assert _find_translation('Hund', {'Hund': 'dog'}) == 'dog'

    def test_normalized_match(self):
        assert _find_translation('Hund.', {'Hund': 'dog'}) == 'dog'

    def test_no_match(self):
        assert _find_translation('Katze', {'Hund': 'dog'}) == ''


@pytest.mark.django_db
class TestGenerateCards:
    @patch('apps.cards.services.generation_service.generate_apkg')
    def test_creates_words_and_deck(self, mock_apkg, user):
        mock_apkg.return_value = None  # generate_apkg writes to file

        result = generate_cards(
            user=user,
            words_list=['Hund', 'Katze'],
            language='de',
            translations={'Hund': 'dog', 'Katze': 'cat'},
            audio_files={},
            image_files={},
            deck_name='Test deck',
            save_to_decks=True,
        )

        assert 'file_id' in result
        assert 'deck_id' in result
        assert result['deck_name'] == 'Test deck'
        assert result['cards_count'] == 4  # 2 words * 2 (two-sided)

        # Words created
        assert Word.objects.filter(user=user, original_word='Hund').exists()
        assert Word.objects.filter(user=user, original_word='Katze').exists()

        # Deck created
        deck = Deck.objects.get(id=result['deck_id'])
        assert deck.words.count() == 2

    @patch('apps.cards.services.generation_service.generate_apkg')
    def test_no_deck_when_save_disabled(self, mock_apkg, user):
        mock_apkg.return_value = None

        result = generate_cards(
            user=user,
            words_list=['Hund'],
            language='de',
            translations={'Hund': 'dog'},
            audio_files={},
            image_files={},
            deck_name='Test',
            save_to_decks=False,
        )

        assert 'deck_id' not in result

    @patch('apps.cards.services.generation_service.generate_apkg')
    def test_updates_existing_word_translation(self, mock_apkg, user):
        Word.objects.create(
            user=user, original_word='Hund', translation='old', language='de')
        mock_apkg.return_value = None

        generate_cards(
            user=user,
            words_list=['Hund'],
            language='de',
            translations={'Hund': 'new'},
            audio_files={},
            image_files={},
            deck_name='Test',
        )

        word = Word.objects.get(user=user, original_word='Hund')
        assert word.translation == 'new'


@pytest.mark.django_db
class TestAutoEnrichSimpleMode:
    @patch('apps.cards.services.generation_service.select_image_style')
    @patch('apps.cards.services.generation_service.detect_category')
    @patch('apps.cards.services.generation_service.generate_deck_name')
    @patch('apps.cards.services.generation_service.translate_words')
    def test_enriches_data(self, mock_translate, mock_name, mock_category, mock_style, user):
        user.learning_language = 'de'
        user.native_language = 'ru'
        user.save()

        mock_translate.return_value = {'Hund': 'dog', 'Katze': 'cat'}
        mock_name.return_value = 'Auto name'
        mock_category.return_value = 'Animals'
        mock_style.return_value = 'realistic'

        translations, deck_name, style = auto_enrich_simple_mode(
            user, ['Hund', 'Katze'], 'de', {}, 'Новая колода')

        assert translations == {'Hund': 'dog', 'Katze': 'cat'}
        assert deck_name == 'Auto name'
        assert style == 'realistic'

    @patch('apps.cards.services.generation_service.select_image_style')
    @patch('apps.cards.services.generation_service.detect_category')
    @patch('apps.cards.services.generation_service.translate_words')
    def test_keeps_existing_translations(self, mock_translate, mock_category, mock_style, user):
        user.learning_language = 'de'
        user.native_language = 'ru'
        user.save()

        mock_translate.return_value = {'Hund': 'auto-dog'}
        mock_category.return_value = 'Animals'
        mock_style.return_value = 'balanced'

        translations, _, _ = auto_enrich_simple_mode(
            user, ['Hund'], 'de', {'Hund': 'manual-dog'}, 'Custom name')

        # Manual translation should take precedence
        assert translations['Hund'] == 'manual-dog'


@pytest.mark.django_db
class TestGenerateApkgFromDeck:
    @patch('apps.cards.services.generation_service.generate_apkg')
    def test_generates_from_deck(self, mock_apkg, user, deck_with_words):
        deck, words = deck_with_words
        mock_apkg.return_value = None

        result = generate_apkg_from_deck(user, deck.id)
        assert 'file_id' in result
        assert GeneratedDeck.objects.filter(user=user).exists()

    def test_empty_deck_raises(self, user, deck):
        with pytest.raises(ValueError, match='empty'):
            generate_apkg_from_deck(user, deck.id)
