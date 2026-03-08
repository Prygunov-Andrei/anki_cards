import apiClient from './api';
import {
  LiterarySource,
  WordContextMedia,
  GenerateContextRequest,
  GenerateBatchContextRequest,
  BatchContextStats,
  JobStatus,
} from '../types/literary-context';
import { API_ENDPOINTS } from '../lib/api-constants';
import { TIMEOUTS } from '@/utils/timeouts';

export const literaryContextService = {
  async getSources(): Promise<LiterarySource[]> {
    const response = await apiClient.get<LiterarySource[]>(API_ENDPOINTS.LITERARY_SOURCES);
    return response.data;
  },

  async generateContext(data: GenerateContextRequest): Promise<WordContextMedia> {
    const response = await apiClient.post<WordContextMedia>(API_ENDPOINTS.LITERARY_GENERATE, data);
    return response.data;
  },

  async generateBatchContext(data: GenerateBatchContextRequest): Promise<BatchContextStats> {
    const response = await apiClient.post<BatchContextStats>(API_ENDPOINTS.LITERARY_GENERATE_BATCH, data);
    return response.data;
  },

  async generateDeckContext(deckId: number, sourceSlug: string): Promise<BatchContextStats> {
    const response = await apiClient.post<BatchContextStats>(
      API_ENDPOINTS.LITERARY_GENERATE_DECK_ASYNC,
      { deck_id: deckId, source_slug: sourceSlug },
      { timeout: TIMEOUTS.API_LONG } // 5 minutes for large decks
    );
    return response.data;
  },

  async getWordContextMedia(wordId: number): Promise<WordContextMedia[]> {
    const response = await apiClient.get<WordContextMedia[]>(API_ENDPOINTS.LITERARY_WORD_MEDIA(wordId));
    return response.data;
  },

  async generateDeckContextAsync(deckId: number, sourceSlug: string): Promise<{ job_id: string }> {
    const response = await apiClient.post<{ job_id: string }>(
      API_ENDPOINTS.LITERARY_GENERATE_DECK_ASYNC,
      { deck_id: deckId, source_slug: sourceSlug },
    );
    return response.data;
  },

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await apiClient.get<JobStatus>(API_ENDPOINTS.LITERARY_JOB_STATUS(jobId));
    return response.data;
  },
};
