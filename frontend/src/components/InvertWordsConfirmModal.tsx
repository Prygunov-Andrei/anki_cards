import React from 'react';
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
import { ArrowLeftRight } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';
import { Deck } from '../types';

interface InvertWordsConfirmModalProps {
  isOpen: boolean;
  deck?: Deck | null;
  onConfirm: () => void;
  onCancel: () => void;
  isSingleWord?: boolean;
}

/**
 * Компонент InvertWordsConfirmModal - модальное окно подтверждения инвертирования слов
 */
export const InvertWordsConfirmModal: React.FC<InvertWordsConfirmModalProps> = ({
  isOpen,
  deck,
  onConfirm,
  onCancel,
  isSingleWord = false,
}) => {
  const t = useTranslation();

  if (!deck && !isSingleWord) return null;

  return (
    <AlertDialog open={isOpen} onOpenChange={onCancel}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center space-x-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-cyan-100 to-pink-100 dark:from-cyan-900/20 dark:to-pink-900/20">
              <ArrowLeftRight className="h-5 w-5 text-cyan-600 dark:text-cyan-500" />
            </div>
            <AlertDialogTitle>
              {isSingleWord ? t.words.invertWordConfirm : t.words.invertAllWordsConfirm}
            </AlertDialogTitle>
          </div>
          <AlertDialogDescription className="pt-2">
            {isSingleWord ? (
              <>
                {t.words.invertWordWarning || 'Это создаст обратную карточку для этого слова. Слово и перевод поменяются местами.'}
              </>
            ) : (
              <>
                {deck && (
                  <span className="block mb-2">
                    {t.decks.deck || 'Колода'}:{' '}
                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                      "{deck.name}"
                    </span>
                  </span>
                )}
                <span className="block mb-2">
                  {t.words.invertAllWordsWarning}
                </span>
                {deck && deck.words_count && (
                  <span className="block font-semibold text-gray-900 dark:text-gray-100">
                    {(() => {
                      // Подсчитываем количество обычных карточек, которые будут инвертированы
                      // Важно: учитываем только те обычные слова, у которых еще нет инвертированной версии в колоде
                      const words = deck.words || [];
                      
                      let normalWordsToInvert = 0;
                      
                      if (words.length > 0 && deck.source_lang && deck.target_lang) {
                        // Фильтруем обычные слова
                        const normalWords = words.filter((w: any) => w.card_type === 'normal' || !w.card_type);
                        
                        // Для каждого обычного слова проверяем, есть ли уже его инвертированная версия
                        normalWordsToInvert = normalWords.filter((normalWord: any) => {
                          // Инвертированная версия = слово, где:
                          // - original_word == translation обычного слова
                          // - translation == original_word обычного слова
                          // - language == source_lang колоды
                          const invertedOriginal = normalWord.translation;
                          const invertedTranslation = normalWord.original_word;
                          
                          // Проверяем, есть ли такое слово в колоде
                          const hasInvertedVersion = words.some((w: any) => 
                            w.original_word === invertedOriginal &&
                            w.translation === invertedTranslation &&
                            w.language === deck.source_lang
                          );
                          
                          return !hasInvertedVersion; // Инвертируем только если инвертированной версии нет
                        }).length;
                      } else if (words.length > 0) {
                        // Если нет source_lang/target_lang, просто считаем все обычные слова
                        normalWordsToInvert = words.filter((w: any) => w.card_type === 'normal' || !w.card_type).length;
                      } else {
                        // Если слов нет в массиве, предполагаем что все слова обычные
                        normalWordsToInvert = deck.words_count;
                      }
                      
                      const currentSize = deck.words_count;
                      const afterInvert = currentSize + normalWordsToInvert; // Текущий размер + новые инвертированные
                      
                      return (
                        <>
                          {t.decks.currentSize || 'Текущий размер'}: {currentSize} {currentSize === 1 ? t.decks.word : t.decks.words}
                          <br />
                          {t.decks.afterInvert || 'После инвертирования'}: {afterInvert} {t.decks.words}
                          {words.length > 0 && normalWordsToInvert < currentSize && (
                            <>
                              <br />
                              <span className="text-sm text-muted-foreground">
                                ({normalWordsToInvert} {t.words.filterNormal.toLowerCase()} {normalWordsToInvert === 1 ? t.words.wordCount : t.words.wordCountMany} {normalWordsToInvert === 1 ? 'будет' : 'будут'} инвертировано)
                              </span>
                            </>
                          )}
                        </>
                      );
                    })()}
                  </span>
                )}
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onCancel}>
            {t.common.cancel}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-gradient-to-r from-cyan-500 to-pink-500 hover:from-cyan-600 hover:to-pink-600"
          >
            {isSingleWord ? t.words.invertWord : t.words.invertAllWords}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};