import React, { useState, useEffect, useRef } from 'react';
import type { CardListItem } from '../../types';
import { cn } from '../ui/utils';
import { Eye, Volume2, BookOpen } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { getAbsoluteUrl, getAudioUrl } from '../../utils/url-helpers';

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
 * Лицевая сторона: слово (или перевод для inverted), картинка, кнопка аудио.
 * Оборотная сторона: перевод (или слово), + подсказка, этимология, предложения.
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
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

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

  const playAudio = (url: string) => {
    try {
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
      }
      audioPlayerRef.current = new Audio(url);
      audioPlayerRef.current.play().catch(() => { /* autoplay blocked */ });
    } catch {
      // Silent fail
    }
  };

  const isInverted = card.card_type === 'inverted';
  const frontText = isInverted ? card.word_translation : card.word_text;
  const frontLabel = isInverted ? t.training.card.translation : t.training.card.word;
  const backText = isInverted ? card.word_text : card.word_translation;
  const backLabel = isInverted ? t.training.card.word : t.training.card.translation;

  // Image: from card directly (immediate), fallback to wordDetail — convert to absolute URL
  const rawImageUrl = card.image_file || wordDetail?.image_url || wordDetail?.image_file || null;
  const imageUrl = getAbsoluteUrl(rawImageUrl);
  // Audio: from card directly — convert to absolute URL
  const rawAudioUrl = card.audio_file || null;
  const audioUrl = getAudioUrl(rawAudioUrl);

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
          className="relative w-full rounded-2xl border bg-card shadow-lg p-6 min-h-[280px] flex flex-col items-center justify-center"
          style={{ backfaceVisibility: 'hidden' }}
        >
          {/* Three-dots menu */}
          {menuElement && (
            <div className="absolute top-3 right-3 z-10" onClick={(e) => e.stopPropagation()}>
              {menuElement}
            </div>
          )}

          <p className="text-xs font-medium text-muted-foreground mb-4 uppercase tracking-wider">
            {frontLabel}
          </p>

          {/* Image on front (if available) */}
          {imageUrl && (
            <div className="mb-4 w-32 h-32 rounded-xl overflow-hidden shadow-md">
              <img
                src={imageUrl}
                alt={card.word_text}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          <h2 className="text-3xl font-bold text-center break-words">
            {frontText}
          </h2>

          {/* Audio play button */}
          {audioUrl && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                playAudio(audioUrl);
              }}
              className="mt-3 flex items-center gap-1.5 rounded-full bg-indigo-100 px-4 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 transition-colors"
            >
              <Volume2 className="h-4 w-4" />
              {t.training.card.listen}
            </button>
          )}

          {card.is_in_learning_mode && (
            <span className="mt-3 inline-flex items-center gap-1 rounded-full bg-orange-100 px-3 py-1 text-xs font-medium text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
              <BookOpen className="h-3 w-3" />
              {t.training.card.learningMode}
            </span>
          )}

          <p className="mt-6 text-sm text-muted-foreground flex items-center gap-1">
            <Eye className="h-4 w-4" />
            {t.training.card.flipHint}
          </p>
        </div>

        {/* BACK */}
        <div
          className="absolute inset-0 w-full rounded-2xl border bg-card shadow-lg p-6 min-h-[280px] flex flex-col overflow-y-auto"
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

          <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider text-center">
            {backLabel}
          </p>
          <h2 className="text-2xl font-bold text-center break-words mb-4">
            {backText}
          </h2>

          {/* Audio play button on back side */}
          {audioUrl && (
            <div className="flex justify-center mb-3">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  playAudio(audioUrl);
                }}
                className="flex items-center gap-1.5 rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 transition-colors"
              >
                <Volume2 className="h-3 w-3" />
                {t.training.card.listen}
              </button>
            </div>
          )}

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
                {wordDetail.hint_audio && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      playAudio(wordDetail.hint_audio!);
                    }}
                    className="mt-1 flex items-center gap-1 text-xs text-blue-500 hover:text-blue-700"
                  >
                    <Volume2 className="h-3 w-3" />
                    {t.training.card.listen}
                  </button>
                )}
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
