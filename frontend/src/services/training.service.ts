/**
 * Сервис для работы с тренировочными сессиями (Этап 10).
 * API: /api/training/
 */
import api from './api';
import { API_ENDPOINTS } from '../lib/api-constants';
import type {
  TrainingSessionParams,
  TrainingSessionResponse,
  TrainingAnswerRequest,
  TrainingAnswerResponse,
  TrainingStats,
  TrainingDashboard,
  ForgettingCurveResponse,
} from '../types';

class TrainingService {
  /**
   * Получить карточки для тренировочной сессии
   */
  async getSession(
    params?: TrainingSessionParams
  ): Promise<TrainingSessionResponse> {
    const response = await api.get<TrainingSessionResponse>(
      API_ENDPOINTS.TRAINING_SESSION,
      { params }
    );
    return response.data;
  }

  /**
   * Отправить ответ на карточку
   */
  async submitAnswer(
    data: TrainingAnswerRequest
  ): Promise<TrainingAnswerResponse> {
    const response = await api.post<TrainingAnswerResponse>(
      API_ENDPOINTS.TRAINING_ANSWER,
      data
    );
    return response.data;
  }

  /**
   * Перевести карточку в режим изучения
   */
  async enterLearning(cardId: number): Promise<{ card_id: number; message: string }> {
    const response = await api.post(API_ENDPOINTS.TRAINING_ENTER_LEARNING, {
      card_id: cardId,
    });
    return response.data;
  }

  /**
   * Вывести карточку из режима изучения
   */
  async exitLearning(cardId: number): Promise<{ card_id: number; message: string }> {
    const response = await api.post(API_ENDPOINTS.TRAINING_EXIT_LEARNING, {
      card_id: cardId,
    });
    return response.data;
  }

  /**
   * Получить статистику тренировок
   */
  async getStats(period?: 'day' | 'week' | 'month' | 'all'): Promise<TrainingStats> {
    const response = await api.get<TrainingStats>(
      API_ENDPOINTS.TRAINING_STATS,
      { params: period ? { period } : undefined }
    );
    return response.data;
  }

  /**
   * Получить данные кривой забывания
   */
  async getForgettingCurve(): Promise<ForgettingCurveResponse> {
    const response = await api.get<ForgettingCurveResponse>(
      API_ENDPOINTS.FORGETTING_CURVE
    );
    return response.data;
  }

  /**
   * Получить дашборд тренировок (колоды, категории, сироты с подсчётом карточек)
   */
  async getDashboard(): Promise<TrainingDashboard> {
    const response = await api.get<TrainingDashboard>(
      API_ENDPOINTS.TRAINING_DASHBOARD
    );
    return response.data;
  }

  /**
   * Активировать колоду для тренировки
   */
  async activateDeck(deckId: number): Promise<void> {
    await api.post(API_ENDPOINTS.TRAINING_DECK_ACTIVATE(deckId));
  }

  /**
   * Деактивировать колоду
   */
  async deactivateDeck(deckId: number): Promise<void> {
    await api.post(API_ENDPOINTS.TRAINING_DECK_DEACTIVATE(deckId));
  }

  /**
   * Активировать категорию для тренировки
   */
  async activateCategory(categoryId: number): Promise<void> {
    await api.post(API_ENDPOINTS.TRAINING_CATEGORY_ACTIVATE(categoryId));
  }

  /**
   * Деактивировать категорию
   */
  async deactivateCategory(categoryId: number): Promise<void> {
    await api.post(API_ENDPOINTS.TRAINING_CATEGORY_DEACTIVATE(categoryId));
  }

  /**
   * Обновить настройку include_orphan_words
   */
  async setIncludeOrphanWords(value: boolean): Promise<void> {
    await api.patch(API_ENDPOINTS.TRAINING_SETTINGS, {
      include_orphan_words: value,
    });
  }
}

export const trainingService = new TrainingService();
