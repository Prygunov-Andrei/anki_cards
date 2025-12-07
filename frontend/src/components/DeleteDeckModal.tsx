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
import { Deck } from '../types';
import { AlertTriangle } from 'lucide-react';

interface DeleteDeckModalProps {
  isOpen: boolean;
  deck: Deck | null;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Компонент DeleteDeckModal - модальное окно подтверждения удаления колоды
 */
export const DeleteDeckModal: React.FC<DeleteDeckModalProps> = ({
  isOpen,
  deck,
  onConfirm,
  onCancel,
}) => {
  if (!deck) return null;

  return (
    <AlertDialog open={isOpen} onOpenChange={onCancel}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center space-x-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-500" />
            </div>
            <AlertDialogTitle>Удалить колоду?</AlertDialogTitle>
          </div>
          <AlertDialogDescription className="pt-2">
            Вы уверены, что хотите удалить колоду{' '}
            <span className="font-semibold text-gray-900 dark:text-gray-100">
              "{deck.name}"
            </span>
            ? Эта колода содержит {deck.words_count}{' '}
            {deck.words_count === 1
              ? 'слово'
              : deck.words_count < 5
              ? 'слова'
              : 'слов'}
            . Все данные будут удалены безвозвратно.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onCancel}>Отмена</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-red-600 hover:bg-red-700 focus:ring-red-600 dark:bg-red-600 dark:hover:bg-red-700"
          >
            Удалить
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
