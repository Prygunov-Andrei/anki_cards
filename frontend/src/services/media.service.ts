import api from './api';
import { API_ENDPOINTS } from '../lib/api-constants';
import { TIMEOUTS } from '@/utils/timeouts';

/**
 * Media Service — image/audio generation, editing, word media updates.
 * Extracted from deck.service.ts.
 */

export async function generateImage(
  data: {
    word: string;
    translation: string;
    language: string;
    image_style: 'minimalistic' | 'balanced' | 'creative';
    provider?: 'openai' | 'gemini';
    gemini_model?: 'gemini-2.5-flash-image' | 'gemini-3.1-flash-image-preview';
    word_id?: number;
  },
  signal?: AbortSignal
): Promise<{ image_url: string }> {
  const response = await api.post<{ image_url: string }>(
    API_ENDPOINTS.MEDIA_GENERATE_IMAGE,
    data,
    { timeout: TIMEOUTS.API_IMAGE, signal }
  );
  return response.data;
}

export async function generateAudio(
  data: {
    word: string;
    language: string;
    provider?: 'openai' | 'gtts';
    word_id?: number;
  },
  signal?: AbortSignal
): Promise<{ audio_url: string }> {
  const response = await api.post<{ audio_url: string }>(
    API_ENDPOINTS.MEDIA_GENERATE_AUDIO,
    data,
    { timeout: TIMEOUTS.API_MEDIUM, signal }
  );
  return response.data;
}

export async function editImage(
  data: { word_id: number; mixin: string },
  signal?: AbortSignal
): Promise<{ image_url: string; mixin: string; word_id: number }> {
  const response = await api.post<{ image_url: string; mixin: string; word_id: number }>(
    API_ENDPOINTS.MEDIA_EDIT_IMAGE,
    data,
    { timeout: TIMEOUTS.API_IMAGE, signal }
  );
  return response.data;
}

export async function updateWordMedia(
  deckId: number,
  wordId: number,
  data: {
    original_word?: string;
    translation?: string;
    image_file?: string | null;
    audio_file?: string | null;
  }
): Promise<{
  id: number;
  original_word: string;
  translation: string;
  language: string;
  image_file: string | null;
  audio_file: string | null;
  updated_fields: string[];
}> {
  const response = await api.patch(API_ENDPOINTS.DECK_WORD(deckId, wordId), data);
  return response.data;
}

export async function updateWordAIContent(
  deckId: number,
  wordId: number,
  data: {
    etymology?: string;
    hint_text?: string;
    hint_audio?: string | null;
    sentences?: Array<{
      id?: number;
      sentence: string;
      translation: string;
      audio_file?: string | null;
    }>;
    part_of_speech?: string;
    notes?: string;
  }
): Promise<unknown> {
  const response = await api.patch(API_ENDPOINTS.DECK_WORD(deckId, wordId), data);
  return response.data;
}

export async function extractWordsFromPhoto(data: {
  image: File;
  target_lang: string;
  source_lang: string;
}): Promise<{ words: string[] }> {
  const formData = new FormData();
  formData.append('image', data.image);
  formData.append('target_lang', data.target_lang);
  formData.append('source_lang', data.source_lang);

  const response = await api.post<{ words: string[] }>(
    API_ENDPOINTS.EXTRACT_WORDS_FROM_PHOTO,
    formData,
    {
      headers: { 'Content-Type': undefined },
      timeout: TIMEOUTS.API_MEDIUM,
    }
  );
  return response.data;
}

export const mediaService = {
  generateImage,
  generateAudio,
  editImage,
  updateWordMedia,
  updateWordAIContent,
  extractWordsFromPhoto,
};
