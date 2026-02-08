/**
 * Base URL backend API.
 * В продакшене: пустая строка (запросы на тот же домен).
 * В разработке: VITE_API_BASE_URL из .env или http://localhost:8000.
 */
const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env?.VITE_API_BASE_URL;
  if (envUrl && envUrl.startsWith('/')) {
    return '';
  }
  if (envUrl) {
    return envUrl.replace(/\/$/, '');
  }
  if (import.meta.env?.DEV) {
    return 'http://localhost:8000';
  }
  return '';
};

const API_BASE_URL = getApiBaseUrl();

/**
 * Преобразует относительный URL в абсолютный
 */
export const getAbsoluteUrl = (url: string | null | undefined): string | null => {
  if (!url) {
    return null;
  }

  if (url.startsWith('http://') || url.startsWith('https://')) {
    if (url.includes('%3A') || url.includes('%3a')) {
      const decodedUrl = decodeURIComponent(url);
      const match = decodedUrl.match(/https?:\/\/[^\/]+\/media\/(https?:\/\/.+)$/);
      if (match) return match[1];
    }
    return url;
  }

  if (url.includes('%3A') || url.includes('%3a')) {
    let decodedUrl = decodeURIComponent(url);
    decodedUrl = decodedUrl.replace(/(https?):\/([^\/])/g, '$1://$2');
    const match = decodedUrl.match(/(https?:\/\/.+)$/);
    if (match) return match[1];
  }

  if (url.startsWith('/media/') || url.startsWith('/static/')) {
    return `${API_BASE_URL}${url}`;
  }
  if (url.startsWith('media/') || url.startsWith('static/')) {
    return `${API_BASE_URL}/${url}`;
  }

  return `${API_BASE_URL}${url.startsWith('/') ? url : `/${url}`}`;
};

export const getUserAvatarUrl = (avatarUrl: string | null | undefined): string | null => {
  return getAbsoluteUrl(avatarUrl);
};

export const getCardImageUrl = (imageUrl: string | null | undefined): string | null => {
  return getAbsoluteUrl(imageUrl);
};

export const getAudioUrl = (audioUrl: string | null | undefined): string | null => {
  return getAbsoluteUrl(audioUrl);
};

/**
 * Преобразует абсолютный URL в относительный путь для отправки на бекенд
 */
export const getRelativePath = (url: string | null | undefined): string | null => {
  if (!url) return null;
  if (!url.startsWith('http://') && !url.startsWith('https://')) return url;
  try {
    const urlObj = new URL(url);
    return urlObj.pathname;
  } catch {
    return null;
  }
};
