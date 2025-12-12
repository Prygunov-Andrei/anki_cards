import { useState, useEffect } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { WordChipsInput } from '../components/WordChipsInput';
import { TranslationTable, WordTranslationPair } from '../components/TranslationTable';
import { GeneratedWordsGrid } from '../components/GeneratedWordsGrid';
import { InsufficientTokensModal } from '../components/InsufficientTokensModal';
import { ImageStyleSelector, ImageStyle } from '../components/ImageStyleSelector';
import { ImageProviderDropdown } from '../components/ImageProviderDropdown';
import { AudioProviderDropdown } from '../components/AudioProviderDropdown';
import { GenerationProgress, GenerationStatus } from '../components/GenerationProgress';
import { GenerationSuccess } from '../components/GenerationSuccess';
import { useTokenContext } from '../contexts/TokenContext';
import { useAuthContext } from '../contexts/AuthContext';
import { useTranslation } from '../contexts/LanguageContext';
import { deckService } from '../services/deck.service';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { getLanguageName } from '../utils/language-helpers';
import { getCardImageUrl, getAudioUrl, getRelativePath } from '../utils/url-helpers';
import { getTotalMediaCost } from '../utils/token-helpers';
import { formatTokensWithText } from '../utils/token-formatting';
import { Download, Loader2, Sparkles, ImageIcon, Volume2 } from 'lucide-react';
import { GeminiModel } from '../types';

/**
 * Главная страница - быстрая генерация карточек
 * iOS 25 стиль, оптимизирован для мобильных
 */
export default function MainPage() {
  const t = useTranslation();
  const { balance, checkBalance, refreshBalance } = useTokenContext();
  const { user } = useAuthContext();

  // Состояние формы
  const [deckName, setDeckName] = useState(t.decks.newDeck);
  const [words, setWords] = useState<string[]>([]);
  const [translations, setTranslations] = useState<WordTranslationPair[]>([]);

  // Медиа настройки
  const [generateImages, setGenerateImages] = useState(true);
  const [generateAudio, setGenerateAudio] = useState(true);
  const [imageStyle, setImageStyle] = useState<ImageStyle>('balanced');
  const [imageProvider, setImageProvider] = useState<'auto' | 'openai' | 'gemini' | 'nano-banana'>('auto');
  const [audioProvider, setAudioProvider] = useState<'auto' | 'openai' | 'gtts'>('auto');
  const [geminiModel, setGeminiModel] = useState<GeminiModel>('gemini-2.5-flash-image');

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

  // Медиа-файлы для предпросмотра
  const [generatedImages, setGeneratedImages] = useState<Record<string, string>>({});
  const [generatedAudio, setGeneratedAudio] = useState<Record<string, string>>({});

  // Языки берем из профиля пользователя
  const targetLang = user?.learning_language || 'en';
  const sourceLang = user?.native_language || 'ru';

  /**
   * Вспомогательная функция для конвертации imageProvider в формат бекенда
   * nano-banana это на самом деле Gemini с моделью nano-banana-pro-preview
   */
  const getProviderParams = (provider: typeof imageProvider) => {
    if (provider === 'auto') {
      return { provider: undefined, gemini_model: undefined };
    }
    if (provider === 'openai') {
      return { provider: 'openai' as const, gemini_model: undefined };
    }
    if (provider === 'gemini') {
      return { provider: 'gemini' as const, gemini_model: 'gemini-2.5-flash-image' as const };
    }
    if (provider === 'nano-banana') {
      return { provider: 'gemini' as const, gemini_model: 'nano-banana-pro-preview' as const };
    }
    return { provider: undefined, gemini_model: undefined };
  };

  /**
   * Обновление названия колоды при изменении языка интерфейса
   */
  useEffect(() => {
    // Обновляем название колоды только если оно пустое или равно предыдущему дефолтному значению
    if (!deckName || deckName === 'Новая колода' || deckName === 'New Deck' || deckName === 'Neues Deck' || 
        deckName === 'Nuevo mazo' || deckName === 'Novo baralho' || deckName === 'Nouveau jeu' || deckName === 'Nuovo mazzo') {
      setDeckName(t.decks.newDeck);
    }
  }, [t.decks.newDeck]);

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
    const updatedTranslations = processedWords.map((word) => {
      // Ищем существующий перевод
      const existing = translations.find((t) => t.word === word);
      return existing || { word, translation: '' };
    });
    
    setTranslations(updatedTranslations);
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
   * Автоперевод слов
   * С механизмом повторных попыток для непереведенных слов
   */
  const handleAutoTranslate = async () => {
    if (words.length === 0) {
      showError(t.toast.addWordsToTranslate);
      return;
    }

    // Находим слова без перевода
    const wordsToTranslate = translations
      .filter((pair) => !pair.translation.trim())
      .map((pair) => pair.word);

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

      // Обновляем переводы после первой попытки
      let updatedTranslations = translations.map((pair) => {
        if (!pair.translation.trim()) {
          // Ищем перевод по полному ключу
          let translation = translationsDict[pair.word];
          
          console.log(`🔍 Ищем перевод для "${pair.word}":`, translation ? `найдено "${translation}"` : 'не найдено');
          
          // Если не нашли, пробуем найти по ключу без скобок
          // Например: "rennen (rannte / gerant)" -> "rennen"
          if (!translation && pair.word.includes('(')) {
            const wordWithoutParens = pair.word.split('(')[0].trim();
            translation = translationsDict[wordWithoutParens];
            console.log(`🔍 Попытка без скобок "${wordWithoutParens}":`, translation ? `найдено "${translation}"` : 'не найдено');
          }
          
          if (translation) {
            return { ...pair, translation };
          }
        }
        return pair;
      });

      // Проверяем какие слова остались непереведенными
      const untranslatedWords = updatedTranslations
        .filter((pair) => !pair.translation.trim())
        .map((pair) => pair.word);

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

          // Обновляем переводы после повторной попытки
          updatedTranslations = updatedTranslations.map((pair) => {
            if (!pair.translation.trim()) {
              // Ищем перевод по полному ключу
              let translation = retryTranslationsDict[pair.word];
              
              // Если не нашли, пробуем найти по ключу без скобок
              if (!translation && pair.word.includes('(')) {
                const wordWithoutParens = pair.word.split('(')[0].trim();
                translation = retryTranslationsDict[wordWithoutParens];
              }
              
              // 🆕 НОВАЯ ЛОГИКА: Backend может вернуть объединенные слова через запятую
              // Например: "Da kann ich mich ganz nach Ihne, richten" 
              if (!translation) {
                // Ищем ключи которые содержат наше слово
                for (const [key, value] of Object.entries(retryTranslationsDict)) {
                  // Проверяем содержится ли наше слово в ключе
                  if (key.includes(pair.word)) {
                    translation = value as string;
                    console.log(`✅ Найден перевод в составном ключе: "${key}" -> "${translation}"`);
                    break;
                  }
                }
              }
              
              if (translation) {
                console.log(`✅ Перевод найден при повторной попытке: ${pair.word} -> ${translation}`);
                return { ...pair, translation };
              } else {
                console.warn(`⚠️ Слово не удалось перевести после повторной попытки: ${pair.word}`);
              }
            }
            return pair;
          });
        } catch (retryError) {
          console.error('Error during retry translation:', retryError);
          // Продолжаем с переводами которые удалось получить при первой попытке
        }
      }

      setTranslations(updatedTranslations);

      // Подсчитываем переведенные слова для уведомления
      const translatedCount = wordsToTranslate.length - updatedTranslations.filter((pair) => !pair.translation.trim()).length;

      showSuccess(t.toast.wordsTranslated, {
        description: `${t.toast.translated} ${translatedCount} ${translatedCount === 1 ? t.toast.word : t.toast.words}`,
      });

      // Предупреждаем о непереведенных словах
      const finalUntranslated = updatedTranslations.filter((pair) => !pair.translation.trim());
      if (finalUntranslated.length > 0) {
        console.warn(`⚠️ Не удалось перевести ${finalUntranslated.length} слов:`, finalUntranslated.map(p => p.word));
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

      const providerParams = getProviderParams(imageProvider);
      
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
        setGeneratedImages(prev => ({ ...prev, [pair.word]: absoluteUrl }));
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

      const provider = audioProvider === 'auto' ? undefined : audioProvider;

      const { audio_url } = await deckService.generateAudio({
        word: pair.word,
        language: targetLang,
        provider, // Используем выбранный провайдер
      });

      // Преобразуем в абсолютный URL и сохраняем в state для предпросмотра
      const absoluteUrl = getAudioUrl(audio_url);
      if (absoluteUrl) {
        setGeneratedAudio(prev => ({ ...prev, [pair.word]: absoluteUrl }));
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

    // Проверка токенов
    const requiredTokens = getTotalMediaCost(
      translations.length,
      generateImages,
      generateAudio,
      imageProvider === 'auto' ? (user?.image_provider || 'openai') : imageProvider,
      imageProvider === 'gemini' ? geminiModel : (user?.gemini_model || 'gemini-2.5-flash-image')
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
        setGenerationStatus('generating_images');
        setGenerationProgress({ current: 0, total: translations.length, currentWord: '' });

        for (let i = 0; i < translations.length; i++) {
          // Проверяем, не отменена ли генерация
          if (controller.signal.aborted) {
            throw new Error('Generation cancelled');
          }
          
          const pair = translations[i];
          
          // Обновляем прогресс
          setGenerationProgress({
            current: i + 1,
            total: translations.length,
            currentWord: pair.word,
          });

          try {
            // Добавляем таймаут для каждого запроса (60 секунд)
            const timeoutPromise = new Promise<never>((_, reject) => {
              setTimeout(() => reject(new Error('Image generation timeout')), 60000);
            });

            const providerParams = getProviderParams(imageProvider);
            
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
              setGeneratedImages(prev => ({ ...prev, [pair.word]: absoluteUrl }));
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
        setGenerationStatus('generating_audio');
        setGenerationProgress({ current: 0, total: translations.length, currentWord: '' });

        for (let i = 0; i < translations.length; i++) {
          // Проверяем, не отменена ли генерация
          if (controller.signal.aborted) {
            throw new Error('Generation cancelled');
          }
          
          const pair = translations[i];
          
          // Обновляем прогресс
          setGenerationProgress({
            current: i + 1,
            total: translations.length,
            currentWord: pair.word,
          });

          try {
            // Добавляем таймаут для каждого запроса (45 секунд для аудио)
            const timeoutPromise = new Promise<never>((_, reject) => {
              setTimeout(() => reject(new Error('Audio generation timeout')), 45000);
            });

            const provider = audioProvider === 'auto' ? undefined : audioProvider;

            const audioPromise = deckService.generateAudio({
              word: pair.word,
              language: targetLang,
              provider, // Используем выбранный провайдер
            }, controller.signal);

            const { audio_url } = await Promise.race([audioPromise, timeoutPromise]);

            // Преобразуем в абсолютный URL и сохраняем в state для предпросмотра
            const absoluteUrl = getAudioUrl(audio_url);
            if (absoluteUrl) {
              setGeneratedAudio(prev => ({ ...prev, [pair.word]: absoluteUrl }));
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
                provider: imageProvider === 'auto' ? undefined : imageProvider,
                gemini_model: imageProvider === 'gemini' ? geminiModel : undefined,
              }, controller.signal);

              const { image_url } = await Promise.race([imagePromise, timeoutPromise]);
              const absoluteUrl = getCardImageUrl(image_url);
              
              if (absoluteUrl) {
                setGeneratedImages(prev => ({ ...prev, [pair.word]: absoluteUrl }));
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

              const provider = audioProvider === 'auto' ? undefined : audioProvider;

              const audioPromise = deckService.generateAudio({
                word: pair.word,
                language: targetLang,
                provider, // Используем выбранный провайдер
              }, controller.signal);

              const { audio_url } = await Promise.race([audioPromise, timeoutPromise]);
              const absoluteUrl = getAudioUrl(audio_url);
              
              if (absoluteUrl) {
                setGeneratedAudio(prev => ({ ...prev, [pair.word]: absoluteUrl }));
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
        const relativePath = getRelativePath(url);
        if (relativePath) {
          imageFiles[word] = relativePath;
        }
      }
      
      for (const [word, url] of Object.entries(generatedAudio)) {
        const relativePath = getRelativePath(url);
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
        console.log('  - generatedImages:', Object.keys(generatedImages).length, 'файло��');
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
      setTimeout(() => {
        setWords([]);
        setTranslations([]);
        setDeckName(t.decks.newDeck);
        setSavedDeckId(null); // Сброс сохранённого ID
        setGenerationStatus('idle');
        setGenerationProgress({ current: 0, total: 0, currentWord: '' });
        setGeneratedImages({}); // Сброс медиа
        setGeneratedAudio({});
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
    imageProvider === 'auto' ? (user?.image_provider || 'openai') : imageProvider,
    imageProvider === 'gemini' ? geminiModel : (user?.gemini_model || 'gemini-2.5-flash-image')
  );

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4 pb-24">
      {/* Форма генерации */}
      <div className="space-y-6">
        {/* Ввод слов с названием колоды */}
        <WordChipsInput
          words={words}
          onChange={handleWordsChange}
          disabled={isGenerating}
          deckName={deckName}
          onDeckNameChange={setDeckName}
          isProcessing={isProcessingWords}
        />

        {/* Кнопка автоперевода */}
        {words.length > 0 && (
          <div className="flex justify-end">
            <Button
              onClick={handleAutoTranslate}
              disabled={isTranslating || isGenerating}
              variant="outline"
              size="default"
              className="min-w-[140px] border-pink-200 bg-gradient-to-r from-pink-50 to-purple-50 hover:from-pink-100 hover:to-purple-100 dark:border-pink-800 dark:from-pink-950/30 dark:to-purple-950/30 dark:hover:from-pink-950/50 dark:hover:to-purple-950/50"
            >
              {isTranslating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.words.translating}
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  {t.words.autoTranslate}
                </>
              )}
            </Button>
          </div>
        )}

        {/* Таблица переводов */}
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

        {/* Сетка готовых карточек с медиа */}
        {words.length > 0 && (
          <GeneratedWordsGrid
            words={translations}
            imageFiles={generatedImages}
            audioFiles={generatedAudio}
            onDeleteWord={(word) => {
              // Удаляем слово из списка
              const newTranslations = translations.filter((t) => t.word !== word);
              setTranslations(newTranslations);
              setWords(newTranslations.map((t) => t.word));
              // Удаляем медиа для этого слова
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

        {/* Настройки медиа */}
        {translations.length > 0 && (
          <Card className="p-6">
            <h2 className="mb-6 flex items-center gap-2 text-gray-900 dark:text-gray-100">
              <ImageIcon className="h-5 w-5 text-blue-500" />
              {t.generation.mediaSettings}
            </h2>

            <div className="space-y-6">
              {/* Чекбоксы для медиа */}
              <div className="space-y-4">
                {/* Генерация изображений */}
                <div className="flex items-center space-x-3">
                  <Checkbox
                    id="generate-images"
                    checked={generateImages}
                    onCheckedChange={setGenerateImages}
                    disabled={isGenerating}
                  />
                  <Label
                    htmlFor="generate-images"
                    className="flex cursor-pointer items-center gap-2 text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    <ImageIcon className="h-4 w-4 text-cyan-500" />
                    {t.generation.generateImages}
                  </Label>
                </div>

                {/* Генерация аудио */}
                <div className="flex items-center space-x-3">
                  <Checkbox
                    id="generate-audio"
                    checked={generateAudio}
                    onCheckedChange={setGenerateAudio}
                    disabled={isGenerating}
                  />
                  <Label
                    htmlFor="generate-audio"
                    className="flex cursor-pointer items-center gap-2 text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    <Volume2 className="h-4 w-4 text-pink-500" />
                    {t.generation.generateAudio}
                  </Label>
                </div>
              </div>

              {/* Селектор стиля изображений */}
              {generateImages && (
                <div className="pt-2 space-y-4">
                  <ImageStyleSelector
                    value={imageStyle}
                    onChange={setImageStyle}
                    disabled={isGenerating}
                  />
                  
                  {/* Селектор провайдера изображений */}
                  <ImageProviderDropdown
                    value={imageProvider}
                    onChange={setImageProvider}
                    disabled={isGenerating}
                  />
                </div>
              )}
              
              {/* Селектор провайдера аудио */}
              {generateAudio && (
                <div className="pt-2 space-y-4">
                  <AudioProviderDropdown
                    value={audioProvider}
                    onChange={setAudioProvider}
                    disabled={isGenerating}
                  />
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Прогресс генерации */}
        <GenerationProgress
          status={generationStatus}
          current={generationProgress.current}
          total={generationProgress.total}
          currentWord={generationProgress.currentWord}
          onCancel={handleCancelGeneration}
        />

        {/* Карточка успешного сохранения */}
        {generationStatus === 'complete' && savedDeckId && (
          <GenerationSuccess
            deckName={deckName}
            deckId={savedDeckId}
            wordsCount={translations.length}
          />
        )}

        {/* Кнопка генерации */}
        {translations.length > 0 && (
          <Card className="p-6">
            <div className="space-y-4">
              {/* Информация о стоимости */}
              <div className="flex items-center justify-between rounded-lg bg-gradient-to-r from-cyan-50 to-pink-50 p-4 dark:from-cyan-950/20 dark:to-pink-950/20">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {t.generation.generationCost}
                  </p>
                  <p className="text-2xl font-semibold text-primary">
                    {formatTokensWithText(estimatedCost, t, sourceLang)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">{t.tokens.yourBalance}</p>
                  <p className="text-2xl font-semibold">
                    {formatTokensWithText(balance, t, sourceLang)}
                  </p>
                </div>
              </div>

              {/* Кнопка */}
              {/* Кнопка генерации медиа (Этап 1) */}
              {Object.keys(generatedImages).length === 0 && Object.keys(generatedAudio).length === 0 && (
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
                    <>
                      <Sparkles className="mr-2 h-5 w-5" />
                      {t.generation.generateMedia}
                    </>
                  )}
                </Button>
              )}

              {/* Кнопка создания колоды (Этап 2) - появляется ПОСЛЕ генерации медиа */}
              {(Object.keys(generatedImages).length > 0 || Object.keys(generatedAudio).length > 0) && (
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
              )}
            </div>
          </Card>
        )}
      </div>

      {/* Модальное окно недостатка токенов */}
      <InsufficientTokensModal
        isOpen={showInsufficientTokensModal}
        onClose={() => setShowInsufficientTokensModal(false)}
        currentBalance={balance}
        requiredTokens={estimatedCost}
      />
    </div>
  );
}