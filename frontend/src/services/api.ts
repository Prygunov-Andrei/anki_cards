import axios, { AxiosInstance, AxiosError } from 'axios';

/**
 * Базовый URL для API.
 * В продакшене: пустая строка (запросы на тот же домен через /api).
 * В разработке: VITE_API_BASE_URL из .env.development или http://localhost:8000.
 */
const getBaseUrl = (): string => {
  const envUrl = import.meta.env?.VITE_API_BASE_URL;
  if (envUrl && envUrl.startsWith('/')) {
    return '';
  }
  if (envUrl) {
    return envUrl.replace(/\/$/, '');
  }
  if (import.meta.env?.DEV) {
    return 'http://localhost:8000';
  }
  return '';
};

const BASE_URL = getBaseUrl();

/**
 * Создание экземпляра Axios с настройками
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: false,
});

/**
 * Interceptor для добавления токена авторизации к запросам
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

/**
 * Interceptor для обработки ответов
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error('Не удалось подключиться к backend. Проверьте, что сервер запущен:', BASE_URL || 'текущий домен');
    }
    if (error.response?.status === 401) {
      // Очищаем невалидный токен из localStorage.
      // НЕ делаем window.location.href — это вызывает жёсткую перезагрузку
      // и цикл редиректов при фоновых polling-запросах (notifications).
      // Вместо этого диспатчим custom event, который useAuth слушает
      // и обновляет React state → ProtectedRoute делает мягкий редирект.
      const requestUrl = error.config?.url || '';
      const isLoginRequest = requestUrl.includes('/login') || requestUrl.includes('/register');
      if (!isLoginRequest) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        window.dispatchEvent(new CustomEvent('auth:token-expired'));
      }
    }
    return Promise.reject(error);
  }
);

export interface ApiError {
  message: string;
  status?: number;
  data?: Record<string, unknown>;
}

export const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<Record<string, unknown>>;

    if (axiosError.code === 'ERR_NETWORK' || axiosError.message === 'Network Error') {
      return {
        message: 'Не удалось подключиться к серверу. Проверьте, что backend запущен.',
        status: 0,
        data: { code: 'NETWORK_ERROR' },
      };
    }
    if (axiosError.code === 'ECONNABORTED') {
      return {
        message: 'Превышено время ожидания ответа от сервера',
        status: 0,
        data: { code: 'TIMEOUT' },
      };
    }
    if (axiosError.message.includes('CORS')) {
      return {
        message: 'Ошибка CORS. Backend должен разрешить запросы от этого домена.',
        status: 0,
        data: { code: 'CORS_ERROR' },
      };
    }
    const responseData = axiosError.response?.data;
    const errorMessage =
      (typeof responseData?.detail === 'string' ? responseData.detail : undefined) ||
      (typeof responseData?.message === 'string' ? responseData.message : undefined) ||
      (typeof responseData?.error === 'string' ? responseData.error : undefined) ||
      axiosError.message ||
      'Произошла ошибка';
    return {
      message: errorMessage,
      status: axiosError.response?.status,
      data: axiosError.response?.data as Record<string, unknown> | undefined,
    };
  }
  return {
    message: error instanceof Error ? error.message : 'Неизвестная ошибка',
  };
};

export default apiClient;
