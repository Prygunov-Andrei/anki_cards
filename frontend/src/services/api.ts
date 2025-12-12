import axios, { AxiosInstance, AxiosError } from 'axios';

/**
 * Базовый URL для API
 * В продакшене: пустая строка (запросы на тот же домен)
 * В разработке: ngrok URL из .env.development
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL?.startsWith('/') ? '' : (import.meta.env.VITE_API_BASE_URL || '');

/**
 * Создание экземпляра Axios с настройками
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    // ngrok требует этот заголовок для обхода предупреждения
    'ngrok-skip-browser-warning': 'true', // Для совместимости с туннелями
  },
  withCredentials: false, // Отключаем credentials для CORS
});

/**
 * Interceptor для добавления токена авторизации к запросам
 */
apiClient.interceptors.request.use(
  (config) => {
    // Улучшенное логирование (не показываем undefined для GET)
    const method = config.method?.toUpperCase();
    const hasData = config.data && Object.keys(config.data).length > 0;
    
    if (hasData) {
      console.log(`[API] ${method} ${config.url}`, config.data);
    } else {
      console.log(`[API] ${method} ${config.url}`);
    }
    
    const token = localStorage.getItem('authToken');
    if (token) {
      // Django REST Framework использует формат "Token <token>"
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
  (response) => {
    console.log(`[API] Response ${response.status}:`, response.data);
    return response;
  },
  (error: AxiosError) => {
    console.error('[API] Response error:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      data: error.response?.data,
      config: {
        url: error.config?.url,
        method: error.config?.method,
        baseURL: error.config?.baseURL,
      }
    });
    
    // Network Error - показываем понятное сообщение
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error('⚠️ NETWORK ERROR: Не удалось подключиться к backend серверу');
      console.error('📍 Проверьте:');
      console.error('   1. Backend сервер запущен (Django)');
      console.error('   2. Туннель активен (Cloudflare/ngrok)');
      console.error(`   3. URL корректный: ${BASE_URL}`);
      console.error('   4. Нет блокировки CORS');
    }
    
    // Если токен истек или невалиден - очищаем хранилище
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Интерфейс для ошибок API
 */
export interface ApiError {
  message: string;
  status?: number;
  data?: any;
}

/**
 * Обработчик ошибок API
 */
export const handleApiError = (error: any): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    
    // Network Error - проблема с подключением
    if (axiosError.code === 'ERR_NETWORK' || axiosError.message === 'Network Error') {
      return {
        message: 'Не удалось подключиться к серверу. Проверьте, что backend запущен и туннель активен.',
        status: 0,
        data: { code: 'NETWORK_ERROR' },
      };
    }
    
    // Timeout
    if (axiosError.code === 'ECONNABORTED') {
      return {
        message: 'Превышено время ожидания ответа от сервера',
        status: 0,
        data: { code: 'TIMEOUT' },
      };
    }
    
    // CORS Error
    if (axiosError.message.includes('CORS')) {
      return {
        message: 'Ошибка CORS. Backend должен разрешить запросы от этого домена.',
        status: 0,
        data: { code: 'CORS_ERROR' },
      };
    }
    
    // Извлекаем сообщение об ошибке из разных возможных полей
    const errorMessage = 
      axiosError.response?.data?.detail ||
      axiosError.response?.data?.message || 
      axiosError.response?.data?.error || 
      axiosError.message || 
      'Произошла ошибка';
    
    return {
      message: errorMessage,
      status: axiosError.response?.status,
      data: axiosError.response?.data,
    };
  }
  return {
    message: error.message || 'Неизвестная ошибка',
  };
};

export default apiClient;