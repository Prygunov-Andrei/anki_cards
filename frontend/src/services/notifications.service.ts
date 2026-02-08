import api from '@/services/api';
import { API_ENDPOINTS } from '@/lib/api-constants';
import type { NotificationSettings, NotificationCheckResponse } from '@/types';

export const notificationsService = {
  async getSettings(): Promise<NotificationSettings> {
    const { data } = await api.get(API_ENDPOINTS.NOTIFICATION_SETTINGS);
    return data;
  },

  async updateSettings(settings: Partial<NotificationSettings>): Promise<NotificationSettings> {
    const { data } = await api.patch(API_ENDPOINTS.NOTIFICATION_SETTINGS, settings);
    return data;
  },

  async check(): Promise<NotificationCheckResponse> {
    const { data } = await api.get(API_ENDPOINTS.NOTIFICATION_CHECK);
    return data;
  },

  /**
   * Запрашивает разрешение на браузерные уведомления.
   * @returns 'granted' | 'denied' | 'default'
   */
  async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      return 'denied';
    }
    return await Notification.requestPermission();
  },

  /**
   * Показывает браузерное уведомление (если есть разрешение).
   */
  showBrowserNotification(title: string, body: string, onClick?: () => void) {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
      return;
    }
    const notification = new Notification(title, {
      body,
      icon: '/favicon.ico',
      tag: 'anki-training-reminder',
    });
    if (onClick) {
      notification.onclick = () => {
        window.focus();
        onClick();
        notification.close();
      };
    }
    // Автозакрытие через 10 секунд
    setTimeout(() => notification.close(), 10000);
  },
};
