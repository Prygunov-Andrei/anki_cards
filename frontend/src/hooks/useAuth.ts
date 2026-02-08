import { useState, useEffect, useCallback, useMemo } from 'react';
import { User } from '../types';
import authService from '../services/authService';

/**
 * Хук для работы с авторизацией
 */
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Проверка наличия токена и загрузка профиля при инициализации
    let isMounted = true; // Флаг для предотвращения race condition
    
    const initAuth = async () => {
      const token = authService.hasToken();
      const storedUser = authService.getCurrentUser();

      if (token && storedUser) {
        try {
          // Пытаемся загрузить актуальный профиль с сервера
          const profile = await authService.getProfile();
          
          // Проверяем, что компонент еще смонтирован
          if (isMounted) {
            setUser(profile);
            setIsAuthenticated(true);
          }
        } catch (error) {
          console.error('Failed to load profile:', error);
          // Если не удалось ��агрузить профиль, используем сохраненные данные
          // но помечаем пользователя как неавторизованного если ошибка 401
          if (error instanceof Error && error.message.includes('401')) {
            // Токен недействителен, очищаем данные
            if (isMounted) {
              localStorage.removeItem('authToken');
              localStorage.removeItem('user');
              setUser(null);
              setIsAuthenticated(false);
            }
          } else {
            // Другая ошибка (сеть и т.д.), используем сохраненные данные
            if (isMounted) {
              setUser(storedUser);
              setIsAuthenticated(true);
            }
          }
        }
      }

      if (isMounted) {
        setIsLoading(false);
      }
    };

    initAuth();

    // Слушаем custom event от API interceptor (когда токен стал невалидным при 401)
    const handleTokenExpired = () => {
      if (isMounted) {
        setUser(null);
        setIsAuthenticated(false);
      }
    };
    window.addEventListener('auth:token-expired', handleTokenExpired);
    
    // Cleanup функция для предотвращения обновления размонтированного компонента
    return () => {
      isMounted = false;
      window.removeEventListener('auth:token-expired', handleTokenExpired);
    };
  }, []);

  const login = useCallback((token: string, userData: User) => {
    localStorage.setItem('authToken', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  const updateUser = useCallback((userData: Partial<User>) => {
    setUser(prev => {
      if (!prev) return prev;
      const updatedUser = { ...prev, ...userData };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return updatedUser;
    });
  }, []);

  return useMemo(() => ({
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    updateUser,
  }), [user, isAuthenticated, isLoading, login, logout, updateUser]);
};