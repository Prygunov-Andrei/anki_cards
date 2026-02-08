import axios from 'axios';
import apiClient, { handleApiError } from './api';
import { User } from '../types'; // ИСПРАВЛЕНО: правильный импорт User
import { API_ENDPOINTS } from '../lib/api-constants'; // ИСПРАВЛЕНО: используем новый файл констант

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
      console.log('[authService] Sending login request with credentials:', { username: credentials.username });
      const response = await apiClient.post<{ token: string; user_id: number }>(API_ENDPOINTS.LOGIN, credentials);
      
      console.log('[authService] Login response received:', response.data);
      console.log('[authService] Response headers:', response.headers);
      console.log('[authService] Full response:', response);
      
      // ⚠️ Проверка: убеждаемся, что ответ не HTML
      if (typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')) {
        console.error('[authService] ❌ Получен HTML вместо JSON!');
        console.error('[authService] Это означает, что запрос уходит не на backend API');
        console.error('[authService] Проверьте BASE_URL в /services/api.ts');
        throw new Error('Backend недоступен: получен HTML вместо JSON. Проверьте, что backend запущен и VITE_API_BASE_URL указан верно.');
      }
      
      // Сохраняем токен
      if (response.data.token) {
        const token = response.data.token;
        console.log('[authService] Token found:', token);
        localStorage.setItem('authToken', token);
        
        // Получаем профиль пользователя с сервера с токеном
        console.log('[authService] Fetching user profile...');
        const profileResponse = await apiClient.get<User>('/api/user/profile/', {
          headers: {
            'Authorization': `Token ${token}`
          }
        });
        const user = profileResponse.data;
        console.log('[authService] User profile received:', user);
        
        // Сохраняем данные пользователя
        localStorage.setItem('user', JSON.stringify(user));
        
        return {
          token: token,
          user: user
        };
      }
      
      console.error('[authService] No token in response! Response data:', response.data);
      throw new Error('No token received');
    } catch (error) {
      console.error('[authService] Login error:', error);
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
        
        // Если сервер вернул полный объект user, используем его
        if (response.data.user) {
          localStorage.setItem('user', JSON.stringify(response.data.user));
          return {
            token: token,
            user: response.data.user
          };
        }
        
        // Иначе получаем профиль с сервера с токеном
        const profileResponse = await apiClient.get<User>('/api/user/profile/', {
          headers: {
            'Authorization': `Token ${token}`
          }
        });
        const user = profileResponse.data;
        
        localStorage.setItem('user', JSON.stringify(user));
        
        return {
          token: token,
          user: user
        };
      }
      
      throw new Error('No token received');
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        console.error('[authService] Registration error details:', error.response?.data);
      } else {
        console.error('[authService] Registration error details:', error);
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
      console.error('Logout error:', error);
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
      console.error('Error parsing user data:', error);
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
      const response = await apiClient.get<User>('/api/user/profile/');
      
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