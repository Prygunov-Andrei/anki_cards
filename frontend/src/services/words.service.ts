/**
 * Сервис для работы с каталогом слов (Этап 8).
 * API: /api/words/
 */
import api from './api';
import { API_ENDPOINTS } from '../lib/api-constants';
import type {
  Word,
  WordsListResponse,
  WordsListParams,
  WordStats,
  WordsStats,
  BulkActionRequest,
  BulkActionResponse,
  WordEnterLearningResponse,
  WordUpdate,
} from '../types';

class WordsService {
  /**
   * Список слов с фильтрацией, сортировкой и пагинацией
   */
  async getList(params?: WordsListParams): Promise<WordsListResponse> {
    const response = await api.get<WordsListResponse>(API_ENDPOINTS.WORDS_LIST, {
      params: params ?? {},
    });
    return response.data;
  }

  /**
   * Детали слова по id (для страницы слова из каталога)
   */
  async getWord(id: number): Promise<Word> {
    const response = await api.get<Word>(API_ENDPOINTS.WORD_BY_ID(id));
    return response.data;
  }

  /**
   * Обновление слова (PATCH)
   */
  async updateWord(id: number, data: Partial<WordUpdate>): Promise<Word> {
    const response = await api.patch<Word>(API_ENDPOINTS.WORD_BY_ID(id), data);
    return response.data;
  }

  /**
   * Удаление слова
   */
  async deleteWord(id: number): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(
      API_ENDPOINTS.WORD_BY_ID(id)
    );
    return response.data;
  }

  /**
   * Статистика по слову
   */
  async getWordStats(id: number): Promise<WordStats> {
    const response = await api.get<WordStats>(API_ENDPOINTS.WORD_STATS(id));
    return response.data;
  }

  /**
   * Общая статистика по словам пользователя
   */
  async getWordsStats(): Promise<WordsStats> {
    const response = await api.get<WordsStats>(API_ENDPOINTS.WORDS_STATS);
    return response.data;
  }

  /**
   * Отправить слово в режим изучения
   */
  async enterLearning(id: number): Promise<WordEnterLearningResponse> {
    const response = await api.post<WordEnterLearningResponse>(
      API_ENDPOINTS.WORD_ENTER_LEARNING(id)
    );
    return response.data;
  }

  /**
   * Массовые действия со словами
   */
  async bulkAction(
    request: BulkActionRequest
  ): Promise<BulkActionResponse> {
    const response = await api.post<BulkActionResponse>(
      API_ENDPOINTS.WORDS_BULK_ACTION,
      request
    );
    return response.data;
  }
}

export const wordsService = new WordsService();
