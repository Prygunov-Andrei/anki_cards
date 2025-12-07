import apiClient from './api';
import { User } from '../types';

/**
 * Сервис для работы с профилем пользователя
 */

export interface ProfileUpdateData {
  first_name?: string;
  last_name?: string;
  email?: string;
  native_language?: string;
  learning_language?: string;
  image_provider?: 'openai' | 'gemini' | 'nano-banana';
  gemini_model?: 'gemini-2.5-flash-image' | 'nano-banana-pro-preview';
}

export const profileService = {
  /**
   * Получить данные профиля
   */
  async getProfile(): Promise<User> {
    const response = await apiClient.get<User>('/api/user/profile/');
    return response.data;
  },

  /**
   * Обновить данные профиля (текстовые поля)
   */
  async updateProfile(data: ProfileUpdateData): Promise<User> {
    const response = await apiClient.patch<User>('/api/user/profile/', data);
    return response.data;
  },

  /**
   * Загрузить аватар (FormData с файлом)
   */
  async uploadAvatar(file: File): Promise<User> {
    const formData = new FormData();
    formData.append('avatar', file);

    const response = await apiClient.patch<User>('/api/user/profile/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Удалить аватар
   */
  async removeAvatar(): Promise<User> {
    const response = await apiClient.patch<User>('/api/user/profile/', {
      avatar: null,
    });
    return response.data;
  },

  /**
   * Обновить профиль с аватаром (комбинированный метод)
   * Использует FormData для отправки и текстовых данных, и файла
   */
  async updateProfileWithAvatar(
    data: ProfileUpdateData,
    avatarFile?: File | null
  ): Promise<User> {
    const formData = new FormData();

    // Добавляем текстовые поля
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value.toString());
      }
    });

    // Добавляем файл аватара, если он есть
    if (avatarFile) {
      formData.append('avatar', avatarFile);
    }

    const response = await apiClient.patch<User>('/api/user/profile/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};