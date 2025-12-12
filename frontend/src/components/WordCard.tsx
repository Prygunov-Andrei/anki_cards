import React, { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { AudioPlayer } from './AudioPlayer';
import { ImagePreviewModal } from './ImagePreviewModal';
import { EditableText } from './EditableText';
import { Trash2, RefreshCw, ImageIcon, MoreVertical, ArrowRight, Volume2, ArrowLeftRight, FileText } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from './ui/dropdown-menu';
import { useTranslation } from '../contexts/LanguageContext';
import { displayWord } from '../utils/helpers';

interface WordCardProps {
  word: string;
  translation: string;
  imageUrl?: string;
  audioUrl?: string;
  wordId?: number;
  deckId?: number;
  onDelete?: () => void;
  onRegenerateImage?: () => Promise<void>;
  onRegenerateAudio?: () => Promise<void>;
  onDeleteImage?: () => Promise<void>;
  onDeleteAudio?: () => Promise<void>;
  onMoveToDeck?: (deckId: number, deckName: string) => Promise<void>;
  onInvertWord?: () => Promise<void>;
  onCreateEmptyCard?: () => Promise<void>;
  onWordUpdate?: (wordId: number, data: { original_word?: string; translation?: string }) => Promise<void>;
  availableDecks?: { id: number; name: string }[];
  allDecks?: { id: number; name: string; words?: any[] }[];
  disabled?: boolean;
}

/**
 * Компоннт WordCard - красивая карточка с медиа-контентом
 * Показывает готовую карточку ANKI с изображением, аудио и переводом
 * iOS 25 стиль, оптимизирован для мобильных устройств
 */
export const WordCard: React.FC<WordCardProps> = ({
  word,
  translation,
  imageUrl,
  audioUrl,
  wordId,
  deckId,
  onDelete,
  onRegenerateImage,
  onRegenerateAudio,
  onDeleteImage,
  onDeleteAudio,
  onMoveToDeck,
  onInvertWord,
  onCreateEmptyCard,
  onWordUpdate,
  availableDecks,
  allDecks,
  disabled = false,
}) => {
  const t = useTranslation();
  
  const [previewImage, setPreviewImage] = useState<{
    url: string;
    word: string;
    translation: string;
  } | null>(null);
  const [regeneratingImage, setRegeneratingImage] = useState(false);
  const [regeneratingAudio, setRegeneratingAudio] = useState(false);

  // Фильтруем список колод - используем availableDecks если передан, иначе allDecks (все колоды минус текущую будут показаны)
  const decksToShow = availableDecks || allDecks;

  /**
   * Открыть превью изображения
   */
  const handleImageClick = () => {
    if (imageUrl) {
      setPreviewImage({ url: imageUrl, word, translation });
    }
  };

  /**
   * Перегенерация изображения
   */
  const handleRegenerateImage = async () => {
    if (!onRegenerateImage) return;
    setRegeneratingImage(true);
    try {
      await onRegenerateImage();
    } finally {
      setRegeneratingImage(false);
    }
  };

  /**
   * Перегенерация аудио
   */
  const handleRegenerateAudio = async () => {
    if (!onRegenerateAudio) return;
    setRegeneratingAudio(true);
    try {
      await onRegenerateAudio();
    } finally {
      setRegeneratingAudio(false);
    }
  };

  return (
    <>
      <Card className="overflow-hidden hover:shadow-lg transition-shadow relative">
        {/* Меню карточки - ВСЕГДА видимое */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="secondary"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
              }}
              disabled={disabled}
              className="absolute top-2 right-2 h-8 w-8 p-0 rounded-full shadow-lg z-10"
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {/* Перегенерировать → */}
            {(onRegenerateImage || onRegenerateAudio) && (
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  {t.words.regenerate}
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  {onRegenerateImage && (
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRegenerateImage();
                      }}
                      disabled={disabled || regeneratingImage}
                    >
                      <ImageIcon className={`mr-2 h-4 w-4 ${regeneratingImage ? 'animate-pulse' : ''}`} />
                      {t.words.regenerateImage}
                    </DropdownMenuItem>
                  )}
                  {onRegenerateAudio && (
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRegenerateAudio();
                      }}
                      disabled={disabled || regeneratingAudio}
                    >
                      <Volume2 className={`mr-2 h-4 w-4 ${regeneratingAudio ? 'animate-pulse' : ''}`} />
                      {t.words.regenerateAudio}
                    </DropdownMenuItem>
                  )}
                </DropdownMenuSubContent>
              </DropdownMenuSub>
            )}

            {/* Удалить → */}
            {(onDelete || onDeleteImage || onDeleteAudio) && (
              <DropdownMenuSub>
                <DropdownMenuSubTrigger className="text-destructive focus:text-destructive">
                  <Trash2 className="mr-2 h-4 w-4" />
                  {t.words.delete}
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  {onDelete && (
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete();
                      }}
                      disabled={disabled}
                      className="text-destructive focus:text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      {t.words.deleteWord}
                    </DropdownMenuItem>
                  )}
                  {onDeleteImage && imageUrl && (
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteImage();
                      }}
                      disabled={disabled}
                      className="text-destructive focus:text-destructive"
                    >
                      <ImageIcon className="mr-2 h-4 w-4" />
                      {t.words.deleteImage}
                    </DropdownMenuItem>
                  )}
                  {onDeleteAudio && audioUrl && (
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteAudio();
                      }}
                      disabled={disabled}
                      className="text-destructive focus:text-destructive"
                    >
                      <Volume2 className="mr-2 h-4 w-4" />
                      {t.words.deleteAudio}
                    </DropdownMenuItem>
                  )}
                </DropdownMenuSubContent>
              </DropdownMenuSub>
            )}

            {/* Переместить в колоду → */}
            {onMoveToDeck && decksToShow && decksToShow.length > 0 && (
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <ArrowRight className="mr-2 h-4 w-4" />
                  {t.words.moveToDeck}
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  {decksToShow.map(deck => (
                    <DropdownMenuItem
                      key={deck.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        onMoveToDeck(deck.id, deck.name);
                      }}
                      disabled={disabled}
                    >
                      {deck.name}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuSubContent>
              </DropdownMenuSub>
            )}

            {/* Инвертировать слово и перевод → */}
            {onInvertWord && (
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onInvertWord();
                }}
                disabled={disabled}
              >
                <ArrowLeftRight className="mr-2 h-4 w-4" />
                {t.words.invertWord}
              </DropdownMenuItem>
            )}

            {/* Создать пустую карточку → */}
            {onCreateEmptyCard && (
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onCreateEmptyCard();
                }}
                disabled={disabled}
              >
                <FileText className="mr-2 h-4 w-4" />
                {t.words.createEmptyCard}
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Изображение */}
        {imageUrl && !regeneratingImage && (
          <div 
            className="relative aspect-video w-full overflow-hidden bg-gradient-to-br from-cyan-50 to-pink-50 dark:from-cyan-950/20 dark:to-pink-950/20 cursor-pointer group"
            onClick={handleImageClick}
          >
            <img
              src={imageUrl}
              alt={word}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
            {/* Overlay при наведении */}
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
              <ImageIcon className="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </div>
        )}

        {/* Индикатор загрузки изображения */}
        {regeneratingImage && (
          <div className="relative aspect-video w-full overflow-hidden bg-gradient-to-br from-cyan-50 to-pink-50 dark:from-cyan-950/20 dark:to-pink-950/20 flex items-center justify-center">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-[#4FACFE] animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
              <div className="w-3 h-3 rounded-full bg-[#FF6B9D] animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1s' }}></div>
              <div className="w-3 h-3 rounded-full bg-[#FFD93D] animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1s' }}></div>
            </div>
          </div>
        )}

        {/* Контент карточки */}
        <div className="p-4 space-y-3">
          {/* Слово и перевод */}
          <div className="space-y-1">
            {wordId && onWordUpdate ? (
              <>
                <div>
                  <EditableText
                    value={word}
                    onSave={async (newWord) => {
                      await onWordUpdate(wordId, { original_word: newWord });
                    }}
                    className="font-semibold text-lg text-gray-900 dark:text-gray-100"
                    inputClassName="font-semibold text-lg"
                  />
                </div>
                <div>
                  <EditableText
                    value={translation}
                    onSave={async (newTranslation) => {
                      await onWordUpdate(wordId, { translation: newTranslation });
                    }}
                    className="text-sm text-muted-foreground"
                    inputClassName="text-sm"
                  />
                </div>
              </>
            ) : (
              <>
                <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100">
                  {displayWord(word)}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {translation}
                </p>
              </>
            )}
          </div>

          {/* Медиа контролы */}
          <div className="flex items-center gap-2">
            {/* Аудио плеер */}
            {!regeneratingAudio && audioUrl && audioUrl !== 'null' && audioUrl !== 'undefined' && audioUrl.trim() !== '' && (
              <div className="flex-1">
                <AudioPlayer
                  audioUrl={audioUrl}
                  word={word}
                  compact={false}
                />
              </div>
            )}
            
            {/* Индикатор загрузки аудио */}
            {regeneratingAudio && (
              <div className="flex-1 flex items-center justify-center py-2">
                <div className="flex gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#4FACFE] animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
                  <div className="w-2 h-2 rounded-full bg-[#FF6B9D] animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1s' }}></div>
                  <div className="w-2 h-2 rounded-full bg-[#FFD93D] animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1s' }}></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Модальное окно предпросмотра */}
      {previewImage && (
        <ImagePreviewModal
          isOpen={!!previewImage}
          onClose={() => setPreviewImage(null)}
          imageUrl={previewImage.url}
          word={previewImage.word}
          translation={previewImage.translation}
        />
      )}
    </>
  );
};