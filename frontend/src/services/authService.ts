import axios from 'axios';
import apiClient, { handleApiError } from './api';
import { User } from '../types'; // ИСПРАВЛЕНО: правильный импорт User
import { API_ENDPOINTS } from '../lib/api-constants'; // ИСПРАВЛЕНО: используем новый файл констант
import { logger } from '@/utils/logger';

/**
 * Интерфейс для данных входа
 */
export interface LoginCredentials {
  username: string;
  password: string;
}

/**
 * Интерфейс для данных регистрации
 */
export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  native_language?: string; // Родной язык (язык интерфейса), по умолчанию 'en'
  learning_language?: string; // Изучаемый язык, по умолчанию 'de'
  preferred_language?: string; // Для совместимости с бэкендом, обычно равен native_language
}

/**
 * Интерфейс для ответа аутентификации
 */
export interface AuthResponse {
  token: string;
  user: User;
}

/**
 * Сервис для работы с аутентификацией
 */
export const authService = {
  /**
   * Вход в систему
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      logger.log('[authService] Sending login request with credentials:', { username: credentials.username });
      const response = await apiClient.post<{ token: string; user_id: number }>(API_ENDPOINTS.LOGIN, credentials);
      
      logger.log('[authService] Login response received:', response.data);
      logger.log('[authService] Response headers:', response.headers);
      logger.log('[authService] Full response:', response);
      
      // ⚠️ Проверка: убеждаемся, что ответ не HTML
      if (typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')) {
        logger.error('[authService] ❌ Получен HTML вместо JSON!');
        logger.error('[authService] Это означает, что запрос уходит не на backend API');
        logger.error('[authService] Проверьте BASE_URL в /services/api.ts');
        throw new Error('Backend недоступен: получен HTML вместо JSON. Проверьте, что backend запущен и VITE_API_BASE_URL указан верно.');
      }
      
      // Сохраняем токен
      if (response.data.token) {
        const token = response.data.token;
        logger.log('[authService] Token found:', token);
        localStorage.setItem('authToken', token);

        // Backend returns full profile + token in one response
        const { token: _, ...userData } = response.data;
        const user = userData as unknown as User;
        logger.log('[authService] User profile from login response:', user);

        // Сохраняем данные пользователя
        localStorage.setItem('user', JSON.stringify(user));

        return {
          token: token,
          user: user
        };
      }
      
      logger.error('[authService] No token in response! Response data:', response.data);
      throw new Error('No token received');
    } catch (error) {
      logger.error('[authService] Login error:', error);
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },

  /**
   * Регистрация нового пользователя
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      const response = await apiClient.post<{ token: string; user_id?: number; user?: User }>(API_ENDPOINTS.REGISTER, data);
      
      // Сохраняем токен
      if (response.data.token) {
        const token = response.data.token;
        localStorage.setItem('authToken', token);

        // Backend returns full profile + token in one response
        const { token: _, user_id: _uid, ...userData } = response.data;
        const user = userData as unknown as User;

        localStorage.setItem('user', JSON.stringify(user));

        return {
          token: token,
          user: user
        };
      }
      
      throw new Error('No token received');
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        logger.error('[authService] Registration error details:', error.response?.data);
      } else {
        logger.error('[authService] Registration error details:', error);
      }
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },

  /**
   * Выход из системы
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post(API_ENDPOINTS.LOGOUT);
    } catch (error) {
      // Игнорируем ошибки при выходе
      logger.error('Logout error:', error);
    } finally {
      // Очищаем локальное хранилище в любом случае
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
    }
  },

  /**
   * Получение текущего пользователя из localStorage
   */
  getCurrentUser(): User | null {
    try {
      const userJson = localStorage.getItem('user');
      if (!userJson || userJson === 'undefined' || userJson === 'null') {
        return null;
      }
      return JSON.parse(userJson);
    } catch (error) {
      logger.error('Error parsing user data:', error);
      // Очищаем поврежденные данные
      localStorage.removeItem('user');
      return null;
    }
  },

  /**
   * Получение профиля пользователя с сервера
   */
  async getProfile(): Promise<User> {
    try {
      const response = await apiClient.get<User>(API_ENDPOINTS.USER_PROFILE);
      
      // Обновляем данные пользователя в localStorage
      localStorage.setItem('user', JSON.stringify(response.data));
      
      return response.data;
    } catch (error) {
      const apiError = handleApiError(error);
      throw new Error(apiError.message);
    }
  },

  /**
   * Проверка наличия токена
   */
  hasToken(): boolean {
    return !!localStorage.getItem('authToken');
  },

  /**
   * Получение токеа
   */
  getToken(): string | null {
    return localStorage.getItem('authToken');
  },
};

export default authService;