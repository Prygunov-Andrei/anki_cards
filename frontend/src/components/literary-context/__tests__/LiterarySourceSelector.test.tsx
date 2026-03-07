import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LiterarySourceSelector } from '../LiterarySourceSelector';

const mockSources = [
  {
    slug: 'chekhov',
    name: 'Chekhov Stories',
    description: 'Short stories',
    cover: null,
    available_languages: ['ru', 'de'],
    is_active: true,
  },
  {
    slug: 'bible',
    name: 'Bible',
    description: 'Biblical texts',
    cover: '/media/bible.jpg',
    available_languages: ['ru', 'de', 'en'],
    is_active: true,
  },
];

vi.mock('../../../services/literary-context.service', () => ({
  literaryContextService: {
    getSources: vi.fn(),
  },
}));

vi.mock('../../../services/api', () => ({
  default: {
    patch: vi.fn(),
  },
}));

vi.mock('sonner@2.0.3', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

import { literaryContextService } from '../../../services/literary-context.service';
import apiClient from '../../../services/api';
import { toast } from 'sonner@2.0.3';

describe('LiterarySourceSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading skeleton initially', () => {
    vi.mocked(literaryContextService.getSources).mockReturnValue(
      new Promise(() => {}) // never resolves
    );
    const { container } = render(
      <LiterarySourceSelector activeSource={null} onSourceChange={vi.fn()} />
    );
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders sources after loading', async () => {
    vi.mocked(literaryContextService.getSources).mockResolvedValueOnce(mockSources);

    render(
      <LiterarySourceSelector activeSource={null} onSourceChange={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText('Chekhov Stories')).toBeInTheDocument();
      expect(screen.getByText('Bible')).toBeInTheDocument();
      expect(screen.getByText('Standard')).toBeInTheDocument();
    });
  });

  it('returns null when no sources available', async () => {
    vi.mocked(literaryContextService.getSources).mockResolvedValueOnce([]);

    const { container } = render(
      <LiterarySourceSelector activeSource={null} onSourceChange={vi.fn()} />
    );

    await waitFor(() => {
      expect(container.querySelector('.animate-pulse')).not.toBeInTheDocument();
    });
    // Should render nothing
    expect(container.innerHTML).toBe('');
  });

  it('calls onSourceChange when a source is selected', async () => {
    vi.mocked(literaryContextService.getSources).mockResolvedValueOnce(mockSources);
    vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: {} } as any);

    const onSourceChange = vi.fn();
    render(
      <LiterarySourceSelector activeSource={null} onSourceChange={onSourceChange} />
    );

    await waitFor(() => {
      expect(screen.getByText('Chekhov Stories')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Chekhov Stories'));

    await waitFor(() => {
      expect(apiClient.patch).toHaveBeenCalled();
      expect(onSourceChange).toHaveBeenCalledWith('chekhov');
      expect(toast.success).toHaveBeenCalled();
    });
  });

  it('switches to Standard when clicked', async () => {
    vi.mocked(literaryContextService.getSources).mockResolvedValueOnce(mockSources);
    vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: {} } as any);

    const onSourceChange = vi.fn();
    render(
      <LiterarySourceSelector activeSource="chekhov" onSourceChange={onSourceChange} />
    );

    await waitFor(() => {
      expect(screen.getByText('Standard')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Standard'));

    await waitFor(() => {
      expect(onSourceChange).toHaveBeenCalledWith(null);
    });
  });
});
