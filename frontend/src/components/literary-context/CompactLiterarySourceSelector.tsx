import React, { useState, useEffect } from 'react';
import { BookOpen, Check, Sparkles } from 'lucide-react';
import { literaryContextService } from '../../services/literary-context.service';
import { LiterarySource } from '../../types/literary-context';
import apiClient from '../../services/api';
import { API_ENDPOINTS } from '../../lib/api-constants';
import { toast } from 'sonner@2.0.3';

interface CompactLiterarySourceSelectorProps {
  activeSource: string | null;
  onSourceChange: (slug: string | null) => void;
}

export const CompactLiterarySourceSelector: React.FC<CompactLiterarySourceSelectorProps> = ({
  activeSource,
  onSourceChange,
}) => {
  const [sources, setSources] = useState<LiterarySource[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    literaryContextService
      .getSources()
      .then(setSources)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = async (slug: string | null) => {
    if (slug === activeSource) return;
    try {
      await apiClient.patch(API_ENDPOINTS.PROFILE, {
        active_literary_source: slug,
      });
      onSourceChange(slug);
    } catch {
      toast.error('Failed to switch literary context');
    }
  };

  if (loading) {
    return (
      <div className="flex gap-2 overflow-x-auto py-1">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-10 w-24 shrink-0 animate-pulse rounded-full bg-muted" />
        ))}
      </div>
    );
  }

  if (sources.length === 0) return null;

  return (
    <div className="flex gap-2 overflow-x-auto py-1 scrollbar-hide">
      {/* Standard (AI) */}
      <button
        type="button"
        onClick={() => handleSelect(null)}
        className={`
          flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-sm font-medium
          transition-all duration-200
          ${!activeSource
            ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2 dark:ring-offset-gray-950'
            : 'bg-muted/60 text-muted-foreground hover:bg-muted'
          }
        `}
      >
        <Sparkles className="h-4 w-4" />
        <span>Standard</span>
        {!activeSource && <Check className="h-3.5 w-3.5" />}
      </button>

      {/* Literary sources */}
      {sources.map((source) => {
        const isSelected = activeSource === source.slug;
        return (
          <button
            key={source.slug}
            type="button"
            onClick={() => handleSelect(source.slug)}
            className={`
              flex shrink-0 items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium
              transition-all duration-200
              ${isSelected
                ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2 dark:ring-offset-gray-950'
                : 'bg-muted/60 text-muted-foreground hover:bg-muted'
              }
            `}
          >
            {source.cover ? (
              <img
                src={source.cover}
                alt={source.name}
                className="h-6 w-6 rounded-full object-cover"
              />
            ) : (
              <BookOpen className="h-4 w-4" />
            )}
            <span className="max-w-[120px] truncate">{source.name}</span>
            {isSelected && <Check className="h-3.5 w-3.5" />}
          </button>
        );
      })}
    </div>
  );
};
