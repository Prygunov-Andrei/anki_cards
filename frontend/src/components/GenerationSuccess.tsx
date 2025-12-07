import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { CheckCircle2, FolderOpen, Edit } from 'lucide-react';

interface GenerationSuccessProps {
  deckName: string;
  deckId?: number | null;
  wordsCount: number;
}

/**
 * Компонент GenerationSuccess - карточка с результатом генерации
 * Показывается после успешной генерации колоды
 * iOS 25 стиль, оптимизирован для мобильных
 */
export const GenerationSuccess: React.FC<GenerationSuccessProps> = ({
  deckName,
  deckId,
  wordsCount,
}) => {
  if (!deckId) return null;

  return (
    <Card className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-800">
      <div className="flex flex-col items-center text-center space-y-4">
        {/* Иконка успеха */}
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
          <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" />
        </div>

        {/* Заголовок */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Колода сохранена!
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Колода "{deckName}" с {wordsCount} {wordsCount === 1 ? 'словом' : wordsCount < 5 ? 'словами' : 'словами'} доступна для редактирования
          </p>
        </div>

        {/* Кнопки навигации */}
        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <Button
            asChild
            variant="default"
            className="gap-2"
          >
            <Link to={`/decks/${deckId}`}>
              <Edit className="h-4 w-4" />
              Открыть в редакторе
            </Link>
          </Button>
          <Button
            asChild
            variant="outline"
            className="gap-2"
          >
            <Link to="/decks">
              <FolderOpen className="h-4 w-4" />
              Перейти в Мои колоды
            </Link>
          </Button>
        </div>
      </div>
    </Card>
  );
};
