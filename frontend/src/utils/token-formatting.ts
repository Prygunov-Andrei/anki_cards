/**
 * Локализованные утилиты для форматирования токенов
 */

import { TranslationKeys } from '../locales/ru';

/**
 * Форматирование баланса токенов с поддержкой дробных значений
 */
export const formatTokenBalance = (value: number, locale: string = 'en-US'): string => {
  // Если баланс целый, показываем без десятичных знаков
  if (value % 1 === 0) {
    return value.toLocaleString(locale);
  }
  // Если дробный, показываем с одним десятичным знаком
  return value.toLocaleString(locale, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
};

/**
 * Склонение слова "токен" в зависимости от числа (с локализацией)
 * Поддерживает дробные значения
 */
export const pluralizeTokens = (count: number, t: TranslationKeys, nativeLang: string): string => {
  // Для дробных чисел
  if (count % 1 !== 0) {
    // В английском и других языках просто используем множественное число
    if (nativeLang === 'en' || nativeLang === 'de' || nativeLang === 'es' || 
        nativeLang === 'fr' || nativeLang === 'it' || nativeLang === 'pt') {
      return t.common.tokens;
    }
    // Для русского используем "токена" для дробных
    return t.common.tokens;
  }

  // Для целых чисел
  const lastDigit = count % 10;
  const lastTwoDigits = count % 100;

  // Русская плюрализация
  if (nativeLang === 'ru') {
    if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
      return t.common.tokensMany;
    }
    if (lastDigit === 1) {
      return t.common.token;
    }
    if (lastDigit >= 2 && lastDigit <= 4) {
      return t.common.tokens;
    }
    return t.common.tokensMany;
  }

  // Английская и другие европейские языки
  return count === 1 ? t.common.token : t.common.tokens;
};

/**
 * Форматирование токенов с текстом (например, "5.5 tokens" или "10 токенов")
 */
export const formatTokensWithText = (
  count: number, 
  t: TranslationKeys,
  nativeLang: string = 'en'
): string => {
  const locale = nativeLang === 'ru' ? 'ru-RU' : 'en-US';
  return `${formatTokenBalance(count, locale)} ${pluralizeTokens(count, t, nativeLang)}`;
};
