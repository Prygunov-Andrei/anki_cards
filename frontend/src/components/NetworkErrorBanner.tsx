import React from 'react';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { WifiOff, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';

interface NetworkErrorBannerProps {
  onRetry?: () => void;
}

/**
 * Баннер с информацией об ошибке подключения к серверу
 */
export const NetworkErrorBanner: React.FC<NetworkErrorBannerProps> = ({ onRetry }) => {
  return (
    <Alert variant="destructive" className="mb-6">
      <WifiOff className="h-4 w-4" />
      <AlertTitle>Нет подключения к серверу</AlertTitle>
      <AlertDescription className="mt-2">
        <div className="space-y-2">
          <p>Не удалось подключиться к backend серверу. Проверьте:</p>
          <ul className="ml-4 list-disc space-y-1 text-sm">
            <li>Backend сервер запущен (Django)</li>
            <li>Backend доступен по адресу из .env (для разработки — localhost:8000)</li>
            <li>URL корректный в настройках</li>
          </ul>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="mt-3"
            >
              <RefreshCw className="mr-2 h-3 w-3" />
              Попробовать снова
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
};