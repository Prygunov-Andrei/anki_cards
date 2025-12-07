import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { WordChipsInput } from './WordChipsInput';
import { TranslationTable } from './TranslationTable';
import { Plus, Loader2, Languages } from 'lucide-react';
import { deckService } from '../services/deck.service';
import { showError } from '../utils/toast-helpers';
import { useTranslation } from '../contexts/LanguageContext';

export interface WordTranslationPair {
  word: string;
  translation: string;
}

interface SmartWordInputProps {
  targetLang: string; // Код языка (например, "de", "en")
  sourceLang: string; // Код языка (например, "ru", "en")
  onAddWords: (pairs: WordTranslationPair[]) => Promise<void>;
  showChipsInput?: boolean; // Показывать ли ввод чипсов (для массового добавления)
  singleWordMode?: boolean; // Режим одного слова (для старой формы)
}

/**
 * Универсальный компонент для ввода слов с:
 * - Автопереводом
 * - Обработкой немецких слов (артикли, капитализация)
 * - Поддержкой массового ввода через чипсы
 * - Поддержкой одиночного ввода через форму
 */
export const SmartWordInput: React.FC<SmartWordInputProps> = ({
  targetLang,
  sourceLang,
  onAddWords,
  showChipsInput = true,
  singleWordMode = false,
}) => {
  const [words, setWords] = useState<string[]>([]);
  const [translations, setTranslations] = useState<WordTranslationPair[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const t = useTranslation();

  // Получаем переведенные названия языков
  const getLanguageName = (code: string): string => {
    return t.languageNames[code as keyof typeof t.languageNames] || code.toUpperCase();
  };

  const targetLangName = getLanguageName(targetLang);
  const sourceLangName = getLanguageName(sourceLang);

  /**
   * Обработка немецких слов (добавление артиклей и капитализация)
   * Пропускаем слова, которые уже содержат скобки (формы глаголов, указанные артикли)
   * Пропускаем словосочетания и предложения (более одного слова)
   */
  const processGermanWords = async (rawWords: string[]) => {
    if (targetLang !== 'de' || rawWords.length === 0) {
      return rawWords;
    }

    setIsProcessing(true);
    try {
      const processedWords = await Promise.all(
        rawWords.map(async (word) => {
          // Если слово содержит скобки, не обрабатываем его
          // (пользователь уже указал формы глагола или артикль)
          if (word.includes('(') || word.includes('[') || word.includes('{')) {
            return word;
          }
          
          // ✅ НОВАЯ ПРОВЕРКА: Пропускаем словосочетания и предложения
          // Backend обрабатывает только отдельные слова
          const trimmedWord = word.trim();
          const wordParts = trimmedWord.split(/\s+/);
          if (wordParts.length > 1) {
            // Это словосочетание или предложение - возвращаем без обработки
            console.log(`⏭️ Пропускаем словосочетание/предложение: "${word}"`);
            return word;
          }
          
          try {
            const { processed_word } = await deckService.processGermanWord(word);
            return processed_word;
          } catch (error) {
            console.error(`Error processing German word "${word}":`, error);
            return word; // Возвращаем оригинал в случае ошибки
          }
        })
      );
      return processedWords;
    } catch (error) {
      console.error('Error processing German words:', error);
      return rawWords;
    } finally {
      setIsProcessing(false);
    }
  };

  /**
   * Обработка изменения списка слов
   */
  const handleWordsChange = async (newWords: string[]) => {
    // Обрабатываем немецкие слова
    const processedWords = await processGermanWords(newWords);
    setWords(processedWords);

    // Создаем пары слово-перевод, сохраняя существующие переводы
    const newTranslations = processedWords.map((word) => {
      const existingPair = translations.find((t) => t.word === word);
      return existingPair || { word, translation: '' };
    });

    setTranslations(newTranslations);
  };

  /**
   * Автоперевод пустых переводов
   */
  const handleAutoTranslate = async () => {
    const wordsToTranslate = translations
      .filter((pair) => !pair.translation.trim())
      .map((pair) => pair.word);

    if (wordsToTranslate.length === 0) {
      showError(t.words.allTranslationsFilled, {
        description: t.words.noEmptyTranslations,
      });
      return;
    }

    setIsTranslating(true);
    try {
      const result = await deckService.translateWords({
        words: wordsToTranslate,
        source_language: targetLang,
        target_language: sourceLang,
      });

      const translationsDict = result.translations || {};

      // Обновляем переводы
      const updatedTranslations = translations.map((pair) => {
        if (!pair.translation.trim()) {
          // Ищем перевод по полному ключу
          let translation = translationsDict[pair.word];
          
          // Если не нашли, пробуем найти по ключу без скобок
          // Например: "rennen (rannte / gerant)" -> "rennen"
          if (!translation && pair.word.includes('(')) {
            const wordWithoutParens = pair.word.split('(')[0].trim();
            translation = translationsDict[wordWithoutParens];
          }
          
          if (translation) {
            return { ...pair, translation };
          }
        }
        return pair;
      });

      setTranslations(updatedTranslations);
    } catch (error) {
      console.error('Error auto-translating:', error);
      showError(t.words.couldNotAutoTranslate, {
        description: t.words.translateManually,
      });
    } finally {
      setIsTranslating(false);
    }
  };

  /**
   * Обработка изменения переводов из таблицы
   */
  const handleTranslationsChange = (newTranslations: WordTranslationPair[]) => {
    setTranslations(newTranslations);
  };

  /**
   * Добавление слов
   */
  const handleSubmit = async () => {
    // Фильтруем только те пары, где есть оба значения
    const validPairs = translations.filter(
      (pair) => pair.word.trim() && pair.translation.trim()
    );

    if (validPairs.length === 0) {
      showError(t.words.fillWordsAndTranslations, {
        description: t.words.addAtLeastOnePair,
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await onAddWords(validPairs);
      // Очищаем форму после успешного добавления
      setWords([]);
      setTranslations([]);
    } catch (error) {
      console.error('Error adding words:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Проверка, можно ли добавить слова
   */
  const canSubmit =
    translations.length > 0 &&
    translations.some((pair) => pair.word.trim() && pair.translation.trim()) &&
    !isSubmitting &&
    !isProcessing &&
    !isTranslating;

  return (
    <div className="space-y-4">
      {/* Ввод слов через чипсы */}
      {showChipsInput && (
        <div className="space-y-2">
          <WordChipsInput
            words={words}
            onChange={handleWordsChange}
            placeholder={`${t.words.enterWordsPlaceholder} ${targetLangName} ${t.words.commaSeparated}`}
            disabled={isProcessing || isSubmitting}
            targetLang={targetLang}
          />
          {isProcessing && (
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              <Loader2 className="h-3 w-3 animate-spin" />
              {t.words.processingWords}
            </p>
          )}
        </div>
      )}

      {/* Таблица переводов */}
      {translations.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">{t.words.translations}</label>
            <Button
              variant="outline"
              size="sm"
              onClick={handleAutoTranslate}
              disabled={
                isTranslating ||
                isSubmitting ||
                translations.every((pair) => pair.translation.trim())
              }
            >
              {isTranslating ? (
                <>
                  <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                  {t.words.translating}
                </>
              ) : (
                <>
                  <Languages className="mr-2 h-3 w-3" />
                  {t.words.autoTranslate}
                </>
              )}
            </Button>
          </div>
          <TranslationTable
            words={words}
            translations={translations}
            onTranslationsChange={handleTranslationsChange}
            targetLang={targetLangName}
            sourceLang={sourceLangName}
            disabled={isSubmitting}
          />
        </div>
      )}

      {/* Кнопка добавления */}
      {translations.length > 0 && (
        <div className="flex justify-end pt-2">
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="w-full sm:w-auto"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.words.adding}
              </>
            ) : (
              <>
                <Plus className="mr-2 h-4 w-4" />
                {t.words.addWords} ({translations.filter(t => t.word.trim() && t.translation.trim()).length})
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
};