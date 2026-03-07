import React, { useState } from 'react';
import { X, Plus, Check, Loader2 } from 'lucide-react';
import { useTranslation } from '../../contexts/LanguageContext';
import { libraryService, WordFromReaderResult } from '../../services/library.service';
import { toast } from 'sonner';

interface WordPopupProps {
  word: string;
  position: { x: number; y: number };
  sourceSlug: string;
  onClose: () => void;
}

export const WordPopup: React.FC<WordPopupProps> = ({ word, position, sourceSlug, onClose }) => {
  const t = useTranslation();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WordFromReaderResult | null>(null);
  const [added, setAdded] = useState(false);

  const handleAdd = async () => {
    setLoading(true);
    try {
      const res = await libraryService.addWordFromReader(word, sourceSlug);
      setResult(res);
      setAdded(true);
      toast.success(
        res.word.is_new
          ? (t.library?.wordAdded || 'Word added')
          : (t.library?.alreadyInVocabulary || 'Already in vocabulary')
      );
    } catch {
      toast.error('Failed to add word');
    } finally {
      setLoading(false);
    }
  };

  // Position popup near the clicked word, clamped to viewport
  const style: React.CSSProperties = {
    position: 'fixed',
    left: Math.min(position.x, window.innerWidth - 280),
    top: Math.min(position.y + 10, window.innerHeight - 200),
    zIndex: 50,
  };

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40" onClick={onClose} />

      {/* Popup */}
      <div style={style} className="z-50 w-64 rounded-2xl border bg-background p-4 shadow-xl">
        <div className="flex items-start justify-between">
          <p className="text-lg font-semibold">{word}</p>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-muted">
            <X className="h-4 w-4" />
          </button>
        </div>

        {result && (
          <div className="mt-2">
            <p className="text-sm text-muted-foreground">
              {result.word.translation || '...'}
            </p>
            {result.context_media?.hint_text && (
              <p className="mt-2 text-xs italic text-muted-foreground">
                {result.context_media.hint_text}
              </p>
            )}
          </div>
        )}

        <div className="mt-3">
          {added ? (
            <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
              <Check className="h-4 w-4" />
              {result?.word.is_new
                ? (t.library?.wordAdded || 'Added')
                : (t.library?.alreadyInVocabulary || 'Already in vocabulary')}
            </div>
          ) : (
            <button
              onClick={handleAdd}
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              {t.library?.addToVocabulary || 'Add to vocabulary'}
            </button>
          )}
        </div>
      </div>
    </>
  );
};
