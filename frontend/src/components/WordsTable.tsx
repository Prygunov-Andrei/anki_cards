import React, { useState } from 'react';
import { Word, Deck } from '../types';
import { Button } from './ui/button';
import { WordCard } from './WordCard';
import { Loader2 } from 'lucide-react';
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

interface WordsTableProps {
  words?: Word[]; // Может быть undefined при загрузке
  deckId?: number; // ID текущей колоды для обновления слов
  onDeleteWord: (wordId: number) => Promise<void>;
  onRegenerateImage?: (wordId: number, word: string, translation: string) => Promise<void>;
  onRegenerateAudio?: (wordId: number, word: string) => Promise<void>;
  onMoveCardToDeck?: (wordId: number, toDeckId: number, toDeckName: string) => Promise<void>;
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
  onMoveCardToDeck,
  onWordUpdate,
  allDecks,
  targetLang,
  sourceLang,
  isGenerating = false,
}) => {
  const [deletingWordId, setDeletingWordId] = useState<number | null>(null);
  const [wordToDelete, setWordToDelete] = useState<Word | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const t = useTranslation();

  /**
   * Открыть диалог удаления
   */
  const openDeleteDialog = (word: Word) => {
    setWordToDelete(word);
    setIsDeleteDialogOpen(true);
  };

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
      {/* Сетка карточек слов */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {words.map((word) => {
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
              onMoveToDeck={
                onMoveCardToDeck && allDecks
                  ? async (toDeckId: number, toDeckName: string) => {
                      await onMoveCardToDeck(word.id, toDeckId, toDeckName);
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