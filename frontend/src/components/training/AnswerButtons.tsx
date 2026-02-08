import React from 'react';
import type { AnswerQuality } from '../../types';
import { Button } from '../ui/button';
import { cn } from '../ui/utils';
import { useLanguage } from '../../contexts/LanguageContext';

interface AnswerButtonsProps {
  onAnswer: (quality: AnswerQuality) => void;
  disabled?: boolean;
  isLearningMode?: boolean;
}

const ANSWER_CONFIG = [
  {
    quality: 0 as AnswerQuality,
    label: 'Снова',
    sublabel: '<1 мин',
    color: 'bg-red-500 hover:bg-red-600 text-white',
    shortcut: '1',
  },
  {
    quality: 1 as AnswerQuality,
    label: 'Трудно',
    sublabel: '',
    color: 'bg-orange-500 hover:bg-orange-600 text-white',
    shortcut: '2',
  },
  {
    quality: 2 as AnswerQuality,
    label: 'Хорошо',
    sublabel: '',
    color: 'bg-green-500 hover:bg-green-600 text-white',
    shortcut: '3',
  },
  {
    quality: 3 as AnswerQuality,
    label: 'Легко',
    sublabel: '',
    color: 'bg-blue-500 hover:bg-blue-600 text-white',
    shortcut: '4',
  },
];

/**
 * 4 кнопки ответа SM-2: Снова, Трудно, Хорошо, Легко
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

  // Keyboard shortcuts
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
            'flex flex-col items-center py-3 h-auto rounded-xl font-semibold text-sm shadow-md transition-all active:scale-95',
            cfg.color
          )}
        >
          <span>{answerLabels[cfg.quality]}</span>
          <span className="text-[10px] font-normal opacity-80 mt-0.5">
            {cfg.shortcut}
          </span>
        </Button>
      ))}
    </div>
  );
};
