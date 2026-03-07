import React, { useState } from 'react';
import { BookOpen, Loader2, RefreshCw } from 'lucide-react';
import { Button } from '../ui/button';
import { literaryContextService } from '../../services/literary-context.service';
import { toast } from 'sonner@2.0.3';

interface GenerateContextButtonProps {
  wordId: number;
  sourceSlug: string;
  hasContext?: boolean;
  onGenerated?: () => void;
}

export const GenerateContextButton: React.FC<GenerateContextButtonProps> = ({
  wordId,
  sourceSlug,
  hasContext = false,
  onGenerated,
}) => {
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      await literaryContextService.generateContext({
        word_id: wordId,
        source_slug: sourceSlug,
      });
      toast.success('Literary context generated');
      onGenerated?.();
    } catch {
      toast.error('Failed to generate literary context');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleGenerate}
      disabled={loading}
      className="gap-2"
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : hasContext ? (
        <RefreshCw className="h-4 w-4" />
      ) : (
        <BookOpen className="h-4 w-4" />
      )}
      {hasContext ? 'Regenerate' : 'Generate'} literary context
    </Button>
  );
};
