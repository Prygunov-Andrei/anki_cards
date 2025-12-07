import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { showError, showWarning } from '../utils/toast-helpers';
import { useTranslation } from '../contexts/LanguageContext';

interface AvatarUploadProps {
  currentAvatar?: string;
  onAvatarChange: (file: File | null) => void;
  onAvatarRemove?: () => void;
}

/**
 * Компонент загрузки аватара с drag-and-drop и предпросмотром
 * iOS 25 стиль
 */
export const AvatarUpload: React.FC<AvatarUploadProps> = ({
  currentAvatar,
  onAvatarChange,
  onAvatarRemove,
}) => {
  const t = useTranslation();
  const [preview, setPreview] = useState<string | null>(currentAvatar || null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Поддерживаемые форматы
  const ALLOWED_FORMATS = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

  /**
   * Синхронизация preview с currentAvatar prop
   */
  useEffect(() => {
    setPreview(currentAvatar || null);
  }, [currentAvatar]);

  /**
   * Валидация файла
   */
  const validateFile = (file: File): boolean => {
    // Проверка формата
    if (!ALLOWED_FORMATS.includes(file.type)) {
      showError(t.errors.unsupportedFormat, {
        description: t.errors.useCorrectFormat,
      });
      return false;
    }

    // Проверка размера
    if (file.size > MAX_FILE_SIZE) {
      showError(t.errors.fileTooLarge, {
        description: t.errors.maxFileSize,
      });
      return false;
    }

    return true;
  };

  /**
   * Обработка выбора файла
   */
  const handleFileSelect = useCallback(
    (file: File) => {
      if (!validateFile(file)) {
        return;
      }

      // Создаем превью
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);

      // Передаем файл наверх
      onAvatarChange(file);
    },
    [onAvatarChange]
  );

  /**
   * Обработчик клика по кнопке загрузки
   */
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  /**
   * Обработчик изменения input
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  /**
   * Обработчик удаления аватара
   */
  const handleRemove = () => {
    setPreview(null);
    onAvatarChange(null);
    if (onAvatarRemove) {
      onAvatarRemove();
    }
    // Очищаем input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  /**
   * Drag and Drop handlers
   */
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  return (
    <div className="space-y-4">
      {/* Превью аватара */}
      <div className="flex items-center justify-center">
        <div className="relative">
          {preview ? (
            <div className="relative h-32 w-32 overflow-hidden rounded-3xl ring-4 ring-gray-200 dark:ring-gray-800">
              <img
                src={preview}
                alt="Avatar preview"
                className="h-full w-full object-cover"
              />
            </div>
          ) : (
            <div className="flex h-32 w-32 items-center justify-center rounded-3xl bg-gradient-to-br from-cyan-400 to-pink-400 text-white ring-4 ring-gray-200 dark:ring-gray-800">
              <ImageIcon className="h-12 w-12 opacity-80" />
            </div>
          )}
        </div>
      </div>

      {/* Drag and Drop зона */}
      <Card
        className={`cursor-pointer transition-all ${
          isDragging
            ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-950/30'
            : 'border-gray-200 hover:border-gray-300 dark:border-gray-800 dark:hover:border-gray-700'
        }`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleUploadClick}
      >
        <div className="flex flex-col items-center justify-center space-y-3 p-6">
          <div
            className={`rounded-full p-3 ${
              isDragging
                ? 'bg-blue-100 dark:bg-blue-900/50'
                : 'bg-gray-100 dark:bg-gray-800'
            }`}
          >
            <Upload
              className={`h-6 w-6 ${
                isDragging
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {isDragging ? t.common.dropFile : t.common.uploadPhoto}
            </p>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {t.common.fileFormats}
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="rounded-xl"
            onClick={(e) => {
              e.stopPropagation();
              handleUploadClick();
            }}
          >
            {t.common.selectFile}
          </Button>
        </div>
      </Card>

      {/* Скрытый input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_FORMATS.join(',')}
        onChange={handleInputChange}
        className="hidden"
      />

      {/* Подсказка для удаления */}
      {preview && (
        <div className="text-center">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleRemove}
            className="text-xs text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
          >
            <X className="mr-1 h-3 w-3" />
            {t.common.removePhoto}
          </Button>
        </div>
      )}
    </div>
  );
};