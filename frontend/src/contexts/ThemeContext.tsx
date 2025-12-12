import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuthContext } from './AuthContext';
import axios from 'axios';

export type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: ReactNode;
}

// API URL из переменной окружения или пустая строка для продакшена
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.startsWith('/') ? '' : (import.meta.env.VITE_API_BASE_URL || '');

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const authContext = useAuthContext();
  const { user, isAuthenticated } = authContext || { user: null, isAuthenticated: false };
  
  // Флаг для отслеживания первой загрузки
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Инициализация темы из localStorage или системных настроек
  const [theme, setThemeState] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    if (savedTheme) {
      return savedTheme;
    }
    
    // Проверяем системные настройки
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    
    return 'light';
  });

  // Загружаем тему из профиля пользователя при авторизации
  useEffect(() => {
    if (isAuthenticated && user?.theme) {
      setThemeState(user.theme as Theme);
    }
    setIsInitialized(true);
  }, [isAuthenticated, user?.theme]);

  // Применяем тему к document
  useEffect(() => {
    const root = window.document.documentElement;
    
    // Удаляем старый класс
    root.classList.remove('light', 'dark');
    
    // Добавляем новый класс
    root.classList.add(theme);
    
    // Сохраняем в localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  const setTheme = async (newTheme: Theme) => {
    setThemeState(newTheme);
    
    // Синхронизируем с сервером только если пользователь авторизован и токен существует
    if (isAuthenticated && user) {
      const token = localStorage.getItem('authToken'); // Исправлено: authToken вместо token
      
      // Если нет токена - просто пропускаем синхронизацию без предупреждения
      if (!token) {
        return;
      }
      
      try {
        await axios.patch(
          `${API_BASE_URL}/user/profile/`,
          { theme: newTheme },
          {
            headers: {
              Authorization: `Token ${token}`,
              'ngrok-skip-browser-warning': 'true',
            },
          }
        );
        console.log('Theme synced with server successfully');
      } catch (error) {
        // Тихо обрабатываем ошибку - тема уже сохранена локально
        if (axios.isAxiosError(error)) {
          // Логируем только если это не ошибка "поле не поддерживается"
          if (error.response?.status !== 400) {
            console.debug('Theme sync skipped:', error.response?.status);
          }
        }
      }
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };

  const value = {
    theme,
    isDark: theme === 'dark',
    toggleTheme,
    setTheme,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};