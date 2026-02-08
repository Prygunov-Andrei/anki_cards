import { Language } from '../types';

/**
 * Константы приложения
 */

// Поддерживаемые языки
export const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷' },
  { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
];

// Уровни сложности
export const DIFFICULTY_LEVELS = [
  { value: 'beginner', label: 'Начинающий', description: 'Простые базовые слова' },
  { value: 'intermediate', label: 'Средний', description: 'Распространенные слова' },
  { value: 'advanced', label: 'Продвинутый', description: 'Сложная лексика' },
] as const;

// Количество слов в колоде
export const WORDS_COUNT_OPTIONS = [10, 20, 30, 50, 100];

// Темы оформления
export const THEMES = ['light', 'dark'] as const;

// Режимы работы
export const MODES = ['simple', 'advanced'] as const;

// Локальное хранилище ключи
export const STORAGE_KEYS = {
  TOKEN: 'token',
  USER: 'user',
  THEME: 'theme',
  LANGUAGE: 'language',
} as const;
