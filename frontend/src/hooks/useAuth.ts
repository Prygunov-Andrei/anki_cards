import { useState, useEffect } from 'react';
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
    
    // Cleanup функция для предотвращения обновления размонтированного компонента
    return () => {
      isMounted = false;
    };
  }, []);

  const login = (token: string, userData: User) => {
    localStorage.setItem('authToken', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    setIsAuthenticated(true);
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
    setIsAuthenticated(false);
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
    }
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    updateUser,
  };
};