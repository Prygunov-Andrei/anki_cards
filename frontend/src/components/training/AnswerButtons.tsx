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
    style: {
      backgroundColor: '#fecdd3',
      color: '#7f1d1d',
      borderColor: '#fda4af',
    },
  },
  {
    quality: 1 as AnswerQuality,
    style: {
      backgroundColor: '#fde68a',
      color: '#78350f',
      borderColor: '#fcd34d',
    },
  },
  {
    quality: 2 as AnswerQuality,
    style: {
      backgroundColor: '#d9f99d',
      color: '#365314',
      borderColor: '#bef264',
    },
  },
  {
    quality: 3 as AnswerQuality,
    style: {
      backgroundColor: '#a7f3d0',
      color: '#065f46',
      borderColor: '#6ee7b7',
    },
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
          variant="ghost"
          style={cfg.style}
          className={cn(
            'flex items-center justify-center py-3 h-auto rounded-xl border font-semibold text-sm shadow-sm transition-colors active:scale-95'
          )}
        >
          {answerLabels[cfg.quality]}
        </Button>
      ))}
    </div>
  );
};
