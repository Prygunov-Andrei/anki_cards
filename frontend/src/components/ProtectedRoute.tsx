import { ReactNode, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthContext } from '../contexts/AuthContext';

/**
 * Компонент для защиты маршрутов, требующих авторизации
 * Если пользователь не авторизован - редирект на страницу входа
 */
interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuthContext();
  const location = useLocation();

  // Показываем загрузку, пока проверяем авторизацию
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-gradient-to-br from-cyan-400 to-pink-400 rounded-3xl mx-auto flex items-center justify-center animate-pulse">
            <span className="text-3xl">🎴</span>
          </div>
          <p className="text-sm text-gray-500">Загрузка...</p>
        </div>
      </div>
    );
  }

  // Если не авторизован - редирект на страницу входа
  // Сохраняем текущий путь для возврата после входа
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Если авторизован - показываем содержимое
  return <>{children}</>;
}

/**
 * Компонент для публичных маршрутов (login, register)
 * Если пользователь уже авторизован - редирект на главную
 */
interface PublicRouteProps {
  children: ReactNode;
}

export function PublicRoute({ children }: PublicRouteProps) {
  const { isAuthenticated, isLoading } = useAuthContext();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-gradient-to-br from-cyan-400 to-pink-400 rounded-3xl mx-auto flex items-center justify-center animate-pulse">
            <span className="text-3xl">🎴</span>
          </div>
          <p className="text-sm text-gray-500">Загрузка...</p>
        </div>
      </div>
    );
  }

  // Если авторизован - редирект на главную или на страницу откуда пришли
  if (isAuthenticated) {
    const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/';
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
}