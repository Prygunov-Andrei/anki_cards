import React, { useState, useMemo } from 'react';
import { Word, Deck } from '../types';
import { Button } from './ui/button';
import { WordCard } from './WordCard';
import { Badge } from './ui/badge';
import { Loader2, Filter } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';
import { Card } from './ui/card';
import { BookOpen } from 'lucide-react';
import { getAbsoluteUrl } from '../utils/url-helpers';
import { useTranslation } from '../contexts/LanguageContext';
import { displayWord } from '../utils/helpers';

interface WordsTableProps {
  words?: Word[]; // Может быть undefined при загрузке
  deckId?: number; // ID текущей колоды для обновления слов
  onDeleteWord: (wordId: number) => Promise<void>;
  onRegenerateImage?: (wordId: number, word: string, translation: string) => Promise<void>;
  onRegenerateAudio?: (wordId: number, word: string) => Promise<void>;
  onEditImage?: (wordId: number, mixin: string) => Promise<void>;
  onDeleteImage?: (wordId: number) => Promise<void>;
  onDeleteAudio?: (wordId: number) => Promise<void>;
  onMoveCardToDeck?: (wordId: number, toDeckId: number, toDeckName: string) => Promise<void>;
  onInvertWord?: (wordId: number) => Promise<void>;
  onCreateEmptyCard?: (wordId: number) => Promise<void>;
  onWordUpdate?: (wordId: number, data: { original_word?: string; translation?: string }) => Promise<void>;
  allDecks?: Deck[]; // Список всех колод пользователя
  targetLang: string;
  sourceLang: string;
  isGenerating?: boolean;
}

/**
 * Компонент WordsTable - сетка красивых карточек слов в колоде
 * iOS 25 стиль, оптимизирован для мобильных
 * Использует компонент WordCard для единообразного отображения
 */
export const WordsTable: React.FC<WordsTableProps> = ({
  words,
  deckId,
  onDeleteWord,
  onRegenerateImage,
  onRegenerateAudio,
  onEditImage,
  onDeleteImage,
  onDeleteAudio,
  onMoveCardToDeck,
  onInvertWord,
  onCreateEmptyCard,
  onWordUpdate,
  allDecks,
  targetLang,
  sourceLang,
  isGenerating = false,
}) => {
  const [deletingWordId, setDeletingWordId] = useState<number | null>(null);
  const [wordToDelete, setWordToDelete] = useState<Word | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [cardTypeFilter, setCardTypeFilter] = useState<'all' | 'normal' | 'inverted' | 'empty'>('all');
  const t = useTranslation();

  /**
   * Открыть диалог удаления
   */
  const openDeleteDialog = (word: Word) => {
    setWordToDelete(word);
    setIsDeleteDialogOpen(true);
  };

  /**
   * Фильтрация слов по типу карточки
   */
  const filteredWords = useMemo(() => {
    if (!words) return [];
    if (cardTypeFilter === 'all') return words;
    return words.filter((word) => word.card_type === cardTypeFilter);
  }, [words, cardTypeFilter]);

  /**
   * Удалить слово
   */
  const handleDelete = async () => {
    if (!wordToDelete) return;

    setDeletingWordId(wordToDelete.id);
    try {
      await onDeleteWord(wordToDelete.id);
      setIsDeleteDialogOpen(false);
      setWordToDelete(null);
    } catch (error) {
      console.error('Error deleting word:', error);
    } finally {
      setDeletingWordId(null);
    }
  };

  // Если слова не загружены или массив пустой
  if (!words || words.length === 0) {
    return (
      <Card className="p-8 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
          <BookOpen className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="mb-2">{t.decks.noWordsYet}</h3>
        <p className="text-sm text-muted-foreground">
          {t.decks.addWordsToStart}
        </p>
      </Card>
    );
  }

  return (
    <>
      {/* Фильтры по типам карточек */}
      {words && words.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Filter className="h-4 w-4" />
            <span>{t.common.filter}:</span>
          </div>
          <Button
            variant={cardTypeFilter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setCardTypeFilter('all')}
            className="h-8"
          >
            {t.words.filterAll}
          </Button>
          <Button
            variant={cardTypeFilter === 'normal' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setCardTypeFilter('normal')}
            className="h-8"
          >
            {t.words.filterNormal}
          </Button>
          <Button
            variant={cardTypeFilter === 'inverted' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setCardTypeFilter('inverted')}
            className="h-8"
          >
            {t.words.filterInverted}
          </Button>
          <Button
            variant={cardTypeFilter === 'empty' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setCardTypeFilter('empty')}
            className="h-8"
          >
            {t.words.filterEmpty}
          </Button>
          {cardTypeFilter !== 'all' && (
            <Badge variant="secondary" className="ml-auto">
              {filteredWords.length} {t.words.wordCountMany}
            </Badge>
          )}
        </div>
      )}

      {/* Сетка карточек слов */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredWords.map((word) => {
          // Fallback для совместимости: backend может возвращать 'word' вместо 'original_word'
          const wordText = word.original_word || (word as any).word || '???';
          const imageUrl = word.image_file ? getAbsoluteUrl(word.image_file) : undefined;
          const audioUrl = word.audio_file ? getAbsoluteUrl(word.audio_file) : undefined;

          return (
            <WordCard
              key={word.id}
              word={wordText}
              translation={word.translation}
              imageUrl={imageUrl}
              audioUrl={audioUrl}
              cardType={word.card_type}
              onDelete={() => openDeleteDialog(word)}
              onRegenerateImage={
                onRegenerateImage
                  ? async () => {
                      await onRegenerateImage(word.id, wordText, word.translation);
                    }
                  : undefined
              }
              onRegenerateAudio={
                onRegenerateAudio
                  ? async () => {
                      await onRegenerateAudio(word.id, wordText);
                    }
                  : undefined
              }
              onEditImage={
                onEditImage
                  ? async (mixin: string) => {
                      await onEditImage(word.id, mixin);
                    }
                  : undefined
              }
              onDeleteImage={
                onDeleteImage
                  ? async () => {
                      await onDeleteImage(word.id);
                    }
                  : undefined
              }
              onDeleteAudio={
                onDeleteAudio
                  ? async () => {
                      await onDeleteAudio(word.id);
                    }
                  : undefined
              }
              onMoveToDeck={
                onMoveCardToDeck && allDecks
                  ? async (toDeckId: number, toDeckName: string) => {
                      await onMoveCardToDeck(word.id, toDeckId, toDeckName);
                    }
                  : undefined
              }
              onInvertWord={
                onInvertWord
                  ? async () => {
                      await onInvertWord(word.id);
                    }
                  : undefined
              }
              onCreateEmptyCard={
                onCreateEmptyCard
                  ? async () => {
                      await onCreateEmptyCard(word.id);
                    }
                  : undefined
              }
              onWordUpdate={
                onWordUpdate && deckId
                  ? async (wordId: number, data: { original_word?: string; translation?: string }) => {
                      await onWordUpdate(wordId, data);
                    }
                  : undefined
              }
              wordId={word.id}
              deckId={deckId}
              allDecks={allDecks}
              disabled={isGenerating || deletingWordId === word.id}
            />
          );
        })}
      </div>

      {/* Диалог подтверждения удаления */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.words.deleteWord}?</AlertDialogTitle>
            <AlertDialogDescription>
              {t.decks.confirmDeleteWord}{' '}
              <span className="font-semibold">
                "{wordToDelete?.original_word}"
              </span>
              ? {t.decks.cannotUndo}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deletingWordId ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.decks.deleting}
                </>
              ) : (
                t.common.delete
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};