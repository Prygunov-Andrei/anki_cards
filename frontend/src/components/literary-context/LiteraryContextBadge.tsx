import React from 'react';
import { BookOpen } from 'lucide-react';

interface LiteraryContextBadgeProps {
  sourceSlug: string;
  matchMethod?: string;
  className?: string;
}

export const LiteraryContextBadge: React.FC<LiteraryContextBadgeProps> = ({
  sourceSlug,
  matchMethod,
  className = '',
}) => {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
        bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 ${className}`}
      title={`Literary context: ${sourceSlug}${matchMethod ? ` (${matchMethod})` : ''}`}
    >
      <BookOpen className="h-3 w-3" />
      {sourceSlug}
    </span>
  );
};
