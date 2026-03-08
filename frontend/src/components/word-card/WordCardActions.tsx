import React from 'react';
import { Button } from '../ui/button';
import { Trash2, RefreshCw, ImageIcon, MoreVertical, ArrowRight, Volume2, ArrowLeftRight, FileText, Wand2, Sparkles } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuSeparator,
} from '../ui/dropdown-menu';
import { useTranslation } from '../../contexts/LanguageContext';
import { useNavigate } from 'react-router-dom';

interface WordCardActionsProps {
  word: string;
  translation: string;
  imageUrl?: string;
  audioUrl?: string;
  wordId?: number;
  deckId?: number;
  disabled?: boolean;
  regeneratingImage: boolean;
  regeneratingAudio: boolean;
  decksToShow?: { id: number; name: string }[];
  onRegenerateImage?: () => void;
  onRegenerateAudio?: () => void;
  onEditImage?: () => void;
  onDelete?: () => void;
  onDeleteImage?: () => Promise<void>;
  onDeleteAudio?: () => Promise<void>;
  onMoveToDeck?: (deckId: number, deckName: string) => Promise<void>;
  onInvertWord?: () => Promise<void>;
  onCreateEmptyCard?: () => Promise<void>;
}

export const WordCardActions: React.FC<WordCardActionsProps> = ({
  word,
  translation,
  imageUrl,
  audioUrl,
  wordId,
  deckId,
  disabled = false,
  regeneratingImage,
  regeneratingAudio,
  decksToShow,
  onRegenerateImage,
  onRegenerateAudio,
  onEditImage,
  onDelete,
  onDeleteImage,
  onDeleteAudio,
  onMoveToDeck,
  onInvertWord,
  onCreateEmptyCard,
}) => {
  const t = useTranslation();
  const navigate = useNavigate();

  return (
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
        {/* Regenerate submenu */}
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
                    onRegenerateImage();
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
                    onRegenerateAudio();
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

        {/* Edit image */}
        {onEditImage && imageUrl && (
          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              onEditImage();
            }}
            disabled={disabled || regeneratingImage}
          >
            <Wand2 className="mr-2 h-4 w-4" />
            {t.words.editImage}
          </DropdownMenuItem>
        )}

        {/* Delete submenu */}
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
                  {t.words.word}
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

        {/* Move to deck submenu */}
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

        {/* Invert word */}
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

        {/* Create empty card */}
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

        <DropdownMenuSeparator />

        {/* AI content */}
        {wordId && (
          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/words/${wordId}`, {
                state: {
                  deckId,
                  word,
                  translation
                }
              });
            }}
            disabled={disabled}
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {t.words.aiContent}
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
