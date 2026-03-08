"""Tests for deck_service.py — deck operations, merge, invert, empty cards."""
import pytest

from apps.words.models import Word
from apps.cards.models import Deck, Card
from apps.cards.services.deck_service import (
    add_words_to_deck,
    update_word_in_deck,
    merge_decks,
    invert_all_words,
    invert_single_word,
    create_empty_cards_for_deck,
    create_empty_card_for_word,
)


@pytest.mark.django_db
class TestAddWordsToDeck:
    def test_add_existing_word(self, user, deck, word):
        added, errors = add_words_to_deck(user, deck, [{'word_id': word.id}])
        assert word.id in added
        assert not errors
        assert word in deck.words.all()

    def test_add_new_word(self, user, deck):
        added, errors = add_words_to_deck(user, deck, [{
            'original_word': 'Katze',
            'translation': 'cat',
            'language': 'de',
        }])
        assert len(added) == 1
        assert not errors

    def test_add_nonexistent_word_id(self, user, deck):
        added, errors = add_words_to_deck(user, deck, [{'word_id': 99999}])
        assert not added
        assert len(errors) == 1

    def test_add_duplicate_word(self, user, deck, word):
        deck.words.add(word)
        added, errors = add_words_to_deck(user, deck, [{'word_id': word.id}])
        assert not added  # Already in deck
        assert not errors


@pytest.mark.django_db
class TestUpdateWordInDeck:
    def test_update_translation(self, user, deck, word):
        deck.words.add(word)
        result = update_word_in_deck(user, deck, word.id, {'translation': 'new translation'})
        assert result['translation'] == 'new translation'
        assert 'translation' in result['updated_fields']

    def test_update_original_word(self, user, deck, word):
        deck.words.add(word)
        result = update_word_in_deck(user, deck, word.id, {'original_word': 'Katze'})
        assert result['original_word'] == 'Katze'

    def test_update_nonexistent_word(self, user, deck):
        with pytest.raises(Word.DoesNotExist):
            update_word_in_deck(user, deck, 99999, {'translation': 'test'})

    def test_empty_update(self, user, deck, word):
        deck.words.add(word)
        with pytest.raises(ValueError):
            update_word_in_deck(user, deck, word.id, {})

    def test_duplicate_word_rejected(self, user, deck, word):
        deck.words.add(word)
        Word.objects.create(user=user, original_word='Katze', translation='cat', language='de')
        with pytest.raises(ValueError):
            update_word_in_deck(user, deck, word.id, {'original_word': 'Katze'})


@pytest.mark.django_db
class TestMergeDecks:
    def test_merge_two_decks(self, user):
        deck1 = Deck.objects.create(user=user, name='D1', target_lang='de', source_lang='ru')
        deck2 = Deck.objects.create(user=user, name='D2', target_lang='de', source_lang='ru')
        w1 = Word.objects.create(user=user, original_word='Hund', translation='dog', language='de')
        w2 = Word.objects.create(user=user, original_word='Katze', translation='cat', language='de')
        deck1.words.add(w1)
        deck2.words.add(w2)

        result = merge_decks(user, [deck1.id, deck2.id], new_deck_name='Merged')
        assert result['words_count'] == 2
        assert result['source_decks_count'] == 2

    def test_merge_with_delete(self, user):
        deck1 = Deck.objects.create(user=user, name='D1', target_lang='de', source_lang='ru')
        deck2 = Deck.objects.create(user=user, name='D2', target_lang='de', source_lang='ru')
        w1 = Word.objects.create(user=user, original_word='Hund', translation='dog', language='de')
        deck1.words.add(w1)
        deck2.words.add(w1)

        result = merge_decks(user, [deck1.id, deck2.id],
                             new_deck_name='Merged', delete_source_decks=True)
        assert len(result['deleted_decks']) == 2
        assert not Deck.objects.filter(id=deck1.id).exists()
        assert not Deck.objects.filter(id=deck2.id).exists()

    def test_merge_empty_decks_raises(self, user):
        deck1 = Deck.objects.create(user=user, name='D1', target_lang='de', source_lang='ru')
        deck2 = Deck.objects.create(user=user, name='D2', target_lang='de', source_lang='ru')

        with pytest.raises(ValueError, match='empty'):
            merge_decks(user, [deck1.id, deck2.id])

    def test_merge_nonexistent_deck_raises(self, user):
        deck1 = Deck.objects.create(user=user, name='D1', target_lang='de', source_lang='ru')
        with pytest.raises(ValueError, match='not found'):
            merge_decks(user, [deck1.id, 99999])


@pytest.mark.django_db
class TestInvertAllWords:
    def test_invert_creates_cards(self, user, deck_with_words):
        deck, words = deck_with_words
        result = invert_all_words(user, deck.id)
        assert result['inverted_cards_count'] == 3
        assert Card.objects.filter(user=user, card_type='inverted').count() == 3

    def test_invert_skips_existing(self, user, deck_with_words):
        deck, words = deck_with_words
        Card.create_inverted(words[0])

        result = invert_all_words(user, deck.id)
        assert result['inverted_cards_count'] == 2
        assert len(result['skipped_words']) == 1

    def test_invert_empty_deck_raises(self, user, deck):
        with pytest.raises(ValueError, match='empty'):
            invert_all_words(user, deck.id)


@pytest.mark.django_db
class TestInvertSingleWord:
    def test_invert_single(self, user, deck_with_words):
        deck, words = deck_with_words
        result = invert_single_word(user, deck.id, words[0].id)
        assert result['inverted_card']['card_type'] == 'inverted'
        assert Card.objects.filter(word=words[0], card_type='inverted').exists()

    def test_invert_already_exists_raises(self, user, deck_with_words):
        deck, words = deck_with_words
        Card.create_inverted(words[0])

        with pytest.raises(ValueError, match='already exists'):
            invert_single_word(user, deck.id, words[0].id)

    def test_invert_nonexistent_word_raises(self, user, deck):
        with pytest.raises(Word.DoesNotExist):
            invert_single_word(user, deck.id, 99999)


@pytest.mark.django_db
class TestCreateEmptyCards:
    def test_create_empty_for_deck(self, user, deck_with_words):
        deck, words = deck_with_words
        result = create_empty_cards_for_deck(user, deck.id)
        assert result['empty_cards_count'] == 3

    def test_create_empty_skips_inverted(self, user, deck_with_words):
        deck, words = deck_with_words
        words[0].card_type = 'inverted'
        words[0].save()

        result = create_empty_cards_for_deck(user, deck.id)
        assert result['empty_cards_count'] == 2
        assert len(result['skipped_cards']) == 1

    def test_create_empty_for_single_word(self, user, deck_with_words):
        deck, words = deck_with_words
        result = create_empty_card_for_word(user, deck.id, words[0].id)
        assert result['empty_card']['created'] is True

    def test_create_empty_for_inverted_raises(self, user, deck_with_words):
        deck, words = deck_with_words
        words[0].card_type = 'inverted'
        words[0].save()

        with pytest.raises(ValueError, match='inverted'):
            create_empty_card_for_word(user, deck.id, words[0].id)
