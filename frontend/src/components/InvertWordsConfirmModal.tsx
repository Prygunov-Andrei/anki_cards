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
import { Deck, Word } from '../types';

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
                      // Подсчитываем количество обычных слов, для которых будут созданы
                      // инвертированные Card-ы (Card-level инверсия, без создания новых Word-ов)
                      const words = deck.words || [];
                      
                      let normalWordsToInvert = 0;
                      
                      if (words.length > 0) {
                        // Считаем только обычные слова (не legacy inverted/empty)
                        normalWordsToInvert = words.filter((w: Word) => 
                          w.card_type === 'normal' || !w.card_type
                        ).length;
                      } else {
                        normalWordsToInvert = deck.words_count;
                      }
                      
                      return (
                        <>
                          {t.decks.currentSize || 'Текущий размер'}: {deck.words_count} {deck.words_count === 1 ? t.decks.word : t.decks.words}
                          <br />
                          {normalWordsToInvert} {normalWordsToInvert === 1 ? t.decks.word : t.words.wordCountMany}{' '}
                          {t.decks.afterInvert || 'получат инвертированные карточки'}
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