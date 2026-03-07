import apiClient from './api';
import { API_ENDPOINTS } from '../lib/api-constants';

export interface LiteraryTextListItem {
  slug: string;
  title: string;
  year: number | null;
  word_count: number;
  sort_order: number;
  languages: string[];
}

export interface LiteraryTextDetail {
  slug: string;
  title: string;
  language: string;
  full_text: string;
  year: number | null;
  word_count: number;
  sort_order: number;
}

export interface WordFromReaderResult {
  word: {
    id: number;
    original_word: string;
    translation: string;
    is_new: boolean;
  };
  context_media: {
    hint_text: string;
    sentences: string[];
    match_method: string;
    is_fallback: boolean;
  } | null;
}

export const libraryService = {
  async getTexts(sourceSlug: string, params?: { search?: string; sort?: string }): Promise<LiteraryTextListItem[]> {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.set('search', params.search);
    if (params?.sort) queryParams.set('sort', params.sort);
    const qs = queryParams.toString();
    const url = API_ENDPOINTS.LITERARY_TEXTS(sourceSlug) + (qs ? `?${qs}` : '');
    const { data } = await apiClient.get(url);
    return data;
  },

  async getText(sourceSlug: string, textSlug: string, language: string = 'de'): Promise<LiteraryTextDetail> {
    const { data } = await apiClient.get(
      API_ENDPOINTS.LITERARY_TEXT_DETAIL(sourceSlug, textSlug) + `?language=${language}`
    );
    return data;
  },

  async addWordFromReader(originalWord: string, sourceSlug?: string, language: string = 'de'): Promise<WordFromReaderResult> {
    const { data } = await apiClient.post(API_ENDPOINTS.LITERARY_WORD_FROM_READER, {
      original_word: originalWord,
      source_slug: sourceSlug || '',
      language,
    });
    return data;
  },
};
