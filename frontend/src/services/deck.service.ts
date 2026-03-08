import api from './api';
import { Deck } from '../types';
import { API_ENDPOINTS } from '../lib/api-constants';
import { logger } from '@/utils/logger';
import { TIMEOUTS } from '@/utils/timeouts';
import { updateWordMedia } from './media.service';

/**
 * Deck Service — CRUD for decks, word management, merge/invert operations.
 * Media generation → media.service.ts
 * German word processing → german.service.ts
 */
class DeckService {
  async getDecks(): Promise<Deck[]> {
    const response = await api.get<Deck[]>(API_ENDPOINTS.DECKS);
    return response.data;
  }

  async getDeck(id: number): Promise<Deck> {
    const response = await api.get<Deck>(API_ENDPOINTS.DECK_BY_ID(id));
    return response.data;
  }

  async createDeck(data: {
    name: string;
    target_lang: string;
    source_lang: string;
  }): Promise<Deck> {
    const response = await api.post<Deck>(API_ENDPOINTS.DECKS, data);
    return response.data;
  }

  async updateDeck(
    id: number,
    data: Partial<{ name: string; target_lang: string; source_lang: string }>
  ): Promise<Deck> {
    const response = await api.patch<Deck>(API_ENDPOINTS.DECK_BY_ID(id), data);
    return response.data;
  }

  async deleteDeck(id: number): Promise<void> {
    await api.delete(API_ENDPOINTS.DECK_BY_ID(id));
  }

  async addWordsToDeck(
    id: number,
    words: { word: string; translation: string }[]
  ): Promise<Deck> {
    const deck = await this.getDeck(id);

    const formattedWords = words.map((w) => ({
      original_word: String(w.word),
      translation: String(w.translation),
      language: deck.target_lang || 'en',
    }));

    const response = await api.post<Deck & { errors?: Array<{ error?: string; message?: string } | string> }>(
      API_ENDPOINTS.DECK_ADD_WORDS(id),
      { words: formattedWords }
    );

    if (response.status === 207 && response.data.errors && response.data.errors.length > 0) {
      const errorMessages = response.data.errors.map((err: { error?: string; message?: string } | string) =>
        typeof err === 'string' ? err : err.error || err.message || JSON.stringify(err)
      ).join('; ');
      throw new Error(`Backend errors: ${errorMessages}`);
    }

    return response.data;
  }

  async removeWordFromDeck(deckId: number, wordId: number): Promise<Deck> {
    const response = await api.post<Deck>(
      API_ENDPOINTS.DECK_REMOVE_WORD(deckId),
      { word_id: wordId }
    );
    return response.data;
  }

  async generateDeckApkg(id: number): Promise<{ file_id: string }> {
    const response = await api.post<{ file_id: string }>(API_ENDPOINTS.DECK_GENERATE(id));
    return response.data;
  }

  async downloadDeck(fileId: string): Promise<Blob> {
    const response = await api.get<Blob>(API_ENDPOINTS.DOWNLOAD(fileId), {
      responseType: 'blob',
    });
    return response.data;
  }

  async generateCards(data: {
    words: string[];
    translations: Record<string, string>;
    language: string;
    deck_name: string;
    image_files?: Record<string, string>;
    audio_files?: Record<string, string>;
    save_to_decks?: boolean;
  }): Promise<{ file_id: string; deck_id?: number }> {
    logger.log('📤 generateCards:', {
      deck_name: data.deck_name,
      words_count: data.words.length,
      images_count: Object.keys(data.image_files || {}).length,
      audio_count: Object.keys(data.audio_files || {}).length,
    });

    const response = await api.post<{ file_id: string; deck_id?: number }>(
      API_ENDPOINTS.CARDS_GENERATE,
      data,
      { timeout: TIMEOUTS.API_LONG }
    );
    return response.data;
  }

  async analyzeWords(data: {
    words: string[];
    learning_language: string;
    native_language: string;
  }): Promise<Record<string, string>> {
    const response = await api.post<Record<string, string>>(
      API_ENDPOINTS.CARDS_ANALYZE_WORDS,
      data
    );
    return response.data;
  }

  async translateWords(data: {
    words: string[];
    source_language: string;
    target_language: string;
  }): Promise<{ translations: Record<string, string> }> {
    const response = await api.post<{ translations: Record<string, string> }>(
      API_ENDPOINTS.CARDS_TRANSLATE_WORDS,
      {
        words: data.words,
        learning_language: data.source_language,
        native_language: data.target_language,
      }
    );
    return response.data;
  }

  async moveCardToDeck(wordId: number, fromDeckId: number, toDeckId: number): Promise<void> {
    await api.post(
      `${API_ENDPOINTS.DECKS}/${fromDeckId}/words/${wordId}/move/`,
      { target_deck_id: toDeckId }
    );
  }

  async copyAndMoveCard(
    word: { id: number; original_word: string; translation: string; image_file?: string | null; audio_file?: string | null },
    fromDeckId: number,
    toDeckId: number
  ): Promise<void> {
    await this.addWordsToDeck(toDeckId, [
      { word: word.original_word, translation: word.translation }
    ]);

    const updatedDeck = await this.getDeck(toDeckId);
    const newWord = updatedDeck.words?.find(w =>
      w.original_word === word.original_word &&
      w.translation === word.translation &&
      !w.image_file &&
      !w.audio_file
    );

    if (newWord && (word.image_file || word.audio_file)) {
      const mediaUpdate: { image_file?: string; audio_file?: string } = {};
      if (word.image_file) mediaUpdate.image_file = word.image_file;
      if (word.audio_file) mediaUpdate.audio_file = word.audio_file;
      await updateWordMedia(toDeckId, newWord.id, mediaUpdate);
    }

    await this.removeWordFromDeck(fromDeckId, word.id);
  }

  async mergeDecks(params: {
    deck_ids: number[];
    target_deck_id?: number;
    new_deck_name?: string;
    delete_source_decks?: boolean;
  }): Promise<{
    message: string;
    target_deck: Deck;
    words_count: number;
    source_decks_count: number;
    deleted_decks?: Array<{ id: number; name: string }> | null;
  }> {
    const response = await api.post(API_ENDPOINTS.DECK_MERGE, params);
    return response.data;
  }

  async invertAllWords(deckId: number): Promise<{
    message: string;
    deck_id: number;
    deck_name: string;
    inverted_cards_count: number;
    inverted_cards: Array<{
      card_id: number;
      word_id: number;
      original_word: string;
      translation: string;
      card_type: string;
    }>;
    skipped_words?: Array<{ id: number; original_word: string; reason: string }>;
    errors?: Array<{ word_id: number; original_word: string; error: string }>;
  }> {
    const response = await api.post(API_ENDPOINTS.DECK_INVERT_ALL(deckId));
    return response.data;
  }

  async invertWord(deckId: number, wordId: number): Promise<{
    message: string;
    original_word: {
      id: number;
      original_word: string;
      translation: string;
      language: string;
    };
    inverted_card: {
      card_id: number;
      word_id: number;
      card_type: string;
    };
  }> {
    const response = await api.post(API_ENDPOINTS.DECK_INVERT_WORD(deckId), {
      word_id: wordId
    });
    return response.data;
  }

  async createEmptyCards(deckId: number): Promise<{
    message: string;
    deck_id: number;
    deck_name: string;
    empty_cards_count: number;
    empty_cards: Array<{
      id: number;
      original_word: string;
      translation: string;
      language: string;
      created: boolean;
    }>;
    skipped_cards?: Array<{ id: number; translation: string; reason: string }>;
    errors?: Array<{ word_id: number; original_word: string; error: string }>;
  }> {
    const response = await api.post(API_ENDPOINTS.DECK_CREATE_EMPTY_CARDS(deckId));
    return response.data;
  }

  async createEmptyCard(deckId: number, wordId: number): Promise<{
    message: string;
    original_word: {
      id: number;
      original_word: string;
      translation: string;
      language: string;
    };
    empty_card: {
      id: number;
      original_word: string;
      translation: string;
      language: string;
      created: boolean;
      added_to_deck: boolean;
    };
  }> {
    const response = await api.post(API_ENDPOINTS.DECK_CREATE_EMPTY_CARD(deckId), {
      word_id: wordId
    });
    return response.data;
  }

  async setDeckLiterarySource(
    deckId: number,
    sourceSlug: string | null,
    useGlobal: boolean
  ): Promise<{ status: string }> {
    const body = useGlobal
      ? { use_global: true }
      : { source_slug: sourceSlug };
    const response = await api.patch(API_ENDPOINTS.DECK_LITERARY_SOURCE(deckId), body);
    return response.data;
  }
}

export const deckService = new DeckService();
