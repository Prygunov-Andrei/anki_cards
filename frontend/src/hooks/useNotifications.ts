import { useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { notificationsService } from '@/services/notifications.service';

/**
 * Хук для автоматической проверки и показа уведомлений.
 * Вызывается в корневом Layout — проверяет каждые 5 минут.
 */
export function useNotifications(isAuthenticated: boolean) {
  const navigate = useNavigate();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const checkNotifications = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      const result = await notificationsService.check();

      if (result.should_notify && result.message) {
        notificationsService.showBrowserNotification(
          'Anki Cards — Тренировка',
          result.message,
          () => navigate('/training'),
        );
      }
    } catch {
      // Silently ignore errors (user might be offline)
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (!isAuthenticated) return;

    // Запросить разрешение при первом рендере
    notificationsService.requestPermission();

    // Первая проверка через 30 секунд (дать время загрузить страницу)
    const initialTimeout = setTimeout(checkNotifications, 30_000);

    // Потом каждые 5 минут
    intervalRef.current = setInterval(checkNotifications, 5 * 60 * 1000);

    return () => {
      clearTimeout(initialTimeout);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isAuthenticated, checkNotifications]);
}
