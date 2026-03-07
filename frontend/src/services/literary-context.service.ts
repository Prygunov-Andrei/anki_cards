import apiClient from './api';
import {
  LiterarySource,
  WordContextMedia,
  GenerateContextRequest,
  GenerateBatchContextRequest,
  BatchContextStats,
} from '../types/literary-context';

const BASE = '/api/literary-context';

export const literaryContextService = {
  async getSources(): Promise<LiterarySource[]> {
    const response = await apiClient.get<LiterarySource[]>(`${BASE}/sources/`);
    return response.data;
  },

  async generateContext(data: GenerateContextRequest): Promise<WordContextMedia> {
    const response = await apiClient.post<WordContextMedia>(`${BASE}/generate/`, data);
    return response.data;
  },

  async generateBatchContext(data: GenerateBatchContextRequest): Promise<BatchContextStats> {
    const response = await apiClient.post<BatchContextStats>(`${BASE}/generate-batch/`, data);
    return response.data;
  },

  async getWordContextMedia(wordId: number): Promise<WordContextMedia[]> {
    const response = await apiClient.get<WordContextMedia[]>(`${BASE}/word/${wordId}/media/`);
    return response.data;
  },
};
