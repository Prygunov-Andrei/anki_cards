import React, { useState } from 'react';
import { apiService } from '../services/api';
import { CardGenerationRequest, Language, WordMedia } from '../types';

interface GenerateButtonProps {
  words: string[];
  language: Language;
  translations: Record<string, string>;
  deckName: string;
  wordMedia?: Record<string, WordMedia>;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const GenerateButton: React.FC<GenerateButtonProps> = ({
  words,
  language,
  translations,
  deckName,
  wordMedia = {},
  onSuccess,
  onError,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const validateInputs = (): boolean => {
    if (words.length === 0) {
      setError('Добавьте хотя бы одно слово');
      return false;
    }

    if (!deckName.trim()) {
      setError('Введите название колоды');
      return false;
    }

    // Проверяем, что для всех слов есть переводы
    const missingTranslations = words.filter((word) => !translations[word]?.trim());
    if (missingTranslations.length > 0) {
      setError(`Заполните переводы для: ${missingTranslations.join(', ')}`);
      return false;
    }

    return true;
  };

  const downloadFile = async (fileId: string, filename: string) => {
    try {
      const blob = await apiService.downloadCards(fileId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.apkg`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Ошибка при скачивании файла:', err);
      throw new Error('Не удалось скачать файл');
    }
  };

  const handleGenerate = async () => {
    setError('');

    if (!validateInputs()) {
      if (onError) {
        onError(error);
      }
      return;
    }

    setIsLoading(true);

    try {
      // Подготавливаем медиафайлы
      const audioFiles: Record<string, string> = {};
      const imageFiles: Record<string, string> = {};

      console.log('GenerateButton: words:', words);
      console.log('GenerateButton: wordMedia:', wordMedia);

      words.forEach((word) => {
        const media = wordMedia[word];
        console.log(`GenerateButton: обработка слова "${word}":`, media);
        console.log(`GenerateButton: media?.imagePath для "${word}":`, media?.imagePath);
        console.log(`GenerateButton: media?.audioPath для "${word}":`, media?.audioPath);
        if (media) {
          // Проверяем imagePath - может быть строкой или undefined
          if (media.imagePath && typeof media.imagePath === 'string' && media.imagePath.trim() !== '') {
            imageFiles[word] = media.imagePath;
            console.log(`GenerateButton: ✅ добавлено изображение для "${word}":`, media.imagePath);
          } else {
            console.warn(`GenerateButton: ⚠️ imagePath пустой или невалидный для "${word}":`, media.imagePath);
          }
          // Проверяем audioPath - может быть строкой или undefined
          if (media.audioPath && typeof media.audioPath === 'string' && media.audioPath.trim() !== '') {
            audioFiles[word] = media.audioPath;
            console.log(`GenerateButton: ✅ добавлено аудио для "${word}":`, media.audioPath);
          } else {
            console.warn(`GenerateButton: ⚠️ audioPath пустой или невалидный для "${word}":`, media.audioPath);
          }
        } else {
          console.warn(`GenerateButton: ❌ медиа не найдено для слова "${word}"`);
        }
      });

      console.log('GenerateButton: audioFiles:', audioFiles);
      console.log('GenerateButton: imageFiles:', imageFiles);

      const requestData: CardGenerationRequest = {
        words: words.join(', '),
        language,
        translations,
        deck_name: deckName,
        ...(Object.keys(audioFiles).length > 0 && { audio_files: audioFiles }),
        ...(Object.keys(imageFiles).length > 0 && { image_files: imageFiles }),
      };

      console.log('GenerateButton: requestData:', requestData);

      const response = await apiService.generateCards(requestData);
      await downloadFile(response.file_id, response.deck_name);

      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.error ||
        err.response?.data?.message ||
        err.message ||
        'Ошибка при генерации карточек';
      setError(errorMessage);
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      <button
        onClick={handleGenerate}
        disabled={isLoading}
        className="w-full bg-green-600 text-white py-3 px-6 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium text-lg"
      >
        {isLoading ? (
          <span className="flex items-center justify-center">
            <svg
              className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Генерация...
          </span>
        ) : (
          'Сгенерировать карточки'
        )}
      </button>
    </div>
  );
};

