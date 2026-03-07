import React, { useState, useEffect } from 'react';
import { BookOpen, Check } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { literaryContextService } from '../../services/literary-context.service';
import { LiterarySource } from '../../types/literary-context';
import apiClient from '../../services/api';
import { API_ENDPOINTS } from '../../lib/api-constants';
import { toast } from 'sonner@2.0.3';

interface LiterarySourceSelectorProps {
  activeSource: string | null;
  onSourceChange: (slug: string | null) => void;
}

export const LiterarySourceSelector: React.FC<LiterarySourceSelectorProps> = ({
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
    try {
      await apiClient.patch(API_ENDPOINTS.PROFILE, {
        active_literary_source: slug,
      });
      onSourceChange(slug);
      toast.success(
        slug
          ? `Literary context switched to "${sources.find(s => s.slug === slug)?.name}"`
          : 'Switched to standard context'
      );
    } catch {
      toast.error('Failed to switch literary context');
    }
  };

  if (loading) {
    return <div className="animate-pulse h-20 bg-muted rounded-lg" />;
  }

  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium flex items-center gap-2">
        <BookOpen className="h-4 w-4" />
        Literary Context
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {/* Standard option */}
        <Card
          className={`cursor-pointer transition-all ${
            !activeSource ? 'ring-2 ring-primary' : 'hover:bg-muted/50'
          }`}
          onClick={() => handleSelect(null)}
        >
          <CardContent className="p-3 flex items-center gap-3">
            <div className="w-10 h-10 rounded bg-muted flex items-center justify-center text-lg">
              AI
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm">Standard</p>
              <p className="text-xs text-muted-foreground truncate">AI-generated content</p>
            </div>
            {!activeSource && <Check className="h-4 w-4 text-primary" />}
          </CardContent>
        </Card>

        {/* Literary sources */}
        {sources.map((source) => (
          <Card
            key={source.slug}
            className={`cursor-pointer transition-all ${
              activeSource === source.slug ? 'ring-2 ring-primary' : 'hover:bg-muted/50'
            }`}
            onClick={() => handleSelect(source.slug)}
          >
            <CardContent className="p-3 flex items-center gap-3">
              {source.cover ? (
                <img
                  src={source.cover}
                  alt={source.name}
                  className="w-10 h-10 rounded object-cover"
                />
              ) : (
                <div className="w-10 h-10 rounded bg-amber-100 dark:bg-amber-900 flex items-center justify-center">
                  <BookOpen className="h-5 w-5 text-amber-700 dark:text-amber-300" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm">{source.name}</p>
                <p className="text-xs text-muted-foreground truncate">{source.description}</p>
              </div>
              {activeSource === source.slug && <Check className="h-4 w-4 text-primary" />}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
