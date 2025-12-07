import api from '../lib/api';
import { AuthResponse, LoginRequest, RegisterRequest, User } from '../types';

/**
 * Сервис для работы с авторизацией и аутентификацией
 */

export const authService = {
  /**
   * Вход в систему
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login/', credentials);
    return response.data;
  },

  /**
   * Регистрация нового пользователя
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/register/', data);
    return response.data;
  },

  /**
   * Выход из системы
   */
  async logout(): Promise<void> {
    await api.post('/auth/logout/');
  },

  /**
   * Получить данные текущего пользователя
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/user/');
    return response.data;
  },

  /**
   * Обновить профиль пользователя
   */
  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await api.patch<User>('/auth/user/', data);
    return response.data;
  },

  /**
   * Изменить пароль
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },
};
