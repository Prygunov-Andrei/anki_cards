import React from 'react';
import type { AnswerQuality } from '../../types';
import { Button } from '../ui/button';
import { cn } from '../ui/utils';
import { useLanguage } from '../../contexts/LanguageContext';

interface AnswerButtonsProps {
  onAnswer: (quality: AnswerQuality) => void;
  disabled?: boolean;
}

const ANSWER_CONFIG = [
  {
    quality: 0 as AnswerQuality,
    color: 'bg-red-500 hover:bg-red-600 text-white',
  },
  {
    quality: 1 as AnswerQuality,
    color: 'bg-yellow-400 hover:bg-yellow-500 text-gray-900 dark:bg-yellow-500 dark:hover:bg-yellow-600 dark:text-gray-900',
  },
  {
    quality: 2 as AnswerQuality,
    color: 'bg-emerald-300 hover:bg-emerald-400 text-gray-900 dark:bg-emerald-500 dark:hover:bg-emerald-600 dark:text-white',
  },
  {
    quality: 3 as AnswerQuality,
    color: 'bg-green-500 hover:bg-green-600 text-white',
  },
];

/**
 * 4 кнопки ответа SM-2: Снова, Трудно, Хорошо, Легко
 * Клавиатурные шорткаты 1-4 работают, но цифры не отображаются.
 */
export const AnswerButtons: React.FC<AnswerButtonsProps> = ({
  onAnswer,
  disabled = false,
}) => {
  const { t } = useLanguage();

  const answerLabels: Record<number, string> = {
    0: t.training.answerButtons.again,
    1: t.training.answerButtons.hard,
    2: t.training.answerButtons.good,
    3: t.training.answerButtons.easy,
  };

  // Keyboard shortcuts (1-4)
  React.useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (disabled) return;
      const key = e.key;
      if (key === '1') onAnswer(0);
      else if (key === '2') onAnswer(1);
      else if (key === '3') onAnswer(2);
      else if (key === '4') onAnswer(3);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onAnswer, disabled]);

  return (
    <div className="grid grid-cols-4 gap-2 w-full">
      {ANSWER_CONFIG.map((cfg) => (
        <Button
          key={cfg.quality}
          onClick={() => onAnswer(cfg.quality)}
          disabled={disabled}
          className={cn(
            'flex items-center justify-center py-3 h-auto rounded-xl font-semibold text-sm shadow-md transition-all active:scale-95',
            cfg.color
          )}
        >
          {answerLabels[cfg.quality]}
        </Button>
      ))}
    </div>
  );
};
