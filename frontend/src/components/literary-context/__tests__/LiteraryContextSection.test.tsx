import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { LiteraryContextSection } from '../LiteraryContextSection';

vi.mock('../../../services/literary-context.service', () => ({
  literaryContextService: {
    getWordContextMedia: vi.fn(),
  },
}));

vi.mock('sonner@2.0.3', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

import { literaryContextService } from '../../../services/literary-context.service';

const mockContext = {
  source_slug: 'chekhov',
  hint_text: 'Think of the market square scene',
  sentences: [
    { text: 'Der Hund lief uber den Platz.', source: 'chekhov' },
  ],
  scene_description: 'A police officer walks across the market square.',
  match_method: 'keyword',
  is_fallback: false,
  image_url: '/media/scenes/test.jpg',
};

describe('LiteraryContextSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(literaryContextService.getWordContextMedia).mockResolvedValue([]);
  });

  it('renders nothing when no active source and no media', async () => {
    const { container } = render(
      <LiteraryContextSection wordId={1} activeSource={null} />
    );
    await waitFor(() => {
      expect(container.innerHTML).toBe('');
    });
  });

  it('shows literary context info when provided', async () => {
    render(
      <LiteraryContextSection
        wordId={1}
        activeSource="chekhov"
        literaryContext={mockContext}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Literary Context')).toBeInTheDocument();
      expect(screen.getByText('chekhov')).toBeInTheDocument();
      expect(screen.getByText('A police officer walks across the market square.')).toBeInTheDocument();
      expect(screen.getByText('Der Hund lief uber den Platz.')).toBeInTheDocument();
    });
  });

  it('shows generate button when active source but no context', async () => {
    render(
      <LiteraryContextSection
        wordId={1}
        activeSource="chekhov"
        literaryContext={undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Literary context not yet generated for this word.')).toBeInTheDocument();
      expect(screen.getByText(/Generate literary context/)).toBeInTheDocument();
    });
  });

  it('shows regenerate button when context exists', async () => {
    render(
      <LiteraryContextSection
        wordId={1}
        activeSource="chekhov"
        literaryContext={mockContext}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Regenerate literary context/)).toBeInTheDocument();
    });
  });
});
