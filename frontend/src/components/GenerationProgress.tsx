import React, { useEffect, useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Loader2, ImageIcon, Volume2, Package, X, AlertTriangle } from 'lucide-react';

export type GenerationStatus = 'idle' | 'generating_images' | 'generating_audio' | 'creating_deck' | 'complete';

interface GenerationProgressProps {
  status: GenerationStatus;
  current: number;
  total: number;
  currentWord?: string;
  onCancel?: () => void; // Callback для отмены генерации
}

/**
 * Компонент GenerationProgress - отображение прогресса генерации медиа
 * iOS 25 стиль, анимированный прогресс-бар
 */
export const GenerationProgress: React.FC<GenerationProgressProps> = ({
  status,
  current,
  total,
  currentWord,
  onCancel,
}) => {
  if (status === 'idle') return null;

  // Вычисляем процент завершения
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

  // Определяем текст и иконку в зависимости от статуса
  const getStatusInfo = () => {
    switch (status) {
      case 'generating_images':
        return {
          icon: <ImageIcon className="h-5 w-5 text-cyan-500" />,
          title: 'Генерация изображений',
          description: currentWord 
            ? `Создаём изображение для "${currentWord}"...`
            : 'Подготовка изображений...',
          color: 'from-cyan-500 to-blue-500',
        };
      case 'generating_audio':
        return {
          icon: <Volume2 className="h-5 w-5 text-pink-500" />,
          title: 'Генерация аудио',
          description: currentWord
            ? `Создаём аудио для "${currentWord}"...`
            : 'Подготовка аудиофайлов...',
          color: 'from-pink-500 to-rose-500',
        };
      case 'creating_deck':
        return {
          icon: <Package className="h-5 w-5 text-yellow-500" />,
          title: 'Создание колоды',
          description: 'Собираем .apkg файл с медиа...',
          color: 'from-yellow-500 to-orange-500',
        };
      case 'complete':
        return {
          icon: <Package className="h-5 w-5 text-green-500" />,
          title: 'Готово!',
          description: 'Колода успешно создана',
          color: 'from-green-500 to-emerald-500',
        };
      default:
        return {
          icon: <Loader2 className="h-5 w-5 animate-spin" />,
          title: 'Генерация...',
          description: 'Обрабатываем...',
          color: 'from-primary to-primary',
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Заголовок с иконкой */}
        <div className="flex items-center gap-3">
          <div className={`rounded-full bg-gradient-to-r ${statusInfo.color} p-2`}>
            {statusInfo.icon}
          </div>
          <div className="flex-1">
            <h3 className="font-semibold">{statusInfo.title}</h3>
            <p className="text-sm text-muted-foreground">
              {statusInfo.description}
            </p>
          </div>
        </div>

        {/* Прогресс-бар */}
        {status !== 'complete' && (
          <div className="space-y-2">
            <Progress value={percentage} className="h-2" />
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {current} из {total}
              </span>
              <span className="font-medium">{percentage}%</span>
            </div>
          </div>
        )}

        {/* Информационное сообщение */}
        {status === 'generating_images' || status === 'generating_audio' ? (
          <div className="rounded-lg bg-muted/50 p-3 text-sm text-muted-foreground">
            <p>
              ⏱️ Генерация {status === 'generating_images' ? 'изображений' : 'аудио'} может занять{' '}
              {status === 'generating_images' ? '3-10' : '2-3'} секунд на слово
            </p>
          </div>
        ) : null}

        {/* Анимированные точки загрузки */}
        {status !== 'complete' && (
          <div className="flex items-center justify-center gap-1">
            <div
              className="h-2 w-2 animate-bounce rounded-full bg-gradient-to-r from-cyan-500 to-blue-500"
              style={{ animationDelay: '0ms' }}
            />
            <div
              className="h-2 w-2 animate-bounce rounded-full bg-gradient-to-r from-pink-500 to-rose-500"
              style={{ animationDelay: '150ms' }}
            />
            <div
              className="h-2 w-2 animate-bounce rounded-full bg-gradient-to-r from-yellow-500 to-orange-500"
              style={{ animationDelay: '300ms' }}
            />
          </div>
        )}

        {/* Кнопка отмены */}
        {status !== 'complete' && onCancel && (
          <div className="flex justify-end">
            <Button
              variant="destructive"
              size="sm"
              onClick={onCancel}
            >
              <X className="h-4 w-4 mr-2" />
              Отменить
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
};