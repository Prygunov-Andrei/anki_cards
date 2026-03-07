import React, { useState } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from '../ui/dropdown-menu';
import { Button } from '../ui/button';
import {
  MoreVertical,
  RefreshCw,
  ArrowRight,
  ImageIcon,
  Volume2,
  Trash2,
  Wand2,
  Loader2,
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { deckService } from '../../services/deck.service';
import { wordsService } from '../../services/words.service';
import { ImageEditModal } from '../ImageEditModal';
import type { CardListItem } from '../../types';
import type { WordDetail } from './TrainingCard';

interface TrainingCardMenuProps {
  card: CardListItem;
  wordDetail?: WordDetail | null;
  availableDecks?: Array<{ id: number; name: string }>;
  onDeleteWord: (wordId: number) => Promise<void>;
  onMoveToDeck: (wordId: number, deckId: number, deckName: string) => Promise<void>;
  onUpdateCardMedia: (cardId: number, updates: { image_file?: string; audio_file?: string }) => void;
  onUpdateWordDetail?: (cardId: number, updates: Partial<WordDetail>) => void;
}

type GeneratingState = {
  image?: boolean;
  audio?: boolean;
  imageEdit?: boolean;
  deletingWord?: boolean;
};

/**
 * Лаконичное меню "три точки" на тренировочной карточке:
 * Перегенерировать (изображение/аудио), изменить картинку, удалить (слово/изобр./аудио), переместить в колоду.
 */
export const TrainingCardMenu: React.FC<TrainingCardMenuProps> = ({
  card,
  wordDetail,
  availableDecks,
  onDeleteWord,
  onMoveToDeck,
  onUpdateCardMedia,
  onUpdateWordDetail,
}) => {
  const { t } = useLanguage();
  const [generating, setGenerating] = useState<GeneratingState>({});
  const [movingDeckId, setMovingDeckId] = useState<number | null>(null);
  const [isImageEditOpen, setIsImageEditOpen] = useState(false);

  const setGen = (key: keyof GeneratingState, val: boolean) => {
    setGenerating((prev) => ({ ...prev, [key]: val }));
  };

  const hasImage = !!card.image_file || !!wordDetail?.image_file || !!wordDetail?.image_url;
  const hasAudio = !!card.audio_file;

  const handleGenerateImage = async () => {
    setGen('image', true);
    try {
      const lang = wordDetail?.language || 'en';
      const res = await deckService.generateImage({
        word: card.word_text,
        translation: card.word_translation,
        language: lang,
        image_style: 'balanced',
        word_id: card.word_id,
      });
      const newUrl = res.image_url;
      onUpdateCardMedia(card.id, { image_file: newUrl });
      onUpdateWordDetail?.(card.id, { image_file: newUrl, image_url: newUrl });
    } catch {
      // Could show a toast here
    } finally {
      setGen('image', false);
    }
  };

  const handleEditImage = async (mixin: string) => {
    setGen('imageEdit', true);
    try {
      const res = await deckService.editImage({
        word_id: card.word_id,
        mixin,
      });
      const newUrl = res.image_url;
      onUpdateCardMedia(card.id, { image_file: newUrl });
      onUpdateWordDetail?.(card.id, { image_file: newUrl, image_url: newUrl });
    } finally {
      setGen('imageEdit', false);
    }
  };

  const handleDeleteImage = async () => {
    try {
      await wordsService.updateWord(card.word_id, { image_file: null });
      onUpdateCardMedia(card.id, { image_file: '' });
      onUpdateWordDetail?.(card.id, { image_file: undefined, image_url: undefined });
    } catch {
      // Silent
    }
  };

  const handleGenerateAudio = async () => {
    setGen('audio', true);
    try {
      const lang = wordDetail?.language || 'en';
      const res = await deckService.generateAudio({
        word: card.word_text,
        language: lang,
        word_id: card.word_id,
      });
      const newUrl = res.audio_url;
      onUpdateCardMedia(card.id, { audio_file: newUrl });
    } catch {
      // Could show a toast here
    } finally {
      setGen('audio', false);
    }
  };

  const handleDeleteAudio = async () => {
    try {
      await wordsService.updateWord(card.word_id, { audio_file: null });
      onUpdateCardMedia(card.id, { audio_file: '' });
    } catch {
      // Silent
    }
  };

  const handleMoveToDeck = async (deckId: number, deckName: string) => {
    setMovingDeckId(deckId);
    try {
      await onMoveToDeck(card.word_id, deckId, deckName);
    } finally {
      setMovingDeckId(null);
    }
  };

  const handleDeleteWord = async () => {
    setGen('deletingWord', true);
    try {
      await onDeleteWord(card.word_id);
    } finally {
      setGen('deletingWord', false);
    }
  };

  const isAnyGenerating = Object.values(generating).some(Boolean);

  const wordsText = t.words;
  const menu = t.trainingCard?.menu;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="secondary"
          size="sm"
          className="h-10 w-10 flex-shrink-0 rounded-full p-0 shadow-lg"
          onClick={(e) => e.preventDefault()}
        >
          {isAnyGenerating ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <MoreVertical className="h-5 w-5" />
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        {/* Regenerate submenu */}
        <DropdownMenuSub>
          <DropdownMenuSubTrigger disabled={generating.image || generating.audio}>
            <RefreshCw className="mr-2 h-4 w-4" />
            {wordsText?.regenerate || 'Regenerate'}
          </DropdownMenuSubTrigger>
          <DropdownMenuSubContent>
            <DropdownMenuItem onClick={handleGenerateImage} disabled={generating.image}>
              <ImageIcon className="mr-2 h-4 w-4" />
              {wordsText?.regenerateImage || 'Regenerate image'}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleGenerateAudio} disabled={generating.audio}>
              <Volume2 className="mr-2 h-4 w-4" />
              {wordsText?.regenerateAudio || 'Regenerate audio'}
            </DropdownMenuItem>
          </DropdownMenuSubContent>
        </DropdownMenuSub>

        {hasImage && (
          <DropdownMenuItem
            onClick={() => setIsImageEditOpen(true)}
            disabled={generating.imageEdit}
          >
            <Wand2 className="mr-2 h-4 w-4" />
            {wordsText?.editImage || 'Edit image'}
          </DropdownMenuItem>
        )}

        {/* Move to deck submenu */}
        {availableDecks && availableDecks.length > 0 && (
          <DropdownMenuSub>
            <DropdownMenuSubTrigger disabled={movingDeckId !== null}>
              <ArrowRight className="mr-2 h-4 w-4" />
              {wordsText?.moveToDeck || 'Move to deck'}
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              {availableDecks.map((deck) => (
                <DropdownMenuItem
                  key={deck.id}
                  onClick={() => handleMoveToDeck(deck.id, deck.name)}
                  disabled={movingDeckId !== null}
                >
                  {deck.name}
                </DropdownMenuItem>
              ))}
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        )}

        <DropdownMenuSeparator />

        <DropdownMenuSub>
          <DropdownMenuSubTrigger className="text-destructive focus:text-destructive">
            <Trash2 className="mr-2 h-4 w-4" />
            {wordsText?.delete || 'Delete'}
          </DropdownMenuSubTrigger>
          <DropdownMenuSubContent>
            <DropdownMenuItem
              onClick={handleDeleteWord}
              disabled={!!generating.deletingWord}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              {wordsText?.word || 'Word'}
            </DropdownMenuItem>
            {hasImage && (
              <DropdownMenuItem
                onClick={handleDeleteImage}
                className="text-destructive focus:text-destructive"
              >
                <ImageIcon className="mr-2 h-4 w-4" />
                {wordsText?.deleteImage || menu?.deleteImage || 'Delete image'}
              </DropdownMenuItem>
            )}
            {hasAudio && (
              <DropdownMenuItem
                onClick={handleDeleteAudio}
                className="text-destructive focus:text-destructive"
              >
                <Volume2 className="mr-2 h-4 w-4" />
                {wordsText?.deleteAudio || menu?.deleteAudio || 'Delete audio'}
              </DropdownMenuItem>
            )}
          </DropdownMenuSubContent>
        </DropdownMenuSub>
      </DropdownMenuContent>

      <ImageEditModal
        isOpen={isImageEditOpen}
        onClose={() => setIsImageEditOpen(false)}
        onSubmit={handleEditImage}
        word={card.word_text}
      />
    </DropdownMenu>
  );
};
