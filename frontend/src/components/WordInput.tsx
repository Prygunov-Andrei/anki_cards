import React, { useState, useEffect } from 'react';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Card } from './ui/card';
import { BookOpen } from 'lucide-react';

interface WordInputProps {
  value: string;
  onChange: (value: string) => void;
  onWordsExtracted: (words: string[]) => void;
  disabled?: boolean;
}

/**
 * Компонент WordInput - textarea для ввода слов
 * iOS 25 стиль, оптимизирован для мобильных устройств
 */
export const WordInput: React.FC<WordInputProps> = ({
  value,
  onChange,
  onWordsExtracted,
  disabled = false,
}) => {
  const [wordCount, setWordCount] = useState(0);

  /**
   * Парсинг слов из текста
   */
  const parseWords = (text: string): string[] => {
    if (!text.trim()) return [];

    // Разделяем по запятым или переносам строки
    const words = text
      .split(/[,\n]+/)
      .map((word) => word.trim())
      .filter((word) => word.length > 0);

    return words;
  };

  /**
   * Обновление счетчика при изменении текста
   */
  useEffect(() => {
    const words = parseWords(value);
    setWordCount(words.length);
  }, [value]);

  /**
   * Обработка изменения текста
   */
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  /**
   * Обработка потери фокуса - извлекаем слова
   */
  const handleBlur = () => {
    const words = parseWords(value);
    onWordsExtracted(words);
  };

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Заголовок */}
        <div className="flex items-center justify-between">
          <Label htmlFor="word-input" className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-cyan-500" />
            <span>Введите слова</span>
          </Label>
          {/* Счетчик слов */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="font-medium text-primary">{wordCount}</span>
            <span>
              {wordCount === 0
                ? 'слов'
                : wordCount === 1
                  ? 'слово'
                  : wordCount < 5
                    ? 'слова'
                    : 'слов'}
            </span>
          </div>
        </div>

        {/* Textarea */}
        <Textarea
          id="word-input"
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={disabled}
          placeholder="Введите слова через запятую или с новой строки&#10;Например:&#10;hello&#10;world&#10;или: hello, world, test"
          className="min-h-[160px] resize-none"
        />

        {/* Подсказка */}
        <p className="text-xs text-muted-foreground">
          💡 Слова можно разделять запятыми или переносом строки
        </p>
      </div>
    </Card>
  );
};
