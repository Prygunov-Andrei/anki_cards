import { toast } from 'sonner@2.0.3';

/**
 * Утилиты для отображения Toast уведомлений
 * iOS 25 стиль с поддержкой темной темы
 */

interface ToastOptions {
  duration?: number;
  description?: string;
}

/**
 * Показывает уведомление об успехе (зеленое)
 */
export const showSuccess = (message: string, options?: ToastOptions) => {
  return toast.success(message, {
    duration: options?.duration || 3000,
    description: options?.description,
  });
};

/**
 * Показывает уведомление об ошибке (красное)
 */
export const showError = (message: string, options?: ToastOptions) => {
  return toast.error(message, {
    duration: options?.duration || 5000,
    description: options?.description,
  });
};

/**
 * Показывает информационное уведомление (синее)
 */
export const showInfo = (message: string, options?: ToastOptions) => {
  return toast.info(message, {
    duration: options?.duration || 3000,
    description: options?.description,
  });
};

/**
 * Показывает предупреждение (оранжевое)
 */
export const showWarning = (message: string, options?: ToastOptions) => {
  return toast.warning(message, {
    duration: options?.duration || 4000,
    description: options?.description,
  });
};

/**
 * Показывает уведомление о загрузке
 */
export const showLoading = (message: string) => {
  return toast.loading(message);
};

/**
 * Обновляет существующее уведомление
 */
export const updateToast = (
  toastId: string | number,
  message: string,
  type: 'success' | 'error' | 'info' = 'success'
) => {
  const toastFn = type === 'success' ? showSuccess : type === 'error' ? showError : showInfo;
  toast.dismiss(toastId);
  return toastFn(message);
};

/**
 * Закрывает уведомление по ID
 */
export const dismissToast = (toastId?: string | number) => {
  toast.dismiss(toastId);
};

/**
 * Закрывает все уведомления
 */
export const dismissAllToasts = () => {
  toast.dismiss();
};