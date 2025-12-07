import React, { useState } from 'react';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { Plus, Loader2 } from 'lucide-react';

interface AddWordFormProps {
  onAddWord: (word: string, translation: string) => Promise<void>;
  targetLang: string;
  sourceLang: string;
}

/**
 * Компонент AddWordForm - форма добавления слова в колоду
 * iOS 25 стиль, оптимизирован для мобильных
 */
export const AddWordForm: React.FC<AddWordFormProps> = ({
  onAddWord,
  targetLang,
  sourceLang,
}) => {
  const [word, setWord] = useState('');
  const [translation, setTranslation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{
    word?: string;
    translation?: string;
  }>({});

  /**
   * Валидация полей
   */
  const validate = (): boolean => {
    const newErrors: { word?: string; translation?: string } = {};

    if (!word.trim()) {
      newErrors.word = 'Введите слово';
    } else if (word.trim().length < 1) {
      newErrors.word = 'Слово слишком короткое';
    } else if (word.trim().length > 100) {
      newErrors.word = 'Слово слишком длинное (макс. 100 символов)';
    }

    if (!translation.trim()) {
      newErrors.translation = 'Введите перевод';
    } else if (translation.trim().length < 1) {
      newErrors.translation = 'Перевод слишком короткий';
    } else if (translation.trim().length > 100) {
      newErrors.translation = 'Перевод слишком длинный (макс. 100 символов)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Отправка формы
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await onAddWord(word.trim(), translation.trim());
      // Очистка полей после успешного добавления
      setWord('');
      setTranslation('');
      setErrors({});
    } catch (error) {
      console.error('Error adding word:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Обработка изменения поля слова
   */
  const handleWordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setWord(e.target.value);
    if (errors.word) {
      setErrors({ ...errors, word: undefined });
    }
  };

  /**
   * Обработка изменения поля перевода
   */
  const handleTranslationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTranslation(e.target.value);
    if (errors.translation) {
      setErrors({ ...errors, translation: undefined });
    }
  };

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          {/* Поле "Слово" */}
          <div className="space-y-2">
            <Label htmlFor="word">
              Слово{' '}
              <span className="text-xs text-muted-foreground">({targetLang})</span>
            </Label>
            <Input
              id="word"
              value={word}
              onChange={handleWordChange}
              placeholder={`Введите слово на ${targetLang}`}
              disabled={isSubmitting}
              className={errors.word ? 'border-destructive' : ''}
            />
            {errors.word && (
              <p className="text-sm text-destructive">{errors.word}</p>
            )}
          </div>

          {/* Поле "Перевод" */}
          <div className="space-y-2">
            <Label htmlFor="translation">
              Перевод{' '}
              <span className="text-xs text-muted-foreground">({sourceLang})</span>
            </Label>
            <Input
              id="translation"
              value={translation}
              onChange={handleTranslationChange}
              placeholder={`Введите перевод на ${sourceLang}`}
              disabled={isSubmitting}
              className={errors.translation ? 'border-destructive' : ''}
            />
            {errors.translation && (
              <p className="text-sm text-destructive">{errors.translation}</p>
            )}
          </div>
        </div>

        {/* Кнопка добавления */}
        <div className="flex justify-end">
          <Button
            type="submit"
            disabled={isSubmitting || !word.trim() || !translation.trim()}
            className="w-full sm:w-auto"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Добавление...
              </>
            ) : (
              <>
                <Plus className="mr-2 h-4 w-4" />
                Добавить слово
              </>
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
};
