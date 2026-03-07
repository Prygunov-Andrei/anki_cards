import React, { useState, useEffect, useRef } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { WordChipsInput } from '../components/WordChipsInput';
import { PhotoWordExtractor } from '../components/PhotoWordExtractor';
import { TranslationTable, WordTranslationPair } from '../components/TranslationTable';
import { GeneratedWordsGrid } from '../components/GeneratedWordsGrid';
import { InsufficientTokensModal } from '../components/InsufficientTokensModal';
import { ImageStyle } from '../components/ImageStyleSelector';
import { GenerationProgress, GenerationStatus } from '../components/GenerationProgress';
import { GenerationSuccess } from '../components/GenerationSuccess';
import { TokenCostBadge } from '../components/TokenCostBadge';
import { CompactLiterarySourceSelector } from '../components/literary-context/CompactLiterarySourceSelector';
import { useTokenContext } from '../contexts/TokenContext';
import { useAuthContext } from '../contexts/AuthContext';
import { useTranslation } from '../contexts/LanguageContext';
import { useDraftDeck } from '../contexts/DraftDeckContext';
import { deckService } from '../services/deck.service';
import { wordsService } from '../services/words.service';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { getCardImageUrl, getAudioUrl, getRelativePath } from '../utils/url-helpers';
import { getTotalMediaCost } from '../utils/token-formatting';
import { Download, Loader2, Sparkles, ImageIcon, Volume2 } from 'lucide-react';
import { literaryContextService } from '../services/literary-context.service';
import { LiterarySource } from '../types/literary-context';
import { PageHelpButton } from '../components/PageHelpButton';

/**
 * Главная страница - быстрая генерация карточек
 * iOS 25 стиль, оптимизирован для мобильных
 */
export default function MainPage() {
  const t = useTranslation();
  const { balance, checkBalance, refreshBalance } = useTokenContext();
  const { user, updateUser } = useAuthContext();

  // Персистентное состояние формы (выживает навигацию и refresh)
  const {
    words, setWords,
    translations: draftTranslations, setTranslations: setDraftTranslations,
    wordIds, setWordIds,
    generatedImages, setGeneratedImages, updateGeneratedImages,
    generatedAudio, setGeneratedAudio, updateGeneratedAudio,
    deckName, setDeckName,
    generateImages, setGenerateImages,
    generateAudio, setGenerateAudio,
    clearDraft,
  } = useDraftDeck();

  // Адаптер: DraftTranslationPair[] <-> WordTranslationPair[] (TranslationTable требует WordTranslationPair)
  const translations: WordTranslationPair[] = draftTranslations;
  const setTranslations = (pairs: WordTranslationPair[]) => {
    setDraftTranslations(pairs.map(p => ({ word: p.word, translation: p.translation })));
  };

  // Литературные источники для auto-naming
  const [literarySources, setLiterarySources] = useState<LiterarySource[]>([]);

  // Провайдеры берутся из профиля пользователя
  const imageStyle: ImageStyle = (user?.image_style as ImageStyle) || 'balanced';
  const imageProvider = user?.image_provider || 'openai';
  const audioProvider = user?.audio_provider || 'openai';
  const geminiModel = user?.gemini_model || 'gemini-2.5-flash-image';

  // Состояния UI
  const [isGenerating, setIsGenerating] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [isProcessingWords, setIsProcessingWords] = useState(false);
  const [showInsufficientTokensModal, setShowInsufficientTokensModal] = useState(false);
  
  // Состояние прогресса генерации
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus>('idle');
  const [generationProgress, setGenerationProgress] = useState({ current: 0, total: 0, currentWord: '' });
  
  // AbortController для отмены генерации
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  
  // Все колоды теперь автоматически сохраняются в "Мои колоды"
  const [savedDeckId, setSavedDeckId] = useState<number | null>(null);

  // Ref для очистки таймера сброса формы при размонтировании
  const resetTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    return () => {
      if (resetTimerRef.current) clearTimeout(resetTimerRef.current);
    };
  }, []);

  // Автоматический перевод при появлении непереведённых слов
  const autoTranslateTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (isTranslating || isProcessingWords || isGenerating) return;
    if (translations.length === 0) return;
    const hasUntranslated = translations.some(p => p.word.trim() && !p.translation.trim());
    if (!hasUntranslated) return;

    // Debounce: ждём 500мс после последнего изменения, чтобы не дёргать API на каждый чип
    if (autoTranslateTimerRef.current) clearTimeout(autoTranslateTimerRef.current);
    autoTranslateTimerRef.current = setTimeout(() => {
      handleAutoTranslate();
    }, 500);

    return () => {
      if (autoTranslateTimerRef.current) clearTimeout(autoTranslateTimerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [translations, isTranslating, isProcessingWords, isGenerating]);

  // Защита от закрытия вкладки во время генерации
  useEffect(() => {
    if (!isGenerating) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isGenerating]);

  // Блокировка навигации через перехват кликов по ссылкам во время генерации
  // (useBlocker требует data router, а приложение использует BrowserRouter)
  // beforeunload выше уже защищает от закрытия вкладки/обновления страницы
  // Данные всё равно персистятся в localStorage, так что навигация безопасна

  // При восстановлении черновика с wordIds — проверяем медиа на сервере
  useEffect(() => {
    const ids = Object.values(wordIds);
    if (ids.length === 0) return;
    wordsService.checkMedia(ids).then(result => {
      const images: Record<string, string> = {};
      const audio: Record<string, string> = {};
      for (const w of result.words) {
        if (w.has_image && w.image_url) images[w.original_word] = w.image_url;
        if (w.has_audio && w.audio_url) audio[w.original_word] = w.audio_url;
      }
      if (Object.keys(images).length > 0) updateGeneratedImages(prev => ({ ...prev, ...images }));
      if (Object.keys(audio).length > 0) updateGeneratedAudio(prev => ({ ...prev, ...audio }));
    }).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Только при маунте

  // Уведомление о восстановлении черновика
  const draftNotifiedRef = useRef(false);
  useEffect(() => {
    if (draftNotifiedRef.current) return;
    if (words.length > 0) {
      draftNotifiedRef.current = true;
      showInfo(t.draft.restored, {
        description: `${words.length} ${t.draft.restoredDescription}`,
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Только при маунте

  // Загружаем литературные источники для авто-названия
  useEffect(() => {
    literaryContextService
      .getSources()
      .then(setLiterarySources)
      .catch(() => {});
  }, []);

  // Авто-название колоды
  const getDefaultDeckName = () => {
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    if (user?.active_literary_source && literarySources.length > 0) {
      const src = literarySources.find(s => s.slug === user.active_literary_source);
      return src ? `${src.name}_${date}` : `Deck_${date}`;
    }
    return `${t.decks.newDeck}_${date}`;
  };

  // Инициализируем deckName при изменении источника
  useEffect(() => {
    if (!deckName) {
      setDeckName(getDefaultDeckName());
    }
  }, [user?.active_literary_source, literarySources]);

  // Языки берем из профиля пользователя
  const targetLang = user?.learning_language || 'en';
  const sourceLang = user?.native_language || 'ru';

  /**
   * Вспомогательная функция для конвертации imageProvider в формат бекенда
   * nano-banana это на самом деле Gemini с моделью nano-banana-pro-preview
   */
  const getProviderParams = () => {
    if (imageProvider === 'openai') {
      return { provider: 'openai' as const, gemini_model: undefined };
    }
    if (imageProvider === 'gemini') {
      return { provider: 'gemini' as const, gemini_model: geminiModel as 'gemini-2.5-flash-image' | 'nano-banana-pro-preview' };
    }
    if (imageProvider === 'nano-banana') {
      return { provider: 'gemini' as const, gemini_model: 'nano-banana-pro-preview' as const };
    }
    return { provider: 'openai' as const, gemini_model: undefined };
  };


  /**
   * Обработка изменения слов из WordChipsInput
   */
  const handleWordsChange = async (newWords: string[]) => {
    setWords(newWords);
    
    // Если язык немецкий, обрабатываем слова через API
    let processedWords = newWords;
    if (targetLang === 'de' && newWords.length > words.length) {
      // Только для новых слов
      const addedWords = newWords.filter((w) => !words.includes(w));
      
      if (addedWords.length > 0) {
        try {
          // Фильтруем слова: пропускаем те, что уже содержат скобки
          // (формы глаголов, указанны артикли)
          // И пропускаем словосочетания/предложения (более одного слова)
          const wordsToProcess = addedWords.filter((word) => {
            // Пропускаем слова со скобками
            if (word.includes('(') || word.includes('[') || word.includes('{')) {
              return false;
            }
            
            // ✅ НОВАЯ ПРОВЕРКА: Пропускаем словосочетания и предложения
            // Backend обрабатывает только отдельные слова
            const trimmedWord = word.trim();
            const wordParts = trimmedWord.split(/\s+/);
            if (wordParts.length > 1) {
              console.log(`⏭️ Пропускаем словосочетание/предложение: "${word}"`);
              return false;
            }
            
            return true;
          });
          
          if (wordsToProcess.length > 0) {
            setIsProcessingWords(true);
            try {
              const processed = await deckService.processGermanWords({
                words: wordsToProcess,
              });
              
              // Заменяем новые слова на обработанные
              processedWords = newWords.map((word) =>
                processed[word] ? processed[word] : word
              );
              
              // Обновляем state с обработанными словами
              setWords(processedWords);
            } catch (error) {
              console.error('Error processing German words:', error);
              // В случае ошибки просто используем оригинальные слова
            } finally {
              setIsProcessingWords(false);
            }
          }
        } catch (error) {
          console.error('Error processing German words:', error);
          // В случае ошибки просто используем оригинальные слова
          setIsProcessingWords(false);
        }
      }
    }
    
    // Создаем или обновляем массив переводов
    setTranslations(processedWords.map((word) => {
      const existing = translations.find((t) => t.word === word);
      return existing || { word, translation: '' };
    }));
  };

  /**
   * Обработка изменения переводов
   */
  const handleTranslationsChange = (pairs: WordTranslationPair[]) => {
    setTranslations(pairs);
    // Синхронизируем массив words с парами переводов
    setWords(pairs.map(pair => pair.word));
  };

  /**
   * Обработка слов, извлечённых из фото
   */
  const handlePhotoWordsExtracted = (photoWords: string[]) => {
    const existingLower = new Set(words.map((w) => w.toLowerCase()));
    const newWords = photoWords.filter((w) => !existingLower.has(w.toLowerCase()));
    if (newWords.length > 0) {
      handleWordsChange([...words, ...newWords]);
    }
  };

  /**
   * Автоперевод слов
   * С механизмом повторных попыток для непереведенных слов
   */
  const handleAutoTranslate = async () => {
    if (words.length === 0) {
      showError(t.toast.addWordsToTranslate);
      return;
    }

    // Логирование для отладки
    console.log('🔍 [AutoTranslate] words:', words);
    console.log('🔍 [AutoTranslate] translations:', translations);

    // Находим слова без перевода
    const wordsToTranslate = translations
      .filter((pair) => !pair.translation.trim())
      .map((pair) => pair.word);

    console.log('🔍 [AutoTranslate] wordsToTranslate:', wordsToTranslate);

    if (wordsToTranslate.length === 0) {
      showInfo(t.toast.allTranslationsFilled);
      return;
    }

    console.log('📤 Отправляем на перевод:', wordsToTranslate);
    console.log('📊 Длины слов:', wordsToTranslate.map(w => `"${w}": ${w.length} символов`));

    setIsTranslating(true);
    showInfo(t.toast.autoTranslating, {
      description: `${t.toast.translatingWords} ${wordsToTranslate.length} ${wordsToTranslate.length === 1 ? t.toast.word : t.toast.words}...`,
    });

    try {
      // Собираем все переводы из обеих попыток в один объект
      let allTranslationsDict: Record<string, string> = {};
      
      // Первая попытка перевода всех слов
      const translatedWords = await deckService.translateWords({
        words: wordsToTranslate,
        source_language: targetLang,
        target_language: sourceLang,
      });

      // API возвращает {translations: {...}}, поэтому используем translatedWords.translations
      const translationsDict = translatedWords.translations || {};
      
      console.log('📥 Получили переводы:', translationsDict);
      console.log('📊 Количество переводов:', Object.keys(translationsDict).length);

      // Добавляем переводы первой попытки
      allTranslationsDict = { ...allTranslationsDict, ...translationsDict };

      // Проверяем какие слова остались непереведенными
      const untranslatedWords = wordsToTranslate.filter((word) => {
        // Ищем перевод по полному ключу
        if (allTranslationsDict[word]) return false;
        // Пробуем найти по ключу без скобок
        if (word.includes('(')) {
          const wordWithoutParens = word.split('(')[0].trim();
          if (allTranslationsDict[wordWithoutParens]) return false;
        }
        return true;
      });

      // Если есть непереведенные слова, делаем повторную попытку
      if (untranslatedWords.length > 0) {
        console.log(`🔄 Повторная попытка перевода ${untranslatedWords.length} слов:`, untranslatedWords);
        console.log('📊 Длины непереведенных слов:', untranslatedWords.map(w => `"${w}": ${w.length} символов`));
        
        try {
          const retryResult = await deckService.translateWords({
            words: untranslatedWords,
            source_language: targetLang,
            target_language: sourceLang,
          });

          const retryTranslationsDict = retryResult.translations || {};
          
          console.log('📥 Получили переводы при retry:', retryTranslationsDict);
          console.log('🔑 Ключи в ответе:', Object.keys(retryTranslationsDict));

          // Добавляем переводы повторной попытки
          allTranslationsDict = { ...allTranslationsDict, ...retryTranslationsDict };
        } catch (retryError) {
          console.error('Error during retry translation:', retryError);
          // Продолжаем с переводами которые удалось получить при первой попытке
        }
      }

      console.log('📊 Все собранные переводы:', allTranslationsDict);

      // Функция поиска перевода для слова
      const findTranslation = (word: string): string | null => {
        // Ищем перевод по полному ключу
        if (allTranslationsDict[word]) {
          return allTranslationsDict[word];
        }
        
        // Пробуем найти по ключу без скобок
        if (word.includes('(')) {
          const wordWithoutParens = word.split('(')[0].trim();
          if (allTranslationsDict[wordWithoutParens]) {
            return allTranslationsDict[wordWithoutParens];
          }
        }
        
        // Ищем ключи которые содержат наше слово (для составных ключей)
        for (const [key, value] of Object.entries(allTranslationsDict)) {
          if (key.includes(word)) {
            console.log(`✅ Найден перевод в составном ключе: "${key}" -> "${value}"`);
            return value;
          }
        }
        
        return null;
      };

      const updatedTranslations = translations.map((pair) => {
        if (!pair.translation.trim()) {
          const translation = findTranslation(pair.word);

          if (translation) {
            console.log(`✅ Перевод применен: ${pair.word} -> ${translation}`);
            return { ...pair, translation };
          } else {
            console.warn(`⚠️ Перевод не найден для: ${pair.word}`);
          }
        }
        return pair;
      });
      setTranslations(updatedTranslations);

      // Подсчитываем переведенные слова для уведомления
      const translatedCount = Object.keys(allTranslationsDict).length;

      showSuccess(t.toast.wordsTranslated, {
        description: `${t.toast.translated} ${translatedCount} ${translatedCount === 1 ? t.toast.word : t.toast.words}`,
      });

      // Предупреждаем о непереведенных словах
      const stillUntranslated = wordsToTranslate.filter(word => !findTranslation(word));
      if (stillUntranslated.length > 0) {
        console.warn(`⚠️ Не удалось перевести ${stillUntranslated.length} слов:`, stillUntranslated);
      }

      // Сохраняем слова на бэкенде (bulk-create) и запоминаем их ID
      try {
        const language = user?.learning_language || 'de';
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
          // Восстанавливаем уже существующие медиа
          if (Object.keys(images).length > 0) updateGeneratedImages(prev => ({ ...prev, ...images }));
          if (Object.keys(audio).length > 0) updateGeneratedAudio(prev => ({ ...prev, ...audio }));
        }
      } catch (err) {
        console.warn('bulk-create failed (non-critical):', err);
      }

    } catch (error) {
      console.error('Error auto-translating:', error);
      showError(t.toast.couldNotTranslate, {
        description: t.toast.tryAgain,
      });
    } finally {
      setIsTranslating(false);
    }
  };

  /**
   * Перегенерация изображения для конкретного слова
   */
  const handleRegenerateImage = async (word: string) => {
    const pair = translations.find(t => t.word === word);
    if (!pair) return;

    try {
      showInfo('Генерация изображения...', {
        description: `Создаём новое изображение для "${word}"`,
      });

      const providerParams = getProviderParams();
      
      const { image_url } = await deckService.generateImage({
        word: pair.word,
        translation: pair.translation,
        language: targetLang,
        image_style: imageStyle,
        ...providerParams,
      });

      // Преобразуем в абсолютный URL и сохраняем в state для предпросмотра
      const absoluteUrl = getCardImageUrl(image_url);
      if (absoluteUrl) {
        updateGeneratedImages(prev => ({ ...prev, [pair.word]: absoluteUrl }));
      }

      showSuccess('Изображение обновлено!', {
        description: `Новое изображение для "${word}" готово`,
      });
    } catch (error) {
      console.error(`Error regenerating image for "${word}":`, error);
      showError('Не удалось создать изображение', {
        description: 'Попробуйте ещё раз',
      });
    }
  };

  /**
   * Перегенерация аудио для конкретного слова
   */
  const handleRegenerateAudio = async (word: string) => {
    const pair = translations.find(t => t.word === word);
    if (!pair) return;

    try {
      showInfo('Генерация аудио...', {
        description: `Создаём новое аудио для "${word}"`,
      });

      const provider = audioProvider;

      const { audio_url } = await deckService.generateAudio({
        word: pair.word,
        language: targetLang,
        provider, // Используем выбранный провайдер
      });

      // Преобразуем в абсолютный URL и сохраняем в state для предпросмотра
      const absoluteUrl = getAudioUrl(audio_url);
      if (absoluteUrl) {
        updateGeneratedAudio(prev => ({ ...prev, [pair.word]: absoluteUrl }));
      }

      showSuccess('Аудио обновлено!', {
        description: `Новое аудио для "${word}" готово`,
      });
    } catch (error) {
      console.error(`Error generating audio for "${pair.word}":`, error);
      showError('Не удалось создать аудио', {
        description: 'Попробуйте ещ раз',
      });
    }
  };

  /**
   * Валидация переводов (для генерации медиа)
   */
  const validateTranslations = (): boolean => {
    if (translations.length === 0) {
      showError('Добавьте слова для генерации');
      return false;
    }

    // Проверка, что все переводы заполнены
    const emptyTranslations = translations.filter(
      (pair) => !pair.translation.trim()
    );

    if (emptyTranslations.length > 0) {
      showError('Заполните переводы для всех слов', {
        description: `Не заполнено переводов: ${emptyTranslations.length}`,
      });
      return false;
    }

    // Проверка, что выбран хотя бы один тип медиа
    if (!generateImages && !generateAudio) {
      showError('Выберите хотя бы один тип медиа', {
        description: 'Включите генерацию изображений или аудио',
      });
      return false;
    }

    return true;
  };

  /**
   * Валидация для создания колоды
   */
  const validateDeckCreation = (): boolean => {
    if (!deckName.trim()) {
      showError(t.toast.enterDeckName);
      return false;
    }

    if (translations.length === 0) {
      showError(t.toast.addWordsToGenerate);
      return false;
    }

    // Проверка, что медиа сгенерированы
    const hasMedia = Object.keys(generatedImages).length > 0 || Object.keys(generatedAudio).length > 0;
    if (!hasMedia) {
      showError(t.toast.generateMediaFirst, {
        description: t.toast.clickGenerateMedia,
      });
      return false;
    }

    return true;
  };

  /**
   * Отмена генерации медиа
   */
  const handleCancelGeneration = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
    }
    
    setIsGenerating(false);
    setGenerationStatus('idle');
    setGenerationProgress({ current: 0, total: 0, currentWord: '' });
    
    showInfo('Генерация отменена', {
      description: 'Процесс остановлен',
    });
  };

  /**
   * Генерация ТОЛЬКО медиа (изображения и аудио)
   * Пользователь сможет увидеть и проверить медиа перед созданием колоды
   */
  const handleGenerateMedia = async () => {
    // Валидация
    if (!validateTranslations()) return;

    // Проверка токенов (учитываем уже сгенерированные медиа)
    const wordsNeedingImages = generateImages ? translations.filter(p => !generatedImages[p.word]).length : 0;
    const wordsNeedingAudio = generateAudio ? translations.filter(p => !generatedAudio[p.word]).length : 0;
    const wordsToGenerate = Math.max(wordsNeedingImages, wordsNeedingAudio);
    const requiredTokens = getTotalMediaCost(
      wordsToGenerate,
      generateImages && wordsNeedingImages > 0,
      generateAudio && wordsNeedingAudio > 0,
      imageProvider === 'nano-banana' ? 'gemini' : (imageProvider as 'openai' | 'gemini'),
      geminiModel as 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'
    );
    const hasEnoughTokens = await checkBalance(requiredTokens);

    if (!hasEnoughTokens || balance < requiredTokens) {
      setShowInsufficientTokensModal(true);
      return;
    }

    setIsGenerating(true);
    
    // Создаём новый AbortController
    const controller = new AbortController();
    setAbortController(controller);

    try {
      // Этап 1: Генерация изображений
      let failedImageWords: string[] = [];
      
      if (generateImages) {
        // Фильтруем слова без готовых изображений
        const pairsNeedingImages = translations.filter(p => !generatedImages[p.word]);
        setGenerationStatus('generating_images');
        setGenerationProgress({ current: 0, total: pairsNeedingImages.length, currentWord: '' });

        for (let i = 0; i < pairsNeedingImages.length; i++) {
          // Проверяем, не отменена ли генерация
          if (controller.signal.aborted) {
            throw new Error('Generation cancelled');
          }

          const pair = pairsNeedingImages[i];

          // Обновляем прогресс
          setGenerationProgress({
            current: i + 1,
            total: pairsNeedingImages.length,
            currentWord: pair.word,
          });

          try {
            // Добавляем таймаут для каждого запроса (60 секунд)
            const timeoutPromise = new Promise<never>((_, reject) => {
              setTimeout(() => reject(new Error('Image generation timeout')), 60000);
            });

            const providerParams = getProviderParams();
            
            const imagePromise = deckService.generateImage({
              word: pair.word,
              translation: pair.translation,
              language: targetLang,
              image_style: imageStyle,
              ...providerParams,
            }, controller.signal);

            const { image_url } = await Promise.race([imagePromise, timeoutPromise]);
            const absoluteUrl = getCardImageUrl(image_url);
            
            if (absoluteUrl) {
              updateGeneratedImages(prev => ({ ...prev, [pair.word]: absoluteUrl }));
            }
          } catch (error) {
            // Если ошибка - отмена, прекращаем цикл
            if (controller.signal.aborted) {
              throw new Error('Generation cancelled');
            }
            console.error(`Error generating image for "${pair.word}":`, error);
            
            // Добавляем в список неудачных
            failedImageWords.push(pair.word);
            
            // Показываем предупреждение, но продолжаем
            if (error instanceof Error && error.message === 'Image generation timeout') {
              console.warn(`Timeout for image "${pair.word}" - will retry later`);
            }
            // Продолжаем даже если одна генерация провалилась
          }
        }
      }

      // Этап 2: Генерация аудио
      let failedAudioWords: string[] = [];
      
      if (generateAudio) {
        // Фильтруем слова без готового аудио
        const pairsNeedingAudio = translations.filter(p => !generatedAudio[p.word]);
        setGenerationStatus('generating_audio');
        setGenerationProgress({ current: 0, total: pairsNeedingAudio.length, currentWord: '' });

        for (let i = 0; i < pairsNeedingAudio.length; i++) {
          // Проверяем, не отменена ли генерация
          if (controller.signal.aborted) {
            throw new Error('Generation cancelled');
          }

          const pair = pairsNeedingAudio[i];

          // Обновляем прогресс
          setGenerationProgress({
            current: i + 1,
            total: pairsNeedingAudio.length,
            currentWord: pair.word,
          });

          try {
            // Добавляем таймаут для каждого запроса (45 секунд для аудио)
            const timeoutPromise = new Promise<never>((_, reject) => {
              setTimeout(() => reject(new Error('Audio generation timeout')), 45000);
            });

            const provider = audioProvider;

            const audioPromise = deckService.generateAudio({
              word: pair.word,
              language: targetLang,
              provider, // Используем выбранный провайдер
            }, controller.signal);

            const { audio_url } = await Promise.race([audioPromise, timeoutPromise]);

            // Преобразуем в абсолютный URL и сохраняем в state для предпросмотра
            const absoluteUrl = getAudioUrl(audio_url);
            if (absoluteUrl) {
              updateGeneratedAudio(prev => ({ ...prev, [pair.word]: absoluteUrl }));
            }
          } catch (error) {
            // Если ошибка - отмена, прекращаем цикл
            if (controller.signal.aborted) {
              throw new Error('Generation cancelled');
            }
            console.error(`Error generating audio for "${pair.word}":`, error);
            
            // Добавляем в список неудачных
            failedAudioWords.push(pair.word);
            
            // Показываем предупреждение, но продолжаем
            if (error instanceof Error && error.message === 'Audio generation timeout') {
              console.warn(`Timeout for audio "${pair.word}" - will retry later`);
            }
            // Продолжаем даже если одна генерация провалилась
          }
        }
      }

      // Этап 3: Retry для неудачных слов (до 2 попыток)
      const maxRetries = 2;
      const retryDelay = 3000; // 3 секунды
      
      for (let retryAttempt = 1; retryAttempt <= maxRetries; retryAttempt++) {
        // Проверяем, есть ли неудачные слова
        if (failedImageWords.length === 0 && failedAudioWords.length === 0) break;
        
        // Проверяем отмену
        if (controller.signal.aborted) {
          throw new Error('Generation cancelled');
        }
        
        console.log(`Retry attempt ${retryAttempt}/${maxRetries}:`, {
          images: failedImageWords.length,
          audio: failedAudioWords.length
        });
        
        // Ждём 3 секунды перед retry
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        
        // Retry изображений
        if (failedImageWords.length > 0) {
          setGenerationStatus('generating_images');
          const currentFailedImages = [...failedImageWords];
          failedImageWords = [];
          
          for (let i = 0; i < currentFailedImages.length; i++) {
            if (controller.signal.aborted) {
              throw new Error('Generation cancelled');
            }
            
            const word = currentFailedImages[i];
            const pair = translations.find(t => t.word === word);
            if (!pair) continue;
            
            setGenerationProgress({
              current: i + 1,
              total: currentFailedImages.length,
              currentWord: `🔄 ${word}`,
            });
            
            try {
              const timeoutPromise = new Promise<never>((_, reject) => {
                setTimeout(() => reject(new Error('Image generation timeout')), 60000);
              });

              const imagePromise = deckService.generateImage({
                word: pair.word,
                translation: pair.translation,
                language: targetLang,
                image_style: imageStyle,
                ...getProviderParams(),
              }, controller.signal);

              const { image_url } = await Promise.race([imagePromise, timeoutPromise]);
              const absoluteUrl = getCardImageUrl(image_url);
              
              if (absoluteUrl) {
                updateGeneratedImages(prev => ({ ...prev, [pair.word]: absoluteUrl }));
                console.log(`✅ Retry successful for image: "${word}"`);
              }
            } catch (error) {
              if (controller.signal.aborted) {
                throw new Error('Generation cancelled');
              }
              console.error(`❌ Retry ${retryAttempt} failed for image "${word}":`, error);
              failedImageWords.push(word);
            }
          }
        }
        
        // Retry аудио
        if (failedAudioWords.length > 0) {
          setGenerationStatus('generating_audio');
          const currentFailedAudio = [...failedAudioWords];
          failedAudioWords = [];
          
          for (let i = 0; i < currentFailedAudio.length; i++) {
            if (controller.signal.aborted) {
              throw new Error('Generation cancelled');
            }
            
            const word = currentFailedAudio[i];
            const pair = translations.find(t => t.word === word);
            if (!pair) continue;
            
            setGenerationProgress({
              current: i + 1,
              total: currentFailedAudio.length,
              currentWord: `🔄 ${word}`,
            });
            
            try {
              const timeoutPromise = new Promise<never>((_, reject) => {
                setTimeout(() => reject(new Error('Audio generation timeout')), 45000);
              });

              const provider = audioProvider;

              const audioPromise = deckService.generateAudio({
                word: pair.word,
                language: targetLang,
                provider, // Используем выбранный провайдер
              }, controller.signal);

              const { audio_url } = await Promise.race([audioPromise, timeoutPromise]);
              const absoluteUrl = getAudioUrl(audio_url);
              
              if (absoluteUrl) {
                updateGeneratedAudio(prev => ({ ...prev, [pair.word]: absoluteUrl }));
                console.log(`✅ Retry successful for audio: "${word}"`);
              }
            } catch (error) {
              if (controller.signal.aborted) {
                throw new Error('Generation cancelled');
              }
              console.error(`❌ Retry ${retryAttempt} failed for audio "${word}":`, error);
              failedAudioWords.push(word);
            }
          }
        }
      }

      // Медиа сгенерированы! Показываем успех
      setGenerationStatus('idle');
      setIsGenerating(false);
      setAbortController(null); // Очищаем контроллер
      
      // Формируем сообщение с учётом неудачных слов
      const totalFailed = failedImageWords.length + failedAudioWords.length;
      const uniqueFailedWords = new Set([...failedImageWords, ...failedAudioWords]);
      
      if (totalFailed > 0) {
        console.warn('⚠️ Some media generation failed after retries:', {
          failedImages: failedImageWords,
          failedAudio: failedAudioWords,
          uniqueWords: Array.from(uniqueFailedWords)
        });
        
        showSuccess('Медиа сгенерированы!', {
          description: `${translations.length - uniqueFailedWords.size}/${translations.length} слов успешно. ${uniqueFailedWords.size > 0 ? `Не удалось: ${Array.from(uniqueFailedWords).join(', ')}` : ''}`,
        });
      } else {
        showSuccess('Медиа сгенерированы!', {
          description: `Проверьте медиа в таблице. Вы можете перегенерировать любое из них.`,
        });
      }

      // Обновляем баланс
      await refreshBalance();
    } catch (error) {
      // Если генерация была отменена, не показываем ошибку
      if (error instanceof Error && error.message === 'Generation cancelled') {
        return; // handleCancelGeneration уже показал уведомление
      }
      
      console.error('Error generating media:', error);
      showError('Ошибка при генерации медиа', {
        description: error instanceof Error ? error.message : 'Попробуйте ещё раз',
      });
      setGenerationStatus('idle');
      setIsGenerating(false);
      setAbortController(null);
    }
  };

  /**
   * Создание колоды ПОСЛЕ того как медиа сгенерированы и проверены
   */
  const handleCreateDeck = async () => {
    // Валидация
    if (!validateDeckCreation()) return;

    setIsGenerating(true);

    try {
      // Этап 1: Создание колоды с медиа
      setGenerationStatus('creating_deck');
      setGenerationProgress({ current: 0, total: 0, currentWord: '' });

      const translationsDict = translations.reduce(
        (acc, pair) => {
          acc[pair.word] = pair.translation;
          return acc;
        },
        {} as Record<string, string>
      );

      // Используем медиа из state (они уже сгенерированы и проверены)
      // ВАЖНО: Конвертируем абсолютные URL в относительные пути для бекенда
      const imageFiles: Record<string, string> = {};
      const audioFiles: Record<string, string> = {};
      
      for (const [word, url] of Object.entries(generatedImages)) {
        const relativePath = getRelativePath(url as string);
        if (relativePath) {
          imageFiles[word] = relativePath;
        }
      }
      
      for (const [word, url] of Object.entries(generatedAudio)) {
        const relativePath = getRelativePath(url as string);
        if (relativePath) {
          audioFiles[word] = relativePath;
        }
      }

      // 🔍 ДИАГНОСТИКА: Логируем что отправляем на бекенд
      console.log('📤 Отправка на бекенд:');
      console.log('  - Слов:', translations.length);
      console.log('  - Изображений:', Object.keys(imageFiles).length);
      console.log('  - Аудио:', Object.keys(audioFiles).length);
      console.log('  - Пример image_file:', Object.values(imageFiles)[0]);
      console.log('  - Пример audio_file:', Object.values(audioFiles)[0]);
      console.log('📋 Полные данные image_files:', imageFiles);
      console.log('📋 Полные данные audio_files:', audioFiles);

      // Генерация карточек через API
      const { file_id, deck_id } = await deckService.generateCards({
        words: translations.map((pair) => pair.word),
        translations: translationsDict,
        language: targetLang,
        deck_name: deckName,
        image_files: imageFiles,
        audio_files: audioFiles,
        save_to_decks: true, // Передаём флаг сохранения
      });

      // Сохраняем deck_id если колода была сохранена
      if (deck_id) {
        setSavedDeckId(deck_id);
        console.log(`✅ Колода сохранена с ID: ${deck_id}`);
        
        // ✅ ВАЖНО: Привязываем медиа к словам в сохранённой колоде
        // Бэкенд добавляет медиа в .apkg файл, но НЕ привязывает их к словам в БД
        // Поэтому делаем PATCH запросы для привязки медиа к словам
        try {
          console.log('🔗 Привязываем медиа к словам в колоде...');
          
          // Получаем созданную колоду со словами
          const createdDeck = await deckService.getDeck(deck_id);
          
          // 🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА: Что бэкенд реально создал?
          console.log('');
          console.log('='.repeat(80));
          console.log('🔍 ДИАГНОСТИКА: ЧТО СОЗДАЛ БЭКЕНД?');
          console.log('='.repeat(80));
          console.log('📦 Созданная колода:');
          console.log('  - ID:', createdDeck.id);
          console.log('  - Название:', createdDeck.name);
          console.log('  - Количество слов (words_count):', createdDeck.words_count);
          console.log('  - Реальное количество слов в массиве:', createdDeck.words?.length || 0);
          console.log('');
          console.log('📝 СПИСОК СЛОВ В СОЗДАННОЙ КОЛОДЕ:');
          
          if (createdDeck.words && createdDeck.words.length > 0) {
            createdDeck.words.forEach((word, index) => {
              console.log(`  ${index + 1}. "${word.original_word}" -> "${word.translation}"`);
              console.log(`     ID: ${word.id}`);
              console.log(`     Изображение: ${word.image_file || '❌ НЕТ'}`);
              console.log(`     Аудио: ${word.audio_file || '❌ НЕТ'}`);
            });
          } else {
            console.error('  ❌ КРИТИЧЕСКАЯ ОШИБКА: СЛОВ НЕТ В КОЛОДЕ!');
          }
          
          console.log('');
          console.log('📋 СРАВНЕНИЕ С ТЕМ, ЧТО МЫ ОТПРАВЛЯЛИ:');
          console.log('  - Мы отправили слов:', translations.length);
          console.log('  - Бэкенд создал слов:', createdDeck.words?.length || 0);
          console.log('  - Наши слова:', translations.map(t => t.word));
          console.log('  - Слова в колоде:', createdDeck.words?.map(w => w.original_word) || []);
          console.log('');
          console.log('📋 МЕДИА ДЛЯ ПРИВЯЗКИ (что мы хотим привязать):');
          console.log('  - image_files:', imageFiles);
          console.log('  - audio_files:', audioFiles);
          console.log('='.repeat(80));
          console.log('');
          
          if (createdDeck.words && createdDeck.words.length > 0) {
            let attachedCount = 0;
            
            console.log('🔗 Начинаем привязку медиа...');
            
            // Для каждого слова обновляем медиа
            for (const word of createdDeck.words) {
              const mediaUpdates: { image_file?: string; audio_file?: string } = {};
              
              console.log(`\n  🔍 Обрабатываем слово: "${word.original_word}"`);
              
              // Проверяем наличие изображения для этого слова
              if (imageFiles[word.original_word]) {
                mediaUpdates.image_file = imageFiles[word.original_word];
                console.log(`    ✅ Найдено изображение: ${mediaUpdates.image_file}`);
              } else {
                console.log(`    ❌ Изображение НЕ найдено для ключа: "${word.original_word}"`);
                console.log(`    📋 Доступные ключи изображений:`, Object.keys(imageFiles));
              }
              
              // Проверяем наличие аудио для этого слова
              if (audioFiles[word.original_word]) {
                mediaUpdates.audio_file = audioFiles[word.original_word];
                console.log(`    ✅ Найдено аудио: ${mediaUpdates.audio_file}`);
              } else {
                console.log(`    ❌ Аудио НЕ найдено для ключа: "${word.original_word}"`);
                console.log(`    📋 Доступные ключи аудио:`, Object.keys(audioFiles));
              }
              
              // Обновляем медиа только если есть что обновлять
              if (Object.keys(mediaUpdates).length > 0) {
                console.log(`    🔄 Отправляем PATCH для привязки медиа...`);
                const result = await deckService.updateWordMedia(deck_id, word.id, mediaUpdates);
                attachedCount++;
                console.log(
                  `    ✅ Медиа привязано к слову "${word.original_word}":`,
                  result.updated_fields
                );
              } else {
                console.log(`    ⚠️ Нет медиа для привязки к этому слову`);
              }
            }
            
            if (attachedCount > 0) {
              console.log(`\n🎉 Всего привязано медиа к ${attachedCount} словам в колоде`);
            } else {
              console.error('\n❌ ОШИБКА: Ни одно медиа НЕ было привязано!');
            }
          } else {
            console.error('❌ КРИТИЧЕСКАЯ ОШИБКА: В колоде НЕТ СЛОВ для привязки медиа!');
          }
        } catch (error) {
          console.error('❌ Ошибка привязки медиа к сохранённой колоде:', error);
          // Не прерываем процесс - .apkg файл уже создан с медиа
          // Медиа можно добавить позже в редакторе колоды
        }
      }

      // Скачивание файла
      const blob = await deckService.downloadDeck(file_id);

      // 🔍 ДИАГНОСТИКА: Проверяем размер файла
      const sizeMB = blob.size / 1024 / 1024;
      console.log(`📦 Размер .apkg файла: ${sizeMB.toFixed(2)} MB (${blob.size} bytes)`);
      
      if (sizeMB < 1) {
        console.warn('⚠️ ВНИМАНИЕ: Размер файла слишком мал! Медиафайлы могут отсутствовать.');
        console.log('🔍 Проверка медиафайлов:');
        console.log('  - generatedImages:', Object.keys(generatedImages).length, 'файло');
        console.log('  - generatedAudio:', Object.keys(generatedAudio).length, 'файлов');
        console.log('  - Примеры URL изображений:', Object.values(generatedImages).slice(0, 2));
        console.log('  - Примеры URL аудио:', Object.values(generatedAudio).slice(0, 2));
        
        // Показываем предупреждение пользователю
        showInfo('⚠️ Файл загружен, но размер подозрительно мал', {
          description: `Размер: ${sizeMB.toFixed(2)} MB. Возможно, медиафайлы не добавлены. Проверьте файл в Anki.`,
        });
      }

      // Создание ссылки для скачивания
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${deckName}.apkg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setGenerationStatus('complete');

      // Показываем уведомление в зависимости от того, сохранили ли в "Мои колоды"
      if (deck_id) {
        showSuccess(t.toast.deckSavedAndDownloaded, {
          description: `${t.toast.deckWith} "${deckName}" ${t.toast.deckAvailableInMyDecks}`,
        });
      } else {
        showSuccess(t.toast.cardsCreated, {
          description: `${t.toast.deckWith} "${deckName}" ${t.toast.with} ${translations.length} ${translations.length === 1 ? t.toast.word : t.toast.words} ${t.toast.isReady}`,
        });
      }

      // Обновляем баланс
      await refreshBalance();

      // Сброс формы через небольшую задержку, чтобы показать "complete"
      resetTimerRef.current = setTimeout(() => {
        clearDraft();
        setSavedDeckId(null);
        setGenerationStatus('idle');
        setGenerationProgress({ current: 0, total: 0, currentWord: '' });
      }, 2000);
    } catch (error) {
      console.error('Error generating cards:', error);
      showError(t.toast.couldNotGenerateCards, {
        description: t.toast.tryAgain,
      });
      setGenerationStatus('idle');
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Подсчет стоимости генерации
   */
  const estimatedCost = getTotalMediaCost(
    translations.length,
    generateImages,
    generateAudio,
    imageProvider === 'nano-banana' ? 'gemini' : (imageProvider as 'openai' | 'gemini'),
    geminiModel as 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'
  );

  const hasMedia = Object.keys(generatedImages).length > 0 || Object.keys(generatedAudio).length > 0;

  return (
    <div className="mx-auto max-w-4xl space-y-4 p-4 pb-24">
      {/* 1. Photo button — hero position */}
      <div className="flex items-center gap-2">
        <PhotoWordExtractor
          targetLang={targetLang}
          sourceLang={sourceLang}
          onWordsExtracted={handlePhotoWordsExtracted}
          disabled={isGenerating}
        />
      </div>

      {/* 2. Word chips input (no deck name) */}
      <WordChipsInput
        words={words}
        onChange={handleWordsChange}
        disabled={isGenerating}
        isProcessing={isProcessingWords}
      />

      {/* 2.5. Clear draft button */}
      {words.length > 0 && !isGenerating && (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            className="text-destructive hover:text-destructive"
            onClick={() => {
              if (window.confirm(t.draft.confirmClear)) {
                clearDraft();
                setSavedDeckId(null);
                setGenerationStatus('idle');
                setGenerationProgress({ current: 0, total: 0, currentWord: '' });
              }
            }}
          >
            {t.draft.clearAll}
          </Button>
        </div>
      )}

      {/* 3. Compact literary source selector ("рубашка") */}
      {words.length > 0 && (
        <CompactLiterarySourceSelector
          activeSource={user?.active_literary_source ?? null}
          onSourceChange={(slug: string | null) => updateUser({ active_literary_source: slug })}
        />
      )}

      {/* 4. Индикатор автоперевода */}
      {isTranslating && (
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          {t.toast.autoTranslating}
        </div>
      )}

      {/* 5. Translation table */}
      {words.length > 0 && (
        <TranslationTable
          words={words}
          translations={translations}
          onTranslationsChange={handleTranslationsChange}
          targetLang={targetLang}
          sourceLang={sourceLang}
          disabled={isGenerating}
          imageFiles={generatedImages}
          audioFiles={generatedAudio}
        />
      )}

      {/* 6. Generated words grid (with frosted glass) */}
      {words.length > 0 && (
        <GeneratedWordsGrid
          words={translations}
          imageFiles={generatedImages}
          audioFiles={generatedAudio}
          onDeleteWord={(word) => {
            const newTranslations = translations.filter((t) => t.word !== word);
            setTranslations(newTranslations);
            setWords(newTranslations.map((t) => t.word));
            const newImages = { ...generatedImages };
            delete newImages[word];
            setGeneratedImages(newImages);
            const newAudio = { ...generatedAudio };
            delete newAudio[word];
            setGeneratedAudio(newAudio);
          }}
          onRegenerateImage={handleRegenerateImage}
          onRegenerateAudio={handleRegenerateAudio}
          disabled={isGenerating}
        />
      )}

      {/* 7. Generation progress */}
      <GenerationProgress
        status={generationStatus}
        current={generationProgress.current}
        total={generationProgress.total}
        currentWord={generationProgress.currentWord}
        onCancel={handleCancelGeneration}
      />

      {/* 8. Success card */}
      {generationStatus === 'complete' && savedDeckId && (
        <GenerationSuccess
          deckName={deckName}
          deckId={savedDeckId}
          wordsCount={translations.length}
        />
      )}

      {/* 9. Action area — compact */}
      {translations.length > 0 && (
        <Card className="p-4">
          <div className="space-y-3">
            {/* Compact media toggles */}
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-1.5 text-sm cursor-pointer">
                <Checkbox
                  id="generate-images"
                  checked={generateImages}
                  onCheckedChange={setGenerateImages}
                  disabled={isGenerating}
                />
                <ImageIcon className="h-3.5 w-3.5 text-cyan-500" />
                <span>{t.generation.generateImages}</span>
              </label>
              <label className="flex items-center gap-1.5 text-sm cursor-pointer">
                <Checkbox
                  id="generate-audio"
                  checked={generateAudio}
                  onCheckedChange={setGenerateAudio}
                  disabled={isGenerating}
                />
                <Volume2 className="h-3.5 w-3.5 text-pink-500" />
                <span>{t.generation.generateAudio}</span>
              </label>
            </div>

            {/* Generate media button with token badge */}
            {!hasMedia && (
              <Button
                onClick={handleGenerateMedia}
                disabled={
                  isGenerating ||
                  balance < estimatedCost ||
                  translations.length === 0
                }
                size="lg"
                className="h-12 w-full bg-gradient-to-r from-cyan-500 to-pink-500 hover:from-cyan-600 hover:to-pink-600"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    {t.generation.generatingMedia}
                  </>
                ) : balance < estimatedCost ? (
                  t.generation.insufficientTokens
                ) : (
                  <span className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    {t.generation.generateMedia}
                    <TokenCostBadge cost={estimatedCost} balance={balance} />
                  </span>
                )}
              </Button>
            )}

            {/* After media: deck name + create button */}
            {hasMedia && (
              <>
                <div className="flex items-center gap-2">
                  <Label htmlFor="deck-name" className="shrink-0 text-sm text-muted-foreground">
                    {t.decks.deckName}:
                  </Label>
                  <Input
                    id="deck-name"
                    value={deckName}
                    onChange={(e) => setDeckName(e.target.value)}
                    className="h-9"
                    disabled={isGenerating}
                  />
                </div>
                <Button
                  onClick={handleCreateDeck}
                  disabled={isGenerating || !deckName.trim()}
                  size="lg"
                  className="h-12 w-full"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      {t.generation.creatingDeck}
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-5 w-5" />
                      {t.generation.createDeck}
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </Card>
      )}

      {/* Insufficient tokens modal */}
      <InsufficientTokensModal
        isOpen={showInsufficientTokensModal}
        onClose={() => setShowInsufficientTokensModal(false)}
        currentBalance={balance}
        requiredTokens={estimatedCost}
      />

      <PageHelpButton pageKey="create" />
    </div>
  );
}