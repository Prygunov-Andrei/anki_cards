import React, { useEffect } from 'react';
import type { CardListItem } from '../../types';
import { cn } from '../ui/utils';
import { getAbsoluteUrl } from '../../utils/url-helpers';
import { LiteraryContextBadge } from '../literary-context/LiteraryContextBadge';

export interface WordDetail {
  etymology?: string;
  hint_text?: string;
  hint_audio?: string;
  sentences?: Array<{ text: string; source: string }>;
  image_file?: string;
  image_url?: string;
  language?: string;
  literary_context?: {
    source_slug: string;
    match_method: string;
  } | null;
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
 * Оборотная сторона: только картинка + перевод.
 * Все сервисные элементы (аудио, подсказка, изучение) вынесены в TrainingSessionPage.
 */
export const TrainingCard: React.FC<TrainingCardProps> = ({
  card,
  isFlipped,
  onFlip,
  wordDetail,
  menuElement,
}) => {
  const handleFlip = () => {
    if (isFlipped) return;
    onFlip();
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
      className="perspective-1000 relative h-full w-full cursor-pointer select-none"
      onClick={handleFlip}
    >
      {isFlipped && menuElement && (
        <div
          className="z-20"
          style={{ position: 'absolute', top: 12, right: 12 }}
          onClick={(e) => e.stopPropagation()}
        >
          {menuElement}
        </div>
      )}
      <div
        className={cn(
          'relative h-full w-full transition-transform duration-500 transform-style-3d',
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
          className="relative h-full w-full min-h-0 rounded-2xl border bg-card p-3 shadow-lg sm:p-4 flex flex-col items-center justify-center"
          style={{ backfaceVisibility: 'hidden' }}
        >
          {/* Image (large) */}
          {imageUrl && (
            <div
              className="mb-3 rounded-xl overflow-hidden shadow-md"
              style={{
                width: 'min(58vw, 52vh, 420px)',
                height: 'min(58vw, 52vh, 420px)',
              }}
            >
              <img
                src={imageUrl}
                alt={card.word_text}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          {/* Word text (large font) */}
          <h2
            className="font-bold text-center break-words leading-tight"
            style={{ fontSize: 'clamp(1.6rem, 3.8vh, 2.9rem)' }}
          >
            {frontText}
          </h2>

          {/* Literary context badge */}
          {wordDetail?.literary_context && (
            <div className="mt-2">
              <LiteraryContextBadge
                sourceSlug={wordDetail.literary_context.source_slug}
                matchMethod={wordDetail.literary_context.match_method}
              />
            </div>
          )}
        </div>

        {/* BACK */}
        <div
          className="absolute inset-0 h-full w-full min-h-0 rounded-2xl border bg-card p-3 shadow-lg sm:p-4 flex flex-col items-center justify-center"
          style={{
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
          }}
        >
          {/* Image on back too (same size as front) */}
          {imageUrl && (
            <div
              className="mb-3 rounded-xl overflow-hidden shadow-md"
              style={{
                width: 'min(58vw, 52vh, 420px)',
                height: 'min(58vw, 52vh, 420px)',
              }}
            >
              <img
                src={imageUrl}
                alt={card.word_text}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          {/* Translation text (large font) */}
          <h2
            className="font-bold text-center break-words leading-tight"
            style={{ fontSize: 'clamp(1.45rem, 3.2vh, 2.5rem)' }}
          >
            {backText}
          </h2>

        </div>
      </div>
    </div>
  );
};
