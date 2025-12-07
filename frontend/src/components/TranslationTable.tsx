import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Trash2, Languages } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';
import { EditableText } from './EditableText';

export interface WordTranslationPair {
  word: string;
  translation: string;
}

// Внутренний тип с ID для стабильных ключей
interface WordTranslationPairWithId extends WordTranslationPair {
  _id: string;
}

interface TranslationTableProps {
  words: string[];
  translations?: WordTranslationPair[];
  onTranslationsChange: (pairs: WordTranslationPair[]) => void;
  targetLang: string;
  sourceLang: string;
  disabled?: boolean;
  // Медиа файлы для фильтрации (показываем только слова БЕЗ медиа)
  imageFiles?: Record<string, string>;
  audioFiles?: Record<string, string>;
}

/**
 * Компонент TranslationTable - компактная таблица слов с редактируемыми переводами
 * Показывает ТОЛЬКО слова, для которых ещё не сгенерированы медиа
 * iOS 25 стиль, оптимизирован для мобильных устройств
 */
export const TranslationTable: React.FC<TranslationTableProps> = ({
  words,
  translations,
  onTranslationsChange,
  targetLang,
  sourceLang,
  disabled = false,
  imageFiles = {},
  audioFiles = {},
}) => {
  const [pairs, setPairs] = useState<WordTranslationPairWithId[]>([]);
  const t = useTranslation();

  /**
   * Инициализация пар при изменении списка слов или переводов
   */
  useEffect(() => {
    // Если переданы переводы извне, используем их напрямую
    if (translations && translations.length > 0) {
      // УМНОЕ обновление: сохраняем _id для стабильности React keys
      setPairs((prevPairs) => {
        // Создаем Map для быстрого поиска по индексу и слову
        // Ключ: `${word}-${index}` для поддержки дубликатов
        const prevPairsMap = new Map(prevPairs.map((p, idx) => [`${p.word}-${idx}`, p]));
        
        // Обновляем пары с сохранением _id
        const updatedPairs = translations.map((newPair, index) => {
          const key = `${newPair.word}-${index}`;
          const existingPair = prevPairsMap.get(key);
          
          // ВСЕГДА сохраняем _id от существующей пары (для стабильных React keys)
          // Используем индекс для уникальности даже при дубликатах слов
          return {
            ...newPair,
            _id: existingPair?._id || `${newPair.word}-${index}-${Date.now()}-${Math.random()}`,
          };
        });
        
        console.log('🔄 TranslationTable: обновление pairs', {
          prevCount: prevPairs.length,
          newCount: updatedPairs.length,
          idsPreserved: updatedPairs.filter((p, idx) => prevPairsMap.has(`${p.word}-${idx}`)).length,
        });
        
        return updatedPairs;
      });
      return;
    }

    // Иначе создаем новые пары для слов с пустыми переводами
    const newPairs = words.map((word, index) => ({ 
      word, 
      translation: '', 
      _id: `${word}-${index}-${Date.now()}-${Math.random()}` 
    }));
    setPairs(newPairs);
  }, [words, translations]);

  /**
   * Удаление пары по _id (вместо слова, чтобы поддерживать дубликаты)
   */
  const handleRemovePairById = (id: string) => {
    const newPairs = pairs.filter((pair) => pair._id !== id);
    setPairs(newPairs);
    onTranslationsChange(newPairs.map((pair) => ({ word: pair.word, translation: pair.translation })));
  };

  /**
   * Обновление слова по _id (находим по _id вместо слова)
   */
  const handleWordChangeById = (id: string, newWord: string) => {
    const newPairs = pairs.map((pair) =>
      pair._id === id ? { ...pair, word: newWord } : pair
    );
    setPairs(newPairs);
    onTranslationsChange(newPairs.map((pair) => ({ word: pair.word, translation: pair.translation })));
  };

  /**
   * Обновление перевода по _id
   */
  const handleTranslationChangeById = (id: string, translation: string) => {
    const newPairs = pairs.map((pair) =>
      pair._id === id ? { ...pair, translation } : pair
    );
    setPairs(newPairs);
    onTranslationsChange(newPairs.map((pair) => ({ word: pair.word, translation: pair.translation })));
  };

  // Фильтруем слова - показываем только те, для которых НЕТ медиа
  const pairsWithoutMedia = pairs.filter(
    (pair) => !imageFiles[pair.word] && !audioFiles[pair.word]
  );

  // Пустое состояние
  if (words.length === 0 || pairs.length === 0) {
    return (
      <Card className="p-8">
        <div className="flex flex-col items-center justify-center text-center">
          <div className="mb-4 rounded-full bg-gradient-to-br from-cyan-400 to-pink-400 p-4">
            <Languages className="h-8 w-8 text-white" />
          </div>
          <h3 className="mb-2 text-lg font-medium">{t.words.enterWordsHere}</h3>
          <p className="text-sm text-muted-foreground">
            {t.words.addWordsAbove}
          </p>
        </div>
      </Card>
    );
  }

  // Если все слова уже имеют медиа, не показываем таблицу
  if (pairsWithoutMedia.length === 0) {
    return null;
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Заголовок */}
        <div className="flex items-center gap-2">
          <Languages className="h-5 w-5 text-pink-500" />
          <h3 className="font-semibold">{t.words.reviewTranslations}</h3>
        </div>

        {/* Таблица - Desktop версия (скрыта на мобильных) */}
        <div className="hidden md:block overflow-x-auto rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12 text-center">№</TableHead>
                <TableHead className="max-w-[250px]">
                  {t.words.word}
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({t.languageNames[targetLang as keyof typeof t.languageNames] || targetLang})
                  </span>
                </TableHead>
                <TableHead className="max-w-[250px]">
                  {t.words.translation}
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({t.languageNames[sourceLang as keyof typeof t.languageNames] || sourceLang})
                  </span>
                </TableHead>
                <TableHead className="w-16 text-center sticky right-0 bg-background shadow-[-4px_0_8px_rgba(0,0,0,0.05)]">
                  <span className="sr-only">{t.words.actions}</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pairsWithoutMedia.map((pair, displayIndex) => (
                <TableRow key={pair._id}>
                  {/* Номер */}
                  <TableCell className="text-center font-medium text-muted-foreground">
                    {displayIndex + 1}
                  </TableCell>

                  {/* Слово */}
                  <TableCell className="font-medium max-w-[250px]">
                    <div className="break-words whitespace-normal">
                      <EditableText
                        value={pair.word}
                        onSave={async (newWord) => {
                          handleWordChangeById(pair._id, newWord);
                        }}
                        placeholder={t.words.enterWordPlaceholder}
                        className="font-medium"
                      />
                    </div>
                  </TableCell>

                  {/* Перевод (редактируемый) */}
                  <TableCell className="max-w-[250px]">
                    <div className="break-words whitespace-normal">
                      <EditableText
                        value={pair.translation}
                        onSave={async (newTranslation) => {
                          handleTranslationChangeById(pair._id, newTranslation);
                        }}
                        placeholder={t.words.enterTranslationPlaceholder}
                        className=""
                      />
                    </div>
                  </TableCell>

                  {/* Кнопка удаления - sticky справа */}
                  <TableCell className="sticky right-0 bg-background shadow-[-4px_0_8px_rgba(0,0,0,0.05)]">
                    <div className="flex items-center justify-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemovePairById(pair._id)}
                        disabled={disabled}
                        className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10 hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Мобильная версия - карточки (показывается только на мобильных) */}
        <div className="md:hidden space-y-2">
          {pairsWithoutMedia.map((pair, displayIndex) => (
            <div
              key={pair._id}
              className="flex items-start gap-3 rounded-lg border bg-background p-3"
            >
              {/* Номер */}
              <div className="flex-shrink-0 pt-1">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground">
                  {displayIndex + 1}
                </span>
              </div>

              {/* Слово и перевод */}
              <div className="flex-1 space-y-2">
                {/* Слово */}
                <div>
                  <div className="mb-1 text-xs text-muted-foreground">
                    {t.words.word} ({t.languageNames[targetLang as keyof typeof t.languageNames] || targetLang})
                  </div>
                  <EditableText
                    value={pair.word}
                    onSave={async (newWord) => {
                      handleWordChangeById(pair._id, newWord);
                    }}
                    placeholder={t.words.enterWordPlaceholder}
                    className="font-medium"
                  />
                </div>

                {/* Перевод */}
                <div>
                  <div className="mb-1 text-xs text-muted-foreground">
                    {t.words.translation} ({t.languageNames[sourceLang as keyof typeof t.languageNames] || sourceLang})
                  </div>
                  <EditableText
                    value={pair.translation}
                    onSave={async (newTranslation) => {
                      handleTranslationChangeById(pair._id, newTranslation);
                    }}
                    placeholder={t.words.enterTranslationPlaceholder}
                    className=""
                  />
                </div>
              </div>

              {/* Кнопка удаления */}
              <div className="flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemovePairById(pair._id)}
                  disabled={disabled}
                  className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10 hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>

        {/* Подсказка */}
        <p className="text-xs text-muted-foreground">
          {t.words.editTranslationsHint}
        </p>
      </div>
    </Card>
  );
};