import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LiteraryContextBadge } from '../LiteraryContextBadge';

describe('LiteraryContextBadge', () => {
  it('renders source slug', () => {
    render(<LiteraryContextBadge sourceSlug="chekhov" />);
    expect(screen.getByText('chekhov')).toBeInTheDocument();
  });

  it('shows match method in title', () => {
    render(<LiteraryContextBadge sourceSlug="bible" matchMethod="keyword" />);
    const badge = screen.getByText('bible').closest('span');
    expect(badge).toHaveAttribute('title', 'Literary context: bible (keyword)');
  });

  it('shows title without match method when not provided', () => {
    render(<LiteraryContextBadge sourceSlug="chekhov" />);
    const badge = screen.getByText('chekhov').closest('span');
    expect(badge).toHaveAttribute('title', 'Literary context: chekhov');
  });

  it('applies custom className', () => {
    render(<LiteraryContextBadge sourceSlug="chekhov" className="custom-class" />);
    const badge = screen.getByText('chekhov').closest('span');
    expect(badge?.className).toContain('custom-class');
  });
});
