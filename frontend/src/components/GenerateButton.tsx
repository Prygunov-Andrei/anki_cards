import React, { useState } from 'react';
import { apiService } from '../services/api';
import { CardGenerationRequest, Language } from '../types';

interface GenerateButtonProps {
  words: string[];
  language: Language;
  translations: Record<string, string>;
  deckName: string;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const GenerateButton: React.FC<GenerateButtonProps> = ({
  words,
  language,
  translations,
  deckName,
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
      const requestData: CardGenerationRequest = {
        words: words.join(', '),
        language,
        translations,
        deck_name: deckName,
      };

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

