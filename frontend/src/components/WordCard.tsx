import React, { useState } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { ImagePreviewModal } from './ImagePreviewModal';
import { ImageEditModal } from './ImageEditModal';
import { ArrowLeftRight, FileText, BookOpen } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';
import { WordCardImage } from './word-card/WordCardImage';
import { WordCardActions } from './word-card/WordCardActions';
import { WordCardAudio } from './word-card/WordCardAudio';
import { WordCardContent } from './word-card/WordCardContent';

interface WordCardProps {
  word: string;
  translation: string;
  imageUrl?: string;
  audioUrl?: string;
  wordId?: number;
  deckId?: number;
  cardType?: 'normal' | 'inverted' | 'empty';
  onDelete?: () => void;
  onRegenerateImage?: () => Promise<void>;
  onRegenerateAudio?: () => Promise<void>;
  onEditImage?: (mixin: string) => Promise<void>;
  onDeleteImage?: () => Promise<void>;
  onDeleteAudio?: () => Promise<void>;
  onMoveToDeck?: (deckId: number, deckName: string) => Promise<void>;
  onInvertWord?: () => Promise<void>;
  onCreateEmptyCard?: () => Promise<void>;
  onWordUpdate?: (wordId: number, data: { original_word?: string; translation?: string }) => Promise<void>;
  availableDecks?: { id: number; name: string }[];
  allDecks?: { id: number; name: string; words?: unknown[] }[];
  disabled?: boolean;
}

const CARD_TYPE_CONFIG = {
  inverted: { icon: ArrowLeftRight, labelKey: 'cardTypeInverted' as const, className: 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20' },
  empty: { icon: FileText, labelKey: 'cardTypeEmpty' as const, className: 'bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/20' },
  normal: { icon: BookOpen, labelKey: 'cardTypeNormal' as const, className: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20' },
};

export const WordCard: React.FC<WordCardProps> = ({
  word, translation, imageUrl, audioUrl, wordId, deckId,
  cardType = 'normal', onDelete, onRegenerateImage, onRegenerateAudio,
  onEditImage, onDeleteImage, onDeleteAudio, onMoveToDeck,
  onInvertWord, onCreateEmptyCard, onWordUpdate,
  availableDecks, allDecks, disabled = false,
}) => {
  const t = useTranslation();
  const [previewImage, setPreviewImage] = useState<{ url: string; word: string; translation: string } | null>(null);
  const [regeneratingImage, setRegeneratingImage] = useState(false);
  const [regeneratingAudio, setRegeneratingAudio] = useState(false);
  const [editImageModalOpen, setEditImageModalOpen] = useState(false);

  const decksToShow = availableDecks || allDecks;

  const handleRegenerateImage = async () => {
    if (!onRegenerateImage) return;
    setRegeneratingImage(true);
    try { await onRegenerateImage(); } finally { setRegeneratingImage(false); }
  };

  const handleRegenerateAudio = async () => {
    if (!onRegenerateAudio) return;
    setRegeneratingAudio(true);
    try { await onRegenerateAudio(); } finally { setRegeneratingAudio(false); }
  };

  const handleEditImage = async (mixin: string) => {
    if (!onEditImage) return;
    setRegeneratingImage(true);
    try { await onEditImage(mixin); } finally { setRegeneratingImage(false); }
  };

  const badgeInfo = CARD_TYPE_CONFIG[cardType];
  const BadgeIcon = badgeInfo.icon;

  return (
    <>
      <Card className="overflow-hidden hover:shadow-lg transition-shadow relative">
        {cardType && (cardType === 'inverted' || cardType === 'empty') && (
          <Badge
            variant="outline"
            className={`absolute top-2 left-2 z-10 text-lg px-6 py-3 flex items-center gap-3 ${badgeInfo.className}`}
            title={t.words[badgeInfo.labelKey]}
          >
            <BadgeIcon className="h-6 w-6" />
            <span className="hidden sm:inline font-semibold">{t.words[badgeInfo.labelKey]}</span>
          </Badge>
        )}

        <WordCardActions
          word={word} translation={translation} imageUrl={imageUrl} audioUrl={audioUrl}
          wordId={wordId} deckId={deckId} disabled={disabled}
          regeneratingImage={regeneratingImage} regeneratingAudio={regeneratingAudio}
          decksToShow={decksToShow} onRegenerateImage={handleRegenerateImage}
          onRegenerateAudio={handleRegenerateAudio}
          onEditImage={onEditImage ? () => setEditImageModalOpen(true) : undefined}
          onDelete={onDelete} onDeleteImage={onDeleteImage} onDeleteAudio={onDeleteAudio}
          onMoveToDeck={onMoveToDeck} onInvertWord={onInvertWord} onCreateEmptyCard={onCreateEmptyCard}
        />

        <WordCardImage
          word={word} imageUrl={imageUrl} regeneratingImage={regeneratingImage}
          disabled={disabled}
          onImageClick={() => setPreviewImage({ url: imageUrl!, word, translation })}
          onRegenerateImage={onRegenerateImage ? handleRegenerateImage : undefined}
        />

        <div className="p-4 space-y-3">
          <WordCardContent
            word={word} translation={translation}
            wordId={wordId} onWordUpdate={onWordUpdate}
          />
          <WordCardAudio
            audioUrl={audioUrl} word={word}
            regeneratingAudio={regeneratingAudio}
          />
        </div>
      </Card>

      {previewImage && (
        <ImagePreviewModal
          isOpen={!!previewImage}
          onClose={() => setPreviewImage(null)}
          imageUrl={previewImage.url}
          word={previewImage.word}
          translation={previewImage.translation}
        />
      )}

      {editImageModalOpen && (
        <ImageEditModal
          isOpen={editImageModalOpen}
          onClose={() => setEditImageModalOpen(false)}
          onSubmit={handleEditImage}
          word={word}
        />
      )}
    </>
  );
};
