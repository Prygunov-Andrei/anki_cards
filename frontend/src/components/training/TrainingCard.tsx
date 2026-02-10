import React, { useState, useEffect, useRef } from 'react';
import type { CardListItem } from '../../types';
import { cn } from '../ui/utils';
import { useLanguage } from '../../contexts/LanguageContext';
import { getAbsoluteUrl } from '../../utils/url-helpers';

export interface WordDetail {
  etymology?: string;
  hint_text?: string;
  hint_audio?: string;
  sentences?: Array<{ text: string; source: string }>;
  image_file?: string;
  image_url?: string;
  language?: string;
}

interface TrainingCardProps {
  card: CardListItem;
  isFlipped: boolean;
  onFlip: () => void;
  /** Word detail info for back side (etymology, hint, etc) */
  wordDetail?: WordDetail | null;
  /** Menu element (three-dots) to render in top-right corner */
  menuElement?: React.ReactNode;
}

/**
 * Компонент тренировочной карточки с анимацией переворота.
 * Лицевая сторона: картинка + слово (минималистично).
 * Оборотная сторона: картинка + перевод + hint/etymology/sentences.
 * Все сервисные элементы (аудио, подсказка, изучение) вынесены в TrainingSessionPage.
 */
export const TrainingCard: React.FC<TrainingCardProps> = ({
  card,
  isFlipped,
  onFlip,
  wordDetail,
  menuElement,
}) => {
  const { t } = useLanguage();
  const [animating, setAnimating] = useState(false);

  // Reset animation state on card change
  useEffect(() => {
    setAnimating(false);
  }, [card.id]);

  const handleFlip = () => {
    if (isFlipped) return;
    setAnimating(true);
    onFlip();
    setTimeout(() => setAnimating(false), 400);
  };

  // Keyboard: space/enter to flip
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.key === ' ' || e.key === 'Enter') && !isFlipped) {
        e.preventDefault();
        handleFlip();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isFlipped]);

  const isInverted = card.card_type === 'inverted';
  const frontText = isInverted ? card.word_translation : card.word_text;
  const backText = isInverted ? card.word_text : card.word_translation;

  // Image: from card directly (immediate), fallback to wordDetail — convert to absolute URL
  const rawImageUrl = card.image_file || wordDetail?.image_url || wordDetail?.image_file || null;
  const imageUrl = getAbsoluteUrl(rawImageUrl);

  return (
    <div
      className="perspective-1000 w-full cursor-pointer select-none"
      onClick={handleFlip}
    >
      <div
        className={cn(
          'relative w-full transition-transform duration-500 transform-style-3d',
          isFlipped && 'rotate-y-180'
        )}
        style={{
          transformStyle: 'preserve-3d',
          transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
          transition: 'transform 0.5s ease',
        }}
      >
        {/* FRONT */}
        <div
          className="relative w-full rounded-2xl border bg-card shadow-lg p-6 min-h-[320px] flex flex-col items-center justify-center"
          style={{ backfaceVisibility: 'hidden' }}
        >
          {/* Three-dots menu */}
          {menuElement && (
            <div className="absolute top-3 right-3 z-10" onClick={(e) => e.stopPropagation()}>
              {menuElement}
            </div>
          )}

          {/* Image (large) */}
          {imageUrl && (
            <div className="mb-5 w-64 h-64 sm:w-80 sm:h-80 rounded-xl overflow-hidden shadow-md">
              <img
                src={imageUrl}
                alt={card.word_text}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          {/* Word text (large font) */}
          <h2 className="text-4xl sm:text-5xl font-bold text-center break-words">
            {frontText}
          </h2>
        </div>

        {/* BACK */}
        <div
          className="absolute inset-0 w-full rounded-2xl border bg-card shadow-lg p-6 min-h-[320px] flex flex-col overflow-y-auto"
          style={{
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
          }}
        >
          {/* Three-dots menu on back too */}
          {menuElement && (
            <div className="absolute top-3 right-3 z-10" onClick={(e) => e.stopPropagation()}>
              {menuElement}
            </div>
          )}

          {/* Image on back too */}
          {imageUrl && (
            <div className="mb-4 w-48 h-48 sm:w-56 sm:h-56 rounded-xl overflow-hidden shadow-md mx-auto">
              <img
                src={imageUrl}
                alt={card.word_text}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          {/* Translation text (large font) */}
          <h2 className="text-3xl sm:text-4xl font-bold text-center break-words mb-4">
            {backText}
          </h2>

          {/* Extra info */}
          <div className="space-y-3 text-sm flex-1">
            {/* Hint */}
            {wordDetail?.hint_text && (
              <div className="rounded-lg bg-blue-50 dark:bg-blue-950/30 p-3">
                <p className="text-xs font-medium text-blue-600 dark:text-blue-400 mb-1">
                  {t.training.card.hint}
                </p>
                <p className="text-blue-900 dark:text-blue-200">
                  {wordDetail.hint_text}
                </p>
              </div>
            )}

            {/* Etymology */}
            {wordDetail?.etymology && (
              <div className="rounded-lg bg-purple-50 dark:bg-purple-950/30 p-3">
                <p className="text-xs font-medium text-purple-600 dark:text-purple-400 mb-1">
                  {t.training.card.etymology}
                </p>
                <p className="text-purple-900 dark:text-purple-200 text-xs leading-relaxed">
                  {wordDetail.etymology}
                </p>
              </div>
            )}

            {/* Sentences */}
            {wordDetail?.sentences && wordDetail.sentences.length > 0 && (
              <div className="rounded-lg bg-green-50 dark:bg-green-950/30 p-3">
                <p className="text-xs font-medium text-green-600 dark:text-green-400 mb-1">
                  {t.training.card.examples}
                </p>
                <ul className="space-y-1">
                  {wordDetail.sentences.slice(0, 2).map((s, i) => (
                    <li
                      key={i}
                      className="text-green-900 dark:text-green-200 text-xs"
                    >
                      {s.text}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
