/**
 * Base URL backend API (через ngrok - постоянный домен)
 */

const API_BASE_URL = 'https://get-anki.fan.ngrok.app';

/**
 * Преобразует относительный URL в абсолютный
 * Django часто возвращает относительные пути для медиа-файлов
 * 
 * @param url - URL который может быть относительным или абсолютным
 * @returns Абсолютный URL
 */
export const getAbsoluteUrl = (url: string | null | undefined): string | null => {
  if (!url) {
    return null;
  }

  // Если URL уже абсолютный (начинается с http:// или https://), проверяем на двойное кодирование
  if (url.startsWith('http://') || url.startsWith('https://')) {
    // Проверяем, не содержит ли URL закодированный протокол внутри
    if (url.includes('%3A') || url.includes('%3a')) {
      const decodedUrl = decodeURIComponent(url);
      // Ищем второй абсолютный URL внутри
      const match = decodedUrl.match(/https?:\/\/[^\/]+\/media\/(https?:\/\/.+)$/);
      if (match) {
        return match[1];
      }
    }
    return url;
  }

  // КРИТИЧНО: Проверяем закодированный абсолютный URL в относительном пути
  // Например: /media/https%3A/get-anki.fan.ngrok.app/media/images/xxx.jpg
  if (url.includes('%3A') || url.includes('%3a')) {
    // Декодируем URL
    let decodedUrl = decodeURIComponent(url);
    
    // ИСПРАВЛЕНИЕ: После декодирования может получиться https:/ вместо https://
    // Исправляем одинарный слэш после протокола
    decodedUrl = decodedUrl.replace(/(https?):\/([^\/])/g, '$1://$2');
    
    // Извлекаем абсолютный URL (начинается с http:// или https://)
    const match = decodedUrl.match(/(https?:\/\/.+)$/);
    if (match) {
      return match[1];
    }
  }

  // Если URL начинается с /media/ или /static/
  if (url.startsWith('/media/') || url.startsWith('/static/')) {
    return `${API_BASE_URL}${url}`;
  }

  // Если URL начинается с media/ или static/ (без /)
  if (url.startsWith('media/') || url.startsWith('static/')) {
    return `${API_BASE_URL}/${url}`;
  }

  // В остальных случаях добавляем API_BASE_URL
  return `${API_BASE_URL}${url.startsWith('/') ? url : `/${url}`}`;
};

/**
 * Получить URL аватара пользователя
 * Возвращает абсолютный URL или null
 */
export const getUserAvatarUrl = (avatarUrl: string | null | undefined): string | null => {
  return getAbsoluteUrl(avatarUrl);
};

/**
 * Получить URL изображения карточки
 */
export const getCardImageUrl = (imageUrl: string | null | undefined): string | null => {
  return getAbsoluteUrl(imageUrl);
};

/**
 * Получить URL аудио файла
 */
export const getAudioUrl = (audioUrl: string | null | undefined): string | null => {
  return getAbsoluteUrl(audioUrl);
};

/**
 * Преобразует абсолютный URL в относительный путь для отправки на бекенд
 * 
 * @param url - Абсолютный URL (например https://get-anki.fan.ngrok.app/media/images/xxx.jpg)
 * @returns Относительный путь (например /media/images/xxx.jpg)
 */
export const getRelativePath = (url: string | null | undefined): string | null => {
  if (!url) {
    return null;
  }

  // Если URL уже относительный, возвращаем как есть
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return url;
  }

  // Извлекаем путь после доменного имени
  // https://get-anki.fan.ngrok.app/media/images/xxx.jpg -> /media/images/xxx.jpg
  try {
    const urlObj = new URL(url);
    return urlObj.pathname;
  } catch (error) {
    console.error('Error parsing URL:', url, error);
    return null;
  }
};