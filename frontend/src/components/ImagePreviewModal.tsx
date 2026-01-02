import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import { getAbsoluteUrl } from '../utils/url-helpers';
import { displayWord } from '../utils/helpers';

interface ImagePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string;
  word: string;
  translation?: string;
}

/**
 * Модальное окно для предпросмотра изображений
 * iOS 25 стиль, оптимизирован для мобильных устройств
 */
export const ImagePreviewModal: React.FC<ImagePreviewModalProps> = ({
  isOpen,
  onClose,
  imageUrl,
  word,
  translation,
}) => {
  // Преобразуем относительный URL в абсолютный
  const absoluteImageUrl = getAbsoluteUrl(imageUrl) || imageUrl;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl p-0">
        {/* Заголовок */}
        <DialogHeader className="border-b p-4">
          <DialogTitle className="text-xl">{displayWord(word)}</DialogTitle>
          <DialogDescription className="sr-only">
            Предпросмотр изображения для слова {displayWord(word)}
          </DialogDescription>
          {translation && (
            <p className="mt-1 text-sm text-muted-foreground">
              {translation}
            </p>
          )}
        </DialogHeader>

        {/* Изображение */}
        <div className="relative flex items-center justify-center bg-gradient-to-br from-cyan-50 to-pink-50 p-8">
          <img
            src={absoluteImageUrl}
            alt={displayWord(word)}
            className="max-h-[70vh] w-full rounded-lg object-contain shadow-lg"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5Y2EzYWYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBub3QgZm91bmQ8L3RleHQ+PC9zdmc+';
            }}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};