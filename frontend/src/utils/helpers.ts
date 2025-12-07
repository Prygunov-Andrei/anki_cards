import { SUPPORTED_LANGUAGES } from './constants';
import { SupportedLanguage } from '../types';

/**
 * Вспомогательные функции
 */

/**
 * Форматирование даты
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInHours = diffInMs / (1000 * 60 * 60);

  if (diffInHours < 24) {
    return 'Сегодня';
  } else if (diffInHours < 48) {
    return 'Вчера';
  } else {
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  }
};

/**
 * Получить название языка по коду
 */
export const getLanguageName = (code: SupportedLanguage): string => {
  const language = SUPPORTED_LANGUAGES.find(lang => lang.code === code);
  return language?.name || code;
};

/**
 * Получить флаг языка по коду
 */
export const getLanguageFlag = (code: SupportedLanguage): string => {
  const language = SUPPORTED_LANGUAGES.find(lang => lang.code === code);
  return language?.flag || '🌐';
};

/**
 * Скачать файл
 */
export const downloadFile = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Получить инициалы пользователя
 */
export const getInitials = (firstName: string, lastName: string): string => {
  const firstInitial = firstName?.charAt(0) || '';
  const lastInitial = lastName?.charAt(0) || '';
  return (firstInitial + lastInitial).toUpperCase();
};

/**
 * Валидация email
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Генерация случайного цвета для аватара
 */
export const getAvatarColor = (id: number): string => {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
    '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
  ];
  return colors[id % colors.length];
};

/**
 * Обрезка текста с добавлением многоточия
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};
