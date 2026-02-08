import React from 'react';
import { Progress } from '../ui/progress';
import { useLanguage } from '../../contexts/LanguageContext';

interface SessionProgressProps {
  current: number;
  total: number;
  newCount: number;
  reviewCount: number;
  learningCount: number;
}

/**
 * Прогресс-бар тренировочной сессии
 */
export const SessionProgress: React.FC<SessionProgressProps> = ({
  current,
  total,
  newCount,
  reviewCount,
  learningCount,
}) => {
  const { t } = useLanguage();
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div className="w-full space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {current} / {total}
        </span>
        <span className="text-muted-foreground">{percentage}%</span>
      </div>
      <Progress value={percentage} className="h-2" />
      <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
        {newCount > 0 && (
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-blue-500" />
            {t.training.sessionProgress.new} {newCount}
          </span>
        )}
        {learningCount > 0 && (
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-orange-500" />
            {t.training.sessionProgress.learning} {learningCount}
          </span>
        )}
        {reviewCount > 0 && (
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
            {t.training.sessionProgress.review} {reviewCount}
          </span>
        )}
      </div>
    </div>
  );
};
