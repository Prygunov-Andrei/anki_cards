import { useState, useEffect, useRef } from 'react';
import { WordTranslationPair } from '../components/TranslationTable';
import { deckService } from '../services/deck.service';
import { germanService } from '../services/german.service';
import { wordsService } from '../services/words.service';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { logger } from '../utils/logger';

interface UseAutoTranslateParams {
  words: string[];
  translations: WordTranslationPair[];
  setWords: (words: string[]) => void;
  setTranslations: (pairs: WordTranslationPair[]) => void;
  setWordIds: (ids: Record<string, number>) => void;
  updateGeneratedImages: (fn: (prev: Record<string, string>) => Record<string, string>) => void;
  updateGeneratedAudio: (fn: (prev: Record<string, string>) => Record<string, string>) => void;
  targetLang: string;
  sourceLang: string;
  userLanguage: string;
  isGenerating: boolean;
  isProcessingWords: boolean;
  t: Record<string, any>;
}

interface UseAutoTranslateReturn {
  isTranslating: boolean;
  isProcessingWords: boolean;
  handleWordsChange: (newWords: string[]) => Promise<void>;
  handleAutoTranslate: () => Promise<void>;
}

export function useAutoTranslate({
  words,
  translations,
  setWords,
  setTranslations,
  setWordIds,
  updateGeneratedImages,
  updateGeneratedAudio,
  targetLang,
  sourceLang,
  userLanguage,
  isGenerating,
  isProcessingWords: externalIsProcessingWords,
  t,
}: UseAutoTranslateParams): UseAutoTranslateReturn {
  const [isTranslating, setIsTranslating] = useState(false);
  const [isProcessingWords, setIsProcessingWords] = useState(false);

  // Debounced auto-translate effect
  const autoTranslateTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (isTranslating || isProcessingWords || externalIsProcessingWords || isGenerating) return;
    if (translations.length === 0) return;
    const hasUntranslated = translations.some(p => p.word.trim() && !p.translation.trim());
    if (!hasUntranslated) return;

    if (autoTranslateTimerRef.current) clearTimeout(autoTranslateTimerRef.current);
    autoTranslateTimerRef.current = setTimeout(() => {
      handleAutoTranslate();
    }, 500);

    return () => {
      if (autoTranslateTimerRef.current) clearTimeout(autoTranslateTimerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [translations, isTranslating, isProcessingWords, externalIsProcessingWords, isGenerating]);

  /**
   * Handle word changes from WordChipsInput.
   * Processes German words if needed, then updates translations array.
   */
  const handleWordsChange = async (newWords: string[]) => {
    setWords(newWords);

    let processedWords = newWords;
    if (targetLang === 'de' && newWords.length > words.length) {
      const addedWords = newWords.filter((w) => !words.includes(w));

      if (addedWords.length > 0) {
        try {
          const wordsToProcess = addedWords.filter((word) => {
            if (word.includes('(') || word.includes('[') || word.includes('{')) {
              return false;
            }
            const trimmedWord = word.trim();
            const wordParts = trimmedWord.split(/\s+/);
            if (wordParts.length > 1) {
              logger.log(`Skipping phrase: "${word}"`);
              return false;
            }
            return true;
          });

          if (wordsToProcess.length > 0) {
            setIsProcessingWords(true);
            try {
              const processed = await germanService.processGermanWords({
                words: wordsToProcess,
              } as any);

              processedWords = newWords.map((word) =>
                processed[word] ? processed[word] : word
              );
              setWords(processedWords);
            } catch (error) {
              logger.error('Error processing German words:', error);
            } finally {
              setIsProcessingWords(false);
            }
          }
        } catch (error) {
          logger.error('Error processing German words:', error);
          setIsProcessingWords(false);
        }
      }
    }

    setTranslations(processedWords.map((word) => {
      const existing = translations.find((t) => t.word === word);
      return existing || { word, translation: '' };
    }));
  };

  /**
   * Auto-translate words with retry logic and bulk word creation.
   */
  const handleAutoTranslate = async () => {
    if (words.length === 0) {
      showError(t.toast.addWordsToTranslate);
      return;
    }

    logger.log('[AutoTranslate] words:', words);
    logger.log('[AutoTranslate] translations:', translations);

    const wordsToTranslate = translations
      .filter((pair) => !pair.translation.trim())
      .map((pair) => pair.word);

    logger.log('[AutoTranslate] wordsToTranslate:', wordsToTranslate);

    if (wordsToTranslate.length === 0) {
      showInfo(t.toast.allTranslationsFilled);
      return;
    }

    logger.log('Sending for translation:', wordsToTranslate);
    logger.log('Word lengths:', wordsToTranslate.map(w => `"${w}": ${w.length} chars`));

    setIsTranslating(true);
    showInfo(t.toast.autoTranslating, {
      description: `${t.toast.translatingWords} ${wordsToTranslate.length} ${wordsToTranslate.length === 1 ? t.toast.word : t.toast.words}...`,
    });

    try {
      let allTranslationsDict: Record<string, string> = {};

      // First attempt
      const translatedWords = await deckService.translateWords({
        words: wordsToTranslate,
        source_language: targetLang,
        target_language: sourceLang,
      });

      const translationsDict = translatedWords.translations || {};

      logger.log('Received translations:', translationsDict);
      logger.log('Translation count:', Object.keys(translationsDict).length);

      allTranslationsDict = { ...allTranslationsDict, ...translationsDict };

      // Check for untranslated words
      const untranslatedWords = wordsToTranslate.filter((word) => {
        if (allTranslationsDict[word]) return false;
        if (word.includes('(')) {
          const wordWithoutParens = word.split('(')[0].trim();
          if (allTranslationsDict[wordWithoutParens]) return false;
        }
        return true;
      });

      // Retry for untranslated words
      if (untranslatedWords.length > 0) {
        logger.log(`Retry translation for ${untranslatedWords.length} words:`, untranslatedWords);
        logger.log('Untranslated word lengths:', untranslatedWords.map(w => `"${w}": ${w.length} chars`));

        try {
          const retryResult = await deckService.translateWords({
            words: untranslatedWords,
            source_language: targetLang,
            target_language: sourceLang,
          });

          const retryTranslationsDict = retryResult.translations || {};

          logger.log('Received retry translations:', retryTranslationsDict);
          logger.log('Retry keys:', Object.keys(retryTranslationsDict));

          allTranslationsDict = { ...allTranslationsDict, ...retryTranslationsDict };
        } catch (retryError) {
          logger.error('Error during retry translation:', retryError);
        }
      }

      logger.log('All collected translations:', allTranslationsDict);

      // Find translation for a word (with fallback strategies)
      const findTranslation = (word: string): string | null => {
        if (allTranslationsDict[word]) {
          return allTranslationsDict[word];
        }

        if (word.includes('(')) {
          const wordWithoutParens = word.split('(')[0].trim();
          if (allTranslationsDict[wordWithoutParens]) {
            return allTranslationsDict[wordWithoutParens];
          }
        }

        for (const [key, value] of Object.entries(allTranslationsDict)) {
          if (key.includes(word)) {
            logger.log(`Found translation in compound key: "${key}" -> "${value}"`);
            return value;
          }
        }

        return null;
      };

      const updatedTranslations = translations.map((pair) => {
        if (!pair.translation.trim()) {
          const translation = findTranslation(pair.word);

          if (translation) {
            logger.log(`Translation applied: ${pair.word} -> ${translation}`);
            return { ...pair, translation };
          } else {
            logger.warn(`Translation not found for: ${pair.word}`);
          }
        }
        return pair;
      });
      setTranslations(updatedTranslations);

      const translatedCount = Object.keys(allTranslationsDict).length;

      showSuccess(t.toast.wordsTranslated, {
        description: `${t.toast.translated} ${translatedCount} ${translatedCount === 1 ? t.toast.word : t.toast.words}`,
      });

      const stillUntranslated = wordsToTranslate.filter(word => !findTranslation(word));
      if (stillUntranslated.length > 0) {
        logger.warn(`Could not translate ${stillUntranslated.length} words:`, stillUntranslated);
      }

      // Переводы уже в таблице — убираем спиннер сразу
      setIsTranslating(false);

      // Bulk-create words on backend and remember their IDs (фоново)
      try {
        const language = userLanguage;
        const bulkPayload = updatedTranslations
          .filter(p => p.word.trim())
          .map(p => ({ original_word: p.word, translation: p.translation, language }));
        if (bulkPayload.length > 0) {
          const result = await wordsService.bulkCreate(bulkPayload);
          const ids: Record<string, number> = {};
          const images: Record<string, string> = {};
          const audio: Record<string, string> = {};
          for (const w of result.words) {
            ids[w.original_word] = w.id;
            if (w.has_image && w.image_url) images[w.original_word] = w.image_url;
            if (w.has_audio && w.audio_url) audio[w.original_word] = w.audio_url;
          }
          setWordIds(ids);
          if (Object.keys(images).length > 0) updateGeneratedImages(prev => ({ ...prev, ...images }));
          if (Object.keys(audio).length > 0) updateGeneratedAudio(prev => ({ ...prev, ...audio }));
        }
      } catch (err) {
        logger.warn('bulk-create failed (non-critical):', err);
      }

    } catch (error) {
      logger.error('Error auto-translating:', error);
      showError(t.toast.couldNotTranslate, {
        description: t.toast.tryAgain,
      });
    } finally {
      setIsTranslating(false);
    }
  };

  return {
    isTranslating,
    isProcessingWords,
    handleWordsChange,
    handleAutoTranslate,
  };
}
