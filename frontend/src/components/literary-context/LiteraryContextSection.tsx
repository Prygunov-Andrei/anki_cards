import React, { useState, useEffect } from 'react';
import { BookOpen, Quote } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { LiteraryContextBadge } from './LiteraryContextBadge';
import { GenerateContextButton } from './GenerateContextButton';
import { literaryContextService } from '../../services/literary-context.service';
import { WordContextMedia } from '../../types/literary-context';

interface LiteraryContextSectionProps {
  wordId: number;
  activeSource: string | null;
  literaryContext?: {
    source_slug: string;
    hint_text: string;
    sentences: Array<{ text: string; source: string }>;
    scene_description: string;
    match_method: string;
    is_fallback: boolean;
    image_url: string | null;
  } | null;
}

export const LiteraryContextSection: React.FC<LiteraryContextSectionProps> = ({
  wordId,
  activeSource,
  literaryContext,
}) => {
  const [contextMedia, setContextMedia] = useState<WordContextMedia[]>([]);
  const [loading, setLoading] = useState(false);

  const loadMedia = () => {
    setLoading(true);
    literaryContextService
      .getWordContextMedia(wordId)
      .then(setContextMedia)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadMedia();
  }, [wordId]);

  if (!activeSource && contextMedia.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <BookOpen className="h-4 w-4" />
          Literary Context
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current overlay info */}
        {literaryContext && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <LiteraryContextBadge
                sourceSlug={literaryContext.source_slug}
                matchMethod={literaryContext.match_method}
              />
            </div>

            {literaryContext.scene_description && (
              <p className="text-sm text-muted-foreground italic">
                {literaryContext.scene_description}
              </p>
            )}

            {literaryContext.sentences?.length > 0 && (
              <div className="space-y-1">
                {literaryContext.sentences.map((s, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <Quote className="h-3 w-3 mt-1 text-muted-foreground shrink-0" />
                    <span>{s.text}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* No context yet */}
        {activeSource && !literaryContext && (
          <div className="text-center py-4 text-sm text-muted-foreground">
            <p>Literary context not yet generated for this word.</p>
            <div className="mt-3">
              <GenerateContextButton
                wordId={wordId}
                sourceSlug={activeSource}
                onGenerated={loadMedia}
              />
            </div>
          </div>
        )}

        {/* Regenerate button if context exists */}
        {activeSource && literaryContext && (
          <GenerateContextButton
            wordId={wordId}
            sourceSlug={activeSource}
            hasContext
            onGenerated={loadMedia}
          />
        )}
      </CardContent>
    </Card>
  );
};
