import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GenerateContextButton } from '../GenerateContextButton';

// Mock the service
vi.mock('../../../services/literary-context.service', () => ({
  literaryContextService: {
    generateContext: vi.fn(),
  },
}));

// Mock sonner toast
vi.mock('sonner@2.0.3', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

import { literaryContextService } from '../../../services/literary-context.service';
import { toast } from 'sonner@2.0.3';

describe('GenerateContextButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Generate" text when no context exists', () => {
    render(<GenerateContextButton wordId={1} sourceSlug="chekhov" />);
    expect(screen.getByText(/Generate literary context/)).toBeInTheDocument();
  });

  it('renders "Regenerate" text when context exists', () => {
    render(<GenerateContextButton wordId={1} sourceSlug="chekhov" hasContext />);
    expect(screen.getByText(/Regenerate literary context/)).toBeInTheDocument();
  });

  it('calls service on click and shows success toast', async () => {
    const mockGenerate = vi.mocked(literaryContextService.generateContext);
    mockGenerate.mockResolvedValueOnce({} as any);

    const onGenerated = vi.fn();
    render(
      <GenerateContextButton
        wordId={42}
        sourceSlug="chekhov"
        onGenerated={onGenerated}
      />
    );

    await userEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(mockGenerate).toHaveBeenCalledWith({
        word_id: 42,
        source_slug: 'chekhov',
      });
      expect(toast.success).toHaveBeenCalledWith('Literary context generated');
      expect(onGenerated).toHaveBeenCalled();
    });
  });

  it('shows error toast on failure', async () => {
    const mockGenerate = vi.mocked(literaryContextService.generateContext);
    mockGenerate.mockRejectedValueOnce(new Error('API error'));

    render(<GenerateContextButton wordId={1} sourceSlug="chekhov" />);
    await userEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to generate literary context');
    });
  });

  it('disables button while loading', async () => {
    const mockGenerate = vi.mocked(literaryContextService.generateContext);
    let resolvePromise: (value: any) => void;
    mockGenerate.mockReturnValueOnce(
      new Promise((resolve) => { resolvePromise = resolve; })
    );

    render(<GenerateContextButton wordId={1} sourceSlug="chekhov" />);
    await userEvent.click(screen.getByRole('button'));

    expect(screen.getByRole('button')).toBeDisabled();

    resolvePromise!({});
    await waitFor(() => {
      expect(screen.getByRole('button')).not.toBeDisabled();
    });
  });
});
