import { describe, it, expect, vi, beforeEach } from 'vitest';
import { literaryContextService } from '../literary-context.service';

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import apiClient from '../api';

describe('literaryContextService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getSources', () => {
    it('fetches active sources', async () => {
      const mockData = [{ slug: 'chekhov', name: 'Chekhov' }];
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockData } as any);

      const result = await literaryContextService.getSources();

      expect(apiClient.get).toHaveBeenCalledWith('/api/literary-context/sources/');
      expect(result).toEqual(mockData);
    });
  });

  describe('generateContext', () => {
    it('posts generate request', async () => {
      const mockResponse = { id: 1, match_method: 'keyword' };
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse } as any);

      const result = await literaryContextService.generateContext({
        word_id: 42,
        source_slug: 'chekhov',
      });

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/literary-context/generate/',
        { word_id: 42, source_slug: 'chekhov' },
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('generateBatchContext', () => {
    it('posts batch generate request', async () => {
      const mockStats = { total: 3, generated: 2, skipped: 1, fallback: 0, errors: 0 };
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockStats } as any);

      const result = await literaryContextService.generateBatchContext({
        word_ids: [1, 2, 3],
        source_slug: 'chekhov',
      });

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/literary-context/generate-batch/',
        { word_ids: [1, 2, 3], source_slug: 'chekhov' },
      );
      expect(result).toEqual(mockStats);
    });
  });

  describe('getWordContextMedia', () => {
    it('fetches word context media', async () => {
      const mockMedia = [{ id: 1, hint_text: 'A hint' }];
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockMedia } as any);

      const result = await literaryContextService.getWordContextMedia(42);

      expect(apiClient.get).toHaveBeenCalledWith('/api/literary-context/word/42/media/');
      expect(result).toEqual(mockMedia);
    });
  });

  describe('generateDeckContextAsync', () => {
    it('posts async job request and returns job_id', async () => {
      const mockResponse = { job_id: 'abc-123-def' };
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse } as any);

      const result = await literaryContextService.generateDeckContextAsync(5, 'chekhov');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/literary-context/generate-deck-context-async/',
        { deck_id: 5, source_slug: 'chekhov' },
      );
      expect(result).toEqual({ job_id: 'abc-123-def' });
    });
  });

  describe('getJobStatus', () => {
    it('fetches job status by id', async () => {
      const mockStatus = {
        job_id: 'abc-123',
        status: 'completed',
        progress: 100,
        stats: { total: 10, generated: 8, skipped: 2, fallback: 1, errors: 0 },
      };
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockStatus } as any);

      const result = await literaryContextService.getJobStatus('abc-123');

      expect(apiClient.get).toHaveBeenCalledWith('/api/literary-context/job/abc-123/status/');
      expect(result).toEqual(mockStatus);
    });

    it('returns pending status for in-progress job', async () => {
      const mockStatus = {
        job_id: 'xyz-456',
        status: 'running',
        progress: 45,
        stats: null,
      };
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockStatus } as any);

      const result = await literaryContextService.getJobStatus('xyz-456');

      expect(result.status).toBe('running');
      expect(result.progress).toBe(45);
    });
  });
});
