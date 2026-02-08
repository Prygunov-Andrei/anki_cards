import React from 'react';
import { Header } from './Header';
import { useNotifications } from '@/hooks/useNotifications';
import { useAuthContext } from '@/contexts/AuthContext';

interface LayoutProps {
  children: React.ReactNode;
}

/**
 * Компонент Layout - общий каркас приложения
 * Включает Header и основной контент.
 * Запускает периодическую проверку уведомлений.
 */
export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isAuthenticated } = useAuthContext();
  useNotifications(isAuthenticated);

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 dark:bg-gray-950">
      <Header />
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
};