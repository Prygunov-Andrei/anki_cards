import React from 'react';
import { Card } from './ui/card';
import { WordCard } from './WordCard';
import { WordTranslationPair } from './TranslationTable';
import { CheckCircle2 } from 'lucide-react';

interface GeneratedWordsGridProps {
  words: WordTranslationPair[];
  imageFiles: Record<string, string>;
  audioFiles: Record<string, string>;
  onDeleteWord: (word: string) => void;
  onRegenerateImage?: (word: string) => Promise<void>;
  onRegenerateAudio?: (word: string) => Promise<void>;
  disabled?: boolean;
}

/**
 * Компонент GeneratedWordsGrid - сетка готовых карточек с медиа
 * Показывает слова, для которых уже сгенерированы изображения и/или аудио
 * iOS 25 стиль, адаптивная сетка для мобильных и десктопа
 */
export const GeneratedWordsGrid: React.FC<GeneratedWordsGridProps> = ({
  words,
  imageFiles,
  audioFiles,
  onDeleteWord,
  onRegenerateImage,
  onRegenerateAudio,
  disabled = false,
}) => {
  // Фильтруем только слова, для которых есть медиа
  const wordsWithMedia = words.filter(
    (pair) => imageFiles[pair.word] || audioFiles[pair.word]
  );

  if (wordsWithMedia.length === 0) {
    return null;
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Заголовок */}
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5 text-green-500" />
          <h3 className="font-semibold">
            Готовые карточки ({wordsWithMedia.length})
          </h3>
        </div>

        {/* Сетка карточек */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {wordsWithMedia.map((pair) => (
            <WordCard
              key={pair.word}
              word={pair.word}
              translation={pair.translation}
              imageUrl={imageFiles[pair.word]}
              audioUrl={audioFiles[pair.word]}
              onDelete={() => onDeleteWord(pair.word)}
              onRegenerateImage={
                onRegenerateImage
                  ? () => onRegenerateImage(pair.word)
                  : undefined
              }
              onRegenerateAudio={
                onRegenerateAudio
                  ? () => onRegenerateAudio(pair.word)
                  : undefined
              }
              disabled={disabled}
            />
          ))}
        </div>

        {/* Подсказка */}
        <p className="text-xs text-muted-foreground">
          💡 Нажмите на изображение для увеличения. Вы можете перегенерировать
          медиа или удалить карточки
        </p>
      </div>
    </Card>
  );
};
