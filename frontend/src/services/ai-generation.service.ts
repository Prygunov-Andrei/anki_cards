import api from './api';
import { API_ENDPOINTS } from '../lib/api-constants';
import {
  GenerateEtymologyRequest,
  GenerateEtymologyResponse,
  GenerateHintRequest,
  GenerateHintResponse,
  GenerateSentenceRequest,
  GenerateSentenceResponse,
  GenerateSynonymRequest,
  GenerateSynonymResponse,
} from '../types';

/**
 * Сервис для работы с AI генерацией контента
 * Этап 7: Генерация этимологии, подсказок, предложений и синонимов
 */
class AIGenerationService {
  /**
   * Генерация этимологии для слова
   * @param request - параметры запроса (word_id, force_regenerate)
   * @returns ответ с этимологией и информацией о токенах
   */
  async generateEtymology(
    request: GenerateEtymologyRequest
  ): Promise<GenerateEtymologyResponse> {
    const response = await api.post<GenerateEtymologyResponse>(
      API_ENDPOINTS.GENERATE_ETYMOLOGY,
      request
    );
    return response.data;
  }

  /**
   * Генерация подсказки (текст + опционально аудио)
   * @param request - параметры запроса (word_id, force_regenerate, generate_audio)
   * @returns ответ с подсказкой и информацией о токенах
   */
  async generateHint(
    request: GenerateHintRequest
  ): Promise<GenerateHintResponse> {
    const response = await api.post<GenerateHintResponse>(
      API_ENDPOINTS.GENERATE_HINT,
      request
    );
    return response.data;
  }

  /**
   * Генерация предложений с использованием слова
   * @param request - параметры запроса (word_id, count, context)
   * @returns ответ с предложениями и информацией о токенах
   */
  async generateSentences(
    request: GenerateSentenceRequest
  ): Promise<GenerateSentenceResponse> {
    const response = await api.post<GenerateSentenceResponse>(
      API_ENDPOINTS.GENERATE_SENTENCE,
      request
    );
    return response.data;
  }

  /**
   * Генерация синонима для слова
   * @param request - параметры запроса (word_id, create_card)
   * @returns ответ с синонимом и информацией о токенах
   */
  async generateSynonym(
    request: GenerateSynonymRequest
  ): Promise<GenerateSynonymResponse> {
    const response = await api.post<GenerateSynonymResponse>(
      API_ENDPOINTS.GENERATE_SYNONYM,
      request
    );
    return response.data;
  }
}

export const aiGenerationService = new AIGenerationService();
