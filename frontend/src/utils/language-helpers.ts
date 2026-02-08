/**
 * Language Helpers - утилиты для работы с языками
 */

import { SupportedLanguage } from '../types';

/**
 * Маппинг языковых кодов на флаги (эмодзи)
 * Поддерживаются все 7 языков приложения
 */
const languageFlags: Record<string, string> = {
  en: '🇬🇧', // English
  ru: '🇷🇺', // Russian
  es: '🇪🇸', // Spanish
  fr: '🇫🇷', // French
  de: '🇩🇪', // German
  it: '🇮🇹', // Italian
  pt: '🇵🇹', // Portuguese
  tr: '🇹🇷', // Turkish
};

/**
 * Маппинг языковых кодов на русские названия
 */
const languageNames: Record<string, string> = {
  en: 'Английский',
  ru: 'Русский',
  es: 'Испанский',
  fr: 'Французский',
  de: 'Немецкий',
  it: 'Итальянский',
  pt: 'Португальский',
  tr: 'Турецкий',
};

/**
 * Маппинг языковых кодов на английские названия (для бэкенда)
 */
const languageBackendNames: Record<string, string> = {
  en: 'English',
  ru: 'Russian',
  es: 'Spanish',
  fr: 'French',
  de: 'German',
  it: 'Italian',
  pt: 'Portuguese',
  tr: 'Turkish',
};

/**
 * Получить флаг языка по коду
 * @param code - код языка
 * @returns эмодзи флага
 */
export const getLanguageFlag = (code: string | undefined): string => {
  if (!code) {
    return '🌐';
  }
  return languageFlags[code as SupportedLanguage] || '🌐';
};

/**
 * Получить название языка по коду
 * @param code - код языка
 * @returns название языка на русском
 */
export const getLanguageName = (code: string | undefined): string => {
  if (!code) {
    return 'Неизвестный';
  }
  return languageNames[code] || code.toUpperCase();
};

/**
 * Конвертировать код языка в формат бэкенда (English, Russian и т.д.)
 * @param code - код языка (en, ru, es и т.д.)
 * @returns название языка на английском для бэкенда
 */
export const languageCodeToBackend = (code: string): string => {
  return languageBackendNames[code] || code;
};

/**
 * Конвертировать название языка с бэкенда в код (English -> en)
 * @param name - название языка (English, Russian и т.д.)
 * @returns код языка (en, ru, es и т.д.)
 */
export const languageBackendToCode = (name: string): string => {
  const entry = Object.entries(languageBackendNames).find(
    ([_, value]) => value.toLowerCase() === name.toLowerCase()
  );
  return entry ? entry[0] : name.toLowerCase().substring(0, 2);
};

/**
 * Получить полную информацию о языке
 * @param code - код языка
 * @returns объект с флагом и названием
 */
export const getLanguageInfo = (code: string) => {
  return {
    code,
    flag: getLanguageFlag(code),
    name: getLanguageName(code),
  };
};