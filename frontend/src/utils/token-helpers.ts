/**
 * Утилиты для работы с токенами
 */

/**
 * Форматирование баланса токенов с поддержкой дробных значений
 */
export const formatTokenBalance = (value: number): string => {
  // Если баланс целый, показываем без десятичных знаков
  if (value % 1 === 0) {
    return value.toLocaleString('ru-RU');
  }
  // Если дробный, показываем с одним десятичным знаком
  return value.toLocaleString('ru-RU', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
};

/**
 * Склонение слова "токен" в зависимости от числа
 * Поддерживает дробные значения
 */
export const pluralizeTokens = (count: number): string => {
  // Для дробных чисел всегда используем "токена"
  if (count % 1 !== 0) {
    return 'токена';
  }

  // Для целых чисел используем обычное склонение
  const lastDigit = count % 10;
  const lastTwoDigits = count % 100;

  if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
    return 'токенов';
  }

  if (lastDigit === 1) {
    return 'токен';
  }

  if (lastDigit >= 2 && lastDigit <= 4) {
    return 'токена';
  }

  return 'токенов';
};

/**
 * Форматирование токенов с текстом (например, "5.5 токена" или "10 токенов")
 */
export const formatTokensWithText = (count: number): string => {
  return `${formatTokenBalance(count)} ${pluralizeTokens(count)}`;
};

/**
 * Получить стоимость генерации в зависимости от провайдера и модели
 */
export const getGenerationCost = (
  provider: 'openai' | 'gemini',
  geminiModel?: 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'
): number => {
  if (provider === 'openai') {
    return 1; // DALL-E 3: 1 токен
  }

  if (provider === 'gemini') {
    if (geminiModel === 'gemini-2.5-flash-image') {
      return 0.5; // Gemini Flash: 0.5 токена
    }
    if (geminiModel === 'nano-banana-pro-preview') {
      return 1; // Nano Banana Pro: 1 токен
    }
    // Дефолтная модель
    return 0.5;
  }

  return 1; // Дефолт
};

/**
 * Получить общую стоимость генерации медиа для колоды
 */
export const getTotalMediaCost = (
  wordsCount: number,
  generateImages: boolean,
  generateAudio: boolean,
  provider: 'openai' | 'gemini' = 'openai',
  geminiModel?: 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'
): number => {
  let cost = 0;

  // Стоимость изображений
  if (generateImages) {
    const imageCost = getGenerationCost(provider, geminiModel);
    cost += imageCost * wordsCount;
  }

  // Стоимость аудио (всегда 0 токенов, бесплатно)
  if (generateAudio) {
    cost += 0;
  }

  return cost;
};