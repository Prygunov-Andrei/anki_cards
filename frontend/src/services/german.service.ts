import api from './api';
import { API_ENDPOINTS } from '../lib/api-constants';
import { logger } from '@/utils/logger';

/**
 * German language processing service — article addition, capitalization.
 * Extracted from deck.service.ts.
 */

export async function processGermanWords(words: string[]): Promise<Record<string, string>> {
  const results: Record<string, string> = {};

  for (const word of words) {
    try {
      const response = await api.post<{ processed_word: string }>(
        API_ENDPOINTS.CARDS_PROCESS_GERMAN,
        { word }
      );
      const processedWord = typeof response.data === 'string'
        ? response.data
        : response.data.processed_word || word;
      results[word] = processedWord;
    } catch (error) {
      logger.error(`Error processing word "${word}":`, error);
      results[word] = word;
    }
  }

  return results;
}

export async function processGermanWord(word: string): Promise<{ processed_word: string }> {
  try {
    const response = await api.post<{ processed_word: string }>(
      API_ENDPOINTS.CARDS_PROCESS_GERMAN,
      { word }
    );
    const processedWord = typeof response.data === 'string'
      ? response.data
      : response.data.processed_word || word;
    return { processed_word: processedWord };
  } catch (error) {
    logger.error(`Error processing German word "${word}":`, error);
    return { processed_word: word };
  }
}

export const germanService = {
  processGermanWords,
  processGermanWord,
};
