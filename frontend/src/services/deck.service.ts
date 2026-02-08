import api from './api';
import { Deck } from '../types';
import { API_ENDPOINTS } from '../lib/api-constants';

/**
 * Deck Service - сервис для работы с колодами
 */
class DeckService {
  /**
   * Получить все колоды пользователя
   * @returns Promise с массивом колод
   */
  async getDecks(): Promise<Deck[]> {
    try {
      const response = await api.get<Deck[]>(API_ENDPOINTS.DECKS);
      return response.data;
    } catch (error) {
      console.error('Error fetching decks:', error);
      throw error;
    }
  }

  /**
   * Получить конкретную колоду по ID
   * @param id - ID колоды
   * @returns Promise с колодой
   */
  async getDeck(id: number): Promise<Deck> {
    try {
      const response = await api.get<Deck>(API_ENDPOINTS.DECK_BY_ID(id));
      return response.data;
    } catch (error) {
      console.error('Error fetching deck:', error);
      throw error;
    }
  }

  /**
   * Создать новую колоду
   * @param data - Данные для создания колоды
   * @returns Promise с созданной колодой
   */
  async createDeck(data: {
    name: string;
    target_lang: string;
    source_lang: string;
  }): Promise<Deck> {
    try {
      const response = await api.post<Deck>(API_ENDPOINTS.DECKS, data);
      return response.data;
    } catch (error) {
      console.error('Error creating deck:', error);
      throw error;
    }
  }

  /**
   * Обновить колоду
   * @param id - ID колоды
   * @param data - Данные для обновления
   * @returns Promise с обновленной колодой
   */
  async updateDeck(
    id: number,
    data: Partial<{ name: string; target_lang: string; source_lang: string }>
  ): Promise<Deck> {
    try {
      const response = await api.patch<Deck>(API_ENDPOINTS.DECK_BY_ID(id), data);
      return response.data;
    } catch (error) {
      console.error('Error updating deck:', error);
      throw error;
    }
  }

  /**
   * Удалить колоду
   * @param id - ID колоды
   * @returns Promise<void>
   */
  async deleteDeck(id: number): Promise<void> {
    try {
      await api.delete(API_ENDPOINTS.DECK_BY_ID(id));
    } catch (error) {
      console.error('Error deleting deck:', error);
      throw error;
    }
  }

  /**
   * Добавить слова в колоду
   * @param id - ID колоды
   * @param words - Массив слов для добавления
   * @returns Promise с обновленной колодой
   */
  async addWordsToDeck(
    id: number,
    words: { word: string; translation: string }[]
  ): Promise<Deck> {
    try {
      // Сначала получаем информацию о колоде, чтобы узнать target_lang
      const deck = await this.getDeck(id);
      
      // Преобразуем формат данных для backend
      // Backend ожидает: original_word, translation, language
      const formattedWords = words.map((w) => ({
        original_word: String(w.word),
        translation: String(w.translation),
        language: deck.target_lang || 'en',
      }));
      
      const response = await api.post<{ errors?: Array<{ error?: string; message?: string } | string>; [key: string]: unknown }>(
        API_ENDPOINTS.DECK_ADD_WORDS(id),
        { words: formattedWords }
      );
      
      // Если backend вернул 207 с ошибками, выбрасываем исключение
      if (response.status === 207 && response.data.errors && response.data.errors.length > 0) {
        const errorMessages = response.data.errors.map((err: { error?: string; message?: string } | string) => 
          typeof err === 'string' ? err : err.error || err.message || JSON.stringify(err)
        ).join('; ');
        throw new Error(`Backend errors: ${errorMessages}`);
      }
      
      return response.data;
    } catch (error) {
      console.error('Error adding words to deck:', error);
      throw error;
    }
  }

  /**
   * Удалить слово из колоды
   * @param deckId - ID колоды
   * @param wordId - ID слова
   * @returns Promise с обновленной колодой
   */
  async removeWordFromDeck(deckId: number, wordId: number): Promise<Deck> {
    try {
      const response = await api.post<Deck>(
        API_ENDPOINTS.DECK_REMOVE_WORD(deckId),
        { word_id: wordId }
      );
      return response.data;
    } catch (error) {
      console.error('Error removing word from deck:', error);
      throw error;
    }
  }

  /**
   * Сгенерировать .apkg файл для колоды
   * @param id - ID колоды
   * @returns Promise с file_id для скачивания
   */
  async generateDeckApkg(id: number): Promise<{ file_id: string }> {
    try {
      const response = await api.post<{ file_id: string }>(
        API_ENDPOINTS.DECK_GENERATE(id)
      );
      return response.data;
    } catch (error) {
      console.error('Error generating deck apkg:', error);
      throw error;
    }
  }

  /**
   * Скачать сгенерированный файл
   * @param fileId - ID файла
   * @returns Promise с Blob файла
   */
  async downloadDeck(fileId: string): Promise<Blob> {
    try {
      const response = await api.get<Blob>(API_ENDPOINTS.DOWNLOAD(fileId), {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      console.error('Error downloading deck:', error);
      throw error;
    }
  }

  /**
   * Быстрая генерация карточек с опциональным сохранением в колоду
   * @param data - Данные для генерации
   * @returns Promise с file_id для скачивания и опциональным deck_id
   */
  async generateCards(data: {
    words: string[];
    translations: Record<string, string>;
    language: string;
    deck_name: string;
    image_files?: Record<string, string>;
    audio_files?: Record<string, string>;
    save_to_decks?: boolean; // Новый параметр
  }): Promise<{ file_id: string; deck_id?: number }> {
    try {
      // 🔍 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ПЕРЕД ОТПРАВКОЙ
      console.log('');
      console.log('='.repeat(80));
      console.log('📤 ОТПРАВКА ДАННЫХ НА БЕКЕНД: /api/cards/generate/');
      console.log('='.repeat(80));
      console.log('📋 ВХОДНЫЕ ДАННЫЕ (от MainPage):');
      console.log('  - deck_name:', data.deck_name);
      console.log('  - words (массив):', data.words);
      console.log('  - language:', data.language);
      console.log('  - save_to_decks:', data.save_to_decks);
      console.log('  - Количество слов:', data.words.length);
      console.log('  - Количество переводов:', Object.keys(data.translations).length);
      console.log('  - Количество изображений:', Object.keys(data.image_files || {}).length);
      console.log('  - Количество аудио:', Object.keys(data.audio_files || {}).length);
      
      // ✅ ИСПРАВЛЕНИЕ: Отправляем words как МАССИВ, а не строку!
      // Бэкенд Django REST Framework отлично работает с JSON массивами
      // Старый способ (НЕПРАВИЛЬНЫЙ): words: data.words.join(', ')
      const requestData = {
        ...data,
        words: data.words, // ✅ Отправляем массив как есть!
      };

      console.log('');
      console.log('🔄 ДАННЫЕ ДЛЯ ОТПРАВКИ (БЕЗ ИЗМЕНЕНИЙ):');
      console.log('  - deck_name:', requestData.deck_name);
      console.log('  - words (массив!):', requestData.words);
      console.log('  - Тип words:', Array.isArray(requestData.words) ? 'Array ✅' : 'String ❌');
      console.log('');
      console.log('⚠️ ПРОВЕРКА: Не перепутались ли deck_name и words?');
      console.log('  - deck_name === words?', requestData.deck_name === requestData.words);
      console.log('  - deck_name содержит запятые?', requestData.deck_name.includes(','));
      console.log('='.repeat(80));
      console.log('');

      // Генерация колоды может занимать много времени, особенно с медиа
      const response = await api.post<{ file_id: string; deck_id?: number }>(
        '/api/cards/generate/',
        requestData,
        { timeout: 300000 } // 5 минут
      );

      console.log('');
      console.log('✅ ОТВЕТ ОТ БЕКЕНДА:');
      console.log('  - file_id:', response.data.file_id);
      console.log('  - deck_id:', response.data.deck_id);
      console.log('');

      return response.data;
    } catch (error) {
      console.error('Error generating cards:', error);
      throw error;
    }
  }

  /**
   * Анализ слов - получение переводов и информации
   * @param data - Данные для анализа
   * @returns Promise с объектом слово -> перевод
   */
  async analyzeWords(data: {
    words: string[];
    learning_language: string;
    native_language: string;
  }): Promise<{ [word: string]: string }> {
    try {
      const response = await api.post<{ [word: string]: string }>(
        '/api/cards/analyze-words/',
        data
      );
      return response.data;
    } catch (error) {
      console.error('Error analyzing words:', error);
      throw error;
    }
  }

  /**
   * Перевод слов
   * @param data - Данные для перевода
   * @returns Promise с объектом { translations: { слово -> перевод } }
   */
  async translateWords(data: {
    words: string[];
    source_language: string;
    target_language: string;
  }): Promise<{ translations: { [word: string]: string } }> {
    try {
      // Backend ожидает learning_language и native_language
      const response = await api.post<{ translations: { [word: string]: string } }>(
        '/api/cards/translate-words/',
        {
          words: data.words,
          learning_language: data.source_language, // Язык изучаемых слов
          native_language: data.target_language,   // Язык перевода (родной)
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error translating words:', error);
      throw error;
    }
  }

  /**
   * Обработка немецких сов (добавление артиклей, капитализация)
   * @param data - Массив слов для обработки
   * @returns Promise с объектом исходное слово -> обработанное слово
   */
  async processGermanWords(data: {
    words: string[];
  }): Promise<{ [word: string]: string }> {
    try {
      const results: { [word: string]: string } = {};
      
      // Backend принимает только одно слово за раз
      // Обрабатываем слова последовательно
      for (const word of data.words) {
        try {
          const response = await api.post<{ processed_word: string }>(
            '/api/cards/process-german-words/',
            { word } // Передаем одно слово как строку
          );
          
          // Backend может вернуть либо { processed_word: "das Haus" }
          // либо просто строку
          const processedWord = typeof response.data === 'string' 
            ? response.data 
            : response.data.processed_word || word;
          
          results[word] = processedWord;
        } catch (error) {
          console.error(`Error processing word "${word}":`, error);
          // В случае ошибки используем оригинальное слово
          results[word] = word;
        }
      }
      
      return results;
    } catch (error) {
      console.error('Error processing German words:', error);
      throw error;
    }
  }

  /**
   * Обработка одного немецкого слова (добавление артикля, капитализация)
   * @param word - Одно слово для обработки
   * @returns Promise с обработанным словом
   */
  async processGermanWord(word: string): Promise<{ processed_word: string }> {
    try {
      const response = await api.post<{ processed_word: string }>(
        '/api/cards/process-german-words/',
        { word }
      );
      
      // Backend может вернуть либо { processed_word: "das Haus" }
      // либо просто строку
      const processedWord = typeof response.data === 'string' 
        ? response.data 
        : response.data.processed_word || word;
      
      return { processed_word: processedWord };
    } catch (error) {
      console.error(`Error processing German word "${word}":`, error);
      // В случае ошибки возвращаем оригинальное слово
      return { processed_word: word };
    }
  }

  /**
   * Генерация изображения для слова
   * @param data - Данные для генерации изображения
   * @param signal - AbortSignal для отмены запроса
   * @returns Promise с URL изображения
   */
  async generateImage(
    data: {
      word: string;
      translation: string;
      language: string;
      image_style: 'minimalistic' | 'balanced' | 'creative';
      provider?: 'openai' | 'gemini'; // Опциональный провайдер (если не указан, берется из профиля)
      gemini_model?: 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'; // Опциональная модель Gemini
      word_id?: number; // Опциональный ID слова для привязки медиа
    },
    signal?: AbortSignal
  ): Promise<{ image_url: string }> {
    try {
      // AI-генерация изображений может занимать 60-120 секунд
      const response = await api.post<{ image_url: string }>(
        '/api/media/generate-image/',
        data,
        { 
          timeout: 180000, // 3 минуты
          signal, // Поддержка отмены запроса
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error generating image:', error);
      throw error;
    }
  }

  /**
   * Генерация аудио для слова
   * @param data - Данные для генерации аудио
   * @param signal - AbortSignal для отмены запроса
   * @returns Promise с URL аудио
   */
  async generateAudio(
    data: {
      word: string;
      language: string;
      provider?: 'openai' | 'gtts'; // Провайдер генерации аудио
      word_id?: number; // Опциональный ID слова для привязки медиа
    },
    signal?: AbortSignal
  ): Promise<{ audio_url: string }> {
    try {
      // AI-генерация аудио может занимать 30-60 секунд
      const response = await api.post<{ audio_url: string }>(
        '/api/media/generate-audio/',
        data,
        { 
          timeout: 120000, // 2 минуты
          signal, // Поддержка отмены запроса
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error generating audio:', error);
      throw error;
    }
  }

  /**
   * Редактирование изображения через миксин
   * Использует nano-banana-pro для image-to-image генерации
   * @param data - Данные для редактирования
   * @param signal - AbortSignal для отмены запроса
   * @returns Promise с URL нового изображения
   */
  async editImage(
    data: {
      word_id: number;
      mixin: string; // Что добавить/изменить на изображении (1-3 слова)
    },
    signal?: AbortSignal
  ): Promise<{ image_url: string; mixin: string; word_id: number }> {
    try {
      // AI-редактирование изображений может занимать 60-120 секунд
      const response = await api.post<{ image_url: string; mixin: string; word_id: number }>(
        '/api/media/edit-image/',
        data,
        { 
          timeout: 180000, // 3 минуты
          signal, // Поддержка отмены запроса
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error editing image:', error);
      throw error;
    }
  }

  /**
   * Обновление медиа для слова в колоде
   * @param deckId - ID колоды
   * @param wordId - ID слова
   * @param data - Данные медиа для обновления
   * @returns Promise с обновлённым словом
   */
  async updateWordMedia(
    deckId: number,
    wordId: number,
    data: {
      original_word?: string;
      translation?: string;
      image_file?: string | null;
      audio_file?: string | null;
    }
  ): Promise<{
    id: number;
    original_word: string;
    translation: string;
    language: string;
    image_file: string | null;
    audio_file: string | null;
    updated_fields: string[];
  }> {
    try {
      const response = await api.patch(
        API_ENDPOINTS.DECK_WORD(deckId, wordId),
        data
      );
      return response.data;
    } catch (error) {
      console.error('Error updating word media:', error);
      throw error;
    }
  }

  /**
   * Обновление AI-контента для слова в колоде
   * @param deckId - ID колоды
   * @param wordId - ID слова
   * @param data - AI-контент для обновления
   * @returns Promise с обновлённым словом
   */
  async updateWordAIContent(
    deckId: number,
    wordId: number,
    data: {
      etymology?: string;
      hint_text?: string;
      hint_audio?: string | null;
      sentences?: Array<{
        id?: number;
        sentence: string;
        translation: string;
        audio_file?: string | null;
      }>;
      part_of_speech?: string;
      notes?: string;
    }
  ): Promise<unknown> {
    try {
      const response = await api.patch(
        API_ENDPOINTS.DECK_WORD(deckId, wordId),
        data
      );
      return response.data;
    } catch (error) {
      console.error('Error updating word AI content:', error);
      throw error;
    }
  }

  /**
   * Перенести карточку из одной колоды в другую
   * @param wordId - ID слова/карточки
   * @param fromDeckId - ID исходной колоды
   * @param toDeckId - ID целевой колоды
   * @returns Promise<void>
   */
  async moveCardToDeck(
    wordId: number,
    fromDeckId: number,
    toDeckId: number
  ): Promise<void> {
    try {
      // Пытаемся использовать специальный эндпоинт для переноса
      await api.post(
        `${API_ENDPOINTS.DECKS}/${fromDeckId}/words/${wordId}/move/`,
        { target_deck_id: toDeckId }
      );
    } catch (error) {
      console.error('Error moving card:', error);
      throw error;
    }
  }

  /**
   * Копировать карточку в другую колоду (альтернатива перносу, если бекенд не поддерживает move)
   * @param word - Объект слова с полными данными
   * @param fromDeckId - ID исходной колоды  
   * @param toDeckId - ID целевой колоды
   * @returns Promise<void>
   */
  async copyAndMoveCard(
    word: { id: number; original_word: string; translation: string; image_file?: string | null; audio_file?: string | null },
    fromDeckId: number,
    toDeckId: number
  ): Promise<void> {
    try {
      // 1. Добавляем слово в целевую колоду
      await this.addWordsToDeck(toDeckId, [
        { word: word.original_word, translation: word.translation }
      ]);

      // 2. Если нужно скопировать медиа, получаем обновлённую колоду
      const updatedDeck = await this.getDeck(toDeckId);
      
      // Находим только что добавленное слово по совпадению текста (НЕ последнее в спике!)
      // Ищем слово с таким же original_word и translation, у которого ещё нет медиа
      const newWord = updatedDeck.words?.find(w => 
        w.original_word === word.original_word && 
        w.translation === word.translation &&
        !w.image_file && // У нового слова ещё нет картинки
        !w.audio_file    // И нет аудио
      );
      
      if (newWord && (word.image_file || word.audio_file)) {
        // Копируем медиа-файлы
        const mediaUpdate: { image_file?: string; audio_file?: string } = {};
        
        if (word.image_file) {
          mediaUpdate.image_file = word.image_file;
        }
        
        if (word.audio_file) {
          mediaUpdate.audio_file = word.audio_file;
        }
        
        // Обновляем медиа для нового слова
        await this.updateWordMedia(toDeckId, newWord.id, mediaUpdate);
      }

      // 3. Удаляем из исходной колоды
      await this.removeWordFromDeck(fromDeckId, word.id);
    } catch (error) {
      console.error('Error copying and moving card:', error);
      throw error;
    }
  }

  /**
   * Объединить колоды
   * @param params - Параметры объединения
   * @returns Promise с результатом объединения
   */
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
    try {
      const response = await api.post('/api/cards/decks/merge/', params);
      return response.data;
    } catch (error) {
      console.error('Error merging decks:', error);
      throw error;
    }
  }

  /**
   * Инвертировать все слова в колоде
   * @param deckId - ID колоды
   * @returns Promise с результатом инвертирования
   */
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
    skipped_words?: Array<{
      id: number;
      original_word: string;
      reason: string;
    }>;
    errors?: Array<{
      word_id: number;
      original_word: string;
      error: string;
    }>;
  }> {
    try {
      const response = await api.post(`/api/cards/decks/${deckId}/invert_all/`);
      return response.data;
    } catch (error) {
      console.error('Error inverting all words:', error);
      throw error;
    }
  }

  /**
   * Инвертировать одно слово в колоде
   * @param deckId - ID колоды
   * @param wordId - ID слова
   * @returns Promise с результатом инвертирования
   */
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
    try {
      const response = await api.post(`/api/cards/decks/${deckId}/invert_word/`, {
        word_id: wordId
      });
      return response.data;
    } catch (error) {
      console.error('Error inverting word:', error);
      throw error;
    }
  }

  /**
   * Создать пустые карточки для всех слов в колоде
   * @param deckId - ID колоды
   * @returns Promise с результатом создания пустых карточек
   */
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
    skipped_cards?: Array<{
      id: number;
      translation: string;
      reason: string;
    }>;
    errors?: Array<{
      word_id: number;
      original_word: string;
      error: string;
    }>;
  }> {
    try {
      const response = await api.post(`/api/cards/decks/${deckId}/create_empty_cards/`);
      return response.data;
    } catch (error) {
      console.error('Error creating empty cards:', error);
      throw error;
    }
  }

  /**
   * Создать пустую карточку для одного слова
   * @param deckId - ID колоды
   * @param wordId - ID слова
   * @returns Promise с результатом создания пустой карточки
   */
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
    try {
      const response = await api.post(`/api/cards/decks/${deckId}/create_empty_card/`, {
        word_id: wordId
      });
      return response.data;
    } catch (error) {
      console.error('Error creating empty card:', error);
      throw error;
    }
  }
}

export const deckService = new DeckService();