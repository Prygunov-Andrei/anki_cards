import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import type { WordListItem as WordListItemType } from '../../types';
import { ChevronRight, BookOpen, Calendar } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface WordListItemProps {
  word: WordListItemType;
}

// STATUS_LABELS moved inside component to use translations

export const WordListItem: React.FC<WordListItemProps> = ({ word }) => {
  const { t } = useLanguage();
  const navigate = useNavigate();

  const STATUS_LABELS: Record<string, string> = {
    new: t.wordsCatalog.status.new,
    learning: t.wordsCatalog.status.learning,
    reviewing: t.wordsCatalog.status.reviewing,
    mastered: t.wordsCatalog.status.mastered,
  };

  const handleClick = () => {
    navigate(`/words/${word.id}`, { state: {} });
  };

  const statusLabel = STATUS_LABELS[word.learning_status] ?? word.learning_status;
  const nextReview = word.next_review
    ? new Date(word.next_review).toLocaleDateString()
    : null;

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={handleClick}
    >
      <CardContent className="flex items-center justify-between p-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate text-lg font-semibold">
              {word.original_word}
            </span>
            <span className="text-muted-foreground">—</span>
            <span className="truncate text-muted-foreground">
              {word.translation}
            </span>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              {statusLabel}
            </Badge>
            {word.part_of_speech && (
              <span className="text-xs text-muted-foreground">
                {word.part_of_speech}
              </span>
            )}
            {word.cards_count > 0 && (
              <span className="flex items-center gap-0.5 text-xs text-muted-foreground">
                <BookOpen className="h-3 w-3" />
                {word.cards_count}
              </span>
            )}
            {nextReview && (
              <span className="flex items-center gap-0.5 text-xs text-muted-foreground">
                <Calendar className="h-3 w-3" />
                {nextReview}
              </span>
            )}
            {word.categories && word.categories.length > 0 && (
              <>
                {word.categories.map((cat) => (
                  <Badge
                    key={cat.id}
                    variant="outline"
                    className="gap-1 border-blue-200 bg-blue-50/50 px-1.5 py-0 text-[10px] text-blue-600 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-400"
                  >
                    <span>{cat.icon || '📂'}</span>
                    {cat.name}
                  </Badge>
                ))}
              </>
            )}
          </div>
        </div>
        <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground" />
      </CardContent>
    </Card>
  );
};
