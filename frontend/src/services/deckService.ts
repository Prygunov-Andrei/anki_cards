import apiClient, { handleApiError } from './api';
import { Deck, Card, GenerateDeckRequest } from '../types';
import { API_ENDPOINTS } from '../lib/config';

/**
 * Интерфейс для параметров создания колоды
 */
export interface CreateDeckParams {
  words: string[];
  sourceLanguage: string;
  targetLanguage: string;
  imageStyle?: string;
  voiceGender?: string;
}

/**
 * Сервис для работы с колодами ANKI
 */
export const deckService = {
  /**
   * Получение списка всех колод пользователя
   */
  async getDecks(): Promise<Deck[]> {
    try {
      const response = await apiClient.get<Deck[]>(API_ENDPOINTS.DECKS);
      return response.data;
    } catch (error) {
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },

  /**
   * Получение одной колоды по ID
   */
  async getDeck(deckId: string): Promise<Deck> {
    try {
      const response = await apiClient.get<Deck>(API_ENDPOINTS.DECK_BY_ID(deckId));
      return response.data;
    } catch (error) {
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },

  /**
   * Создание новой колоды
   */
  async createDeck(params: CreateDeckParams): Promise<{ taskId: string }> {
    try {
      const response = await apiClient.post<{ taskId: string }>(API_ENDPOINTS.GENERATE, params);
      return response.data;
    } catch (error) {
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },

  /**
   * Удаление колоды
   */
  async deleteDeck(deckId: string): Promise<void> {
    try {
      await apiClient.delete(API_ENDPOINTS.DECK_BY_ID(deckId));
    } catch (error) {
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },

  /**
   * Скачивание ZIP архива колоды
   */
  async downloadDeck(deckId: string): Promise<Blob> {
    try {
      const response = await apiClient.get(`${API_ENDPOINTS.DECK_BY_ID(deckId)}download/`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },

  /**
   * Проверка статуса генерации колоды
   */
  async checkGenerationStatus(taskId: string): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress?: number;
    deckId?: string;
    error?: string;
  }> {
    try {
      const response = await apiClient.get(`/api/decks/status/${taskId}/`);
      return response.data;
    } catch (error) {
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },

  /**
   * Получение карточек колоды
   */
  async getDeckCards(deckId: string): Promise<Card[]> {
    try {
      const response = await apiClient.get<Card[]>(`${API_ENDPOINTS.DECK_BY_ID(deckId)}cards/`);
      return response.data;
    } catch (error) {
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },
};

export default deckService;