import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Deck } from '../types';
import { deckService } from '../services/deck.service';
import { EditableTitle } from '../components/EditableTitle';
import { WordsTable } from '../components/WordsTable';
import { SmartWordInput, WordTranslationPair } from '../components/SmartWordInput';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { GenerationProgress, GenerationStatus } from '../components/GenerationProgress';
import { MediaSettings } from '../components/MediaSettings';
import { ImageStyle } from '../components/ImageStyleSelector';
import {
  ArrowLeft,
  Download,
  Loader2,
  BookOpen,
  Sparkles,
  Plus,
  GraduationCap,
} from 'lucide-react';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { getLanguageName } from '../utils/language-helpers';
import { useTranslation } from '../contexts/LanguageContext';
import { useAuthContext } from '../contexts/AuthContext';
import { Card } from '../components/ui/card';
import axios from 'axios';

/**
 * Страница DeckEditorPage - редактор колоды
 * Логика как на главной: добавляем слова → настройки медиа → генерация карточек → добавление в олоду
 * iOS 25 стиль, оптимизирован для iPhone 17 Air
 */
const DeckEditorPage: React.FC = () => {
  const t = useTranslation();
  const { user } = useAuthContext();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Список всех колод пользователя (для переноса карточек)
  const [allDecks, setAllDecks] = useState<Deck[]>([]);
  
  // Новые слова для добавления (буфер до генерации)
  const [pendingWords, setPendingWords] = useState<WordTranslationPair[]>([]);
  
  // Настройки медиа
  const [generateImages, setGenerateImages] = useState(true);
  const [generateAudio, setGenerateAudio] = useState(true);
  const [imageStyle, setImageStyle] = useState<ImageStyle>('balanced');
  const [imageProvider, setImageProvider] = useState<'auto' | 'openai' | 'gemini' | 'nano-banana'>('auto');
  const [audioProvider, setAudioProvider] = useState<'auto' | 'openai' | 'gtts'>('auto');
  
  // Прогресс генерации
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus>('idle');
  const [generationProgress, setGenerationProgress] = useState({ current: 0, total: 0, currentWord: '' });

  /**
   * Загрузка колоды и списка всех колод
   */
  useEffect(() => {
    loadDeck();
    loadAllDecks();
  }, [id]);

  const loadDeck = async () => {
    if (!id) {
      navigate('/decks');
      return;
    }

    setIsLoading(true);
    try {
      const data = await deckService.getDeck(Number(id));
      setDeck(data);
    } catch (error) {
      console.error('Error loading deck:', error);
      showError(t.decks.couldNotLoadDecks, {
        description: t.decks.tryRefreshPage,
      });
      navigate('/decks');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAllDecks = async () => {
    try {
      const data = await deckService.getDecks();
      setAllDecks(data);
    } catch (error) {
      console.error('Error loading all decks:', error);
      showError(t.decks.couldNotLoadDecksList, {
        description: t.decks.tryRefreshPage,
      });
    }
  };

  /**
   * Сохранение названия колоды
   */
  const handleSaveTitle = async (newTitle: string) => {
    if (!deck) return;

    try {
      const updatedDeck = await deckService.updateDeck(deck.id, {
        name: newTitle,
      });
      setDeck(updatedDeck);
      showSuccess(t.decks.titleUpdated, {
        description: `${t.decks.deckRenamedTo} "${newTitle}"`,
      });
    } catch (error) {
      console.error('Error updating deck title:', error);
      showError(t.decks.couldNotUpdateTitle, {
        description: t.toast.tryAgain,
      });
      throw error;
    }
  };

  /**
   * Добавление слов в буфер (НЕ в колоду напрямую!)
   */
  const handleAddWords = async (pairs: WordTranslationPair[]) => {
    setPendingWords(prev => [...prev, ...pairs]);
    
    const count = pairs.length;
    const wordText = count === 1 ? t.decks.wordAdded : count < 5 ? t.decks.wordsAdded : t.decks.wordsManyAdded;
    
    showSuccess(
      `${count} ${wordText}`,
      {
        description: t.decks.pressGenerateCards,
      }
    );
  };

  /**
   * Генерация карточек с медиа и добавление в колоду
   */
  const handleGenerateCards = async () => {
    if (!deck || pendingWords.length === 0) return;

    console.log('🚀 Starting card generation...', {
      deck: deck.id,
      pendingWords,
      generateImages,
      generateAudio,
      imageStyle,
    });

    setIsGenerating(true);

    try {
      // Сначала добавляем слова в колоду (без медиа)
      console.log('📝 Adding words to deck...');
      const addResult = await deckService.addWordsToDeck(deck.id, pendingWords);
      
      console.log('✅ Words added, result:', addResult);
      
      // API возвращает {added_words: [...], message: '...'} 
      // где added_words - массив ID в том же порядке, что и отправленные слова
      const addedWordIds = addResult.added_words || [];
      console.log('📝 Added word IDs:', addedWordIds);

      if (addedWordIds.length === 0) {
        console.log('⚠️ No words added!');
        setIsGenerating(false);
        setPendingWords([]);
        return;
      }

      // Перезагружаем колоду, чтобы получить полные анные о словах
      console.log('🔄 Reloading deck...');
      const updatedDeck = await deckService.getDeck(deck.id);
      setDeck(updatedDeck);

      // Создаем карту ID -> Word для быстрого поиска
      const wordsById = new Map(updatedDeck.words?.map(w => [w.id, w]) || []);
      
      // Получаем слова в том же порядке, что и pendingWords (по addedWordIds)
      const newWords = addedWordIds.map(id => wordsById.get(id)).filter(Boolean);

      console.log('🔍 Found new words:', newWords);

      if (newWords.length === 0) {
        console.log('⚠️ No new words found in deck!');
        setIsGenerating(false);
        setPendingWords([]);
        return;
      }

      const wordCount = newWords.length;
      const wordText = wordCount === 1 ? t.decks.word : t.decks.wordsTwo;
      
      showInfo(t.decks.generatingMedia, {
        description: `${t.decks.creatingMediaFor} ${wordCount} ${wordText}...`,
      });

      // Генерация изображений
      if (generateImages) {
        console.log('🖼️ Starting image generation...');
        setGenerationStatus('generating_images');
        setGenerationProgress({ current: 0, total: newWords.length, currentWord: '' });

        for (let i = 0; i < newWords.length; i++) {
          const word = newWords[i];

          console.log(`🖼️ Generating image ${i + 1}/${newWords.length} for "${word.original_word}" (word_id: ${word.id})`);

          setGenerationProgress({
            current: i + 1,
            total: newWords.length,
            currentWord: word.original_word,
          });

          try {
            await deckService.generateImage({
              word: word.original_word,
              translation: word.translation,
              language: deck.target_lang,
              image_style: imageStyle,
              word_id: word.id, // Передаем ID слова для привязки медиа
              provider: imageProvider, // Используем провайдер из настроек
            });

            console.log(`✅ Image generated for "${word.original_word}"`);
          } catch (error) {
            console.error(`❌ Error generating image for "${word.original_word}":`, error);
            // Продолжаем даже если одна генерация провалилась
          }
        }
      } else {
        console.log('⏭️ Skipping image generation (disabled)');
      }

      // Генерация аудио
      if (generateAudio) {
        console.log('🔊 Starting audio generation...');
        setGenerationStatus('generating_audio');
        setGenerationProgress({ current: 0, total: newWords.length, currentWord: '' });

        for (let i = 0; i < newWords.length; i++) {
          const word = newWords[i];

          console.log(`🔊 Generating audio ${i + 1}/${newWords.length} for "${word.original_word}" (word_id: ${word.id})`);

          setGenerationProgress({
            current: i + 1,
            total: newWords.length,
            currentWord: word.original_word,
          });

          try {
            const provider = audioProvider === 'auto' ? undefined : audioProvider;

            await deckService.generateAudio({
              word: word.original_word,
              language: deck.target_lang,
              provider, // Используем провайдер из настроек
              word_id: word.id, // Передаем ID слова для привязки медиа
            });

            console.log(`✅ Audio generated for "${word.original_word}"`);
          } catch (error) {
            console.error(`❌ Error generating audio for "${word.original_word}":`, error);
            // Продолжаем даже если одна генерация провалилась
          }
        }
      } else {
        console.log('⏭️ Skipping audio generation (disabled)');
      }

      // Перезагружаем колоду с обновленными медиа
      console.log('🔄 Reloading deck with updated media...');
      const reloadedDeck = await deckService.getDeck(deck.id);
      
      // Логируем, что пришло в словах
      console.log('📦 Reloaded deck words:', reloadedDeck.words);
      if (reloadedDeck.words && reloadedDeck.words.length > 0) {
        const firstWord = reloadedDeck.words[0];
        console.log('🔍 First word FULL object:', firstWord);
        console.log('🔍 First word media status:', {
          id: firstWord.id,
          original_word: firstWord.original_word,
          image_file: firstWord.image_file,
          audio_file: firstWord.audio_file,
        });
      }
      
      setDeck(reloadedDeck);

      setGenerationStatus('complete');

      const cardCount = newWords.length;
      const cardText = cardCount === 1 ? t.decks.cardAdded : cardCount < 5 ? t.decks.cardsAddedPlural : t.decks.cardsManyAdded;
      
      showSuccess(t.decks.cardsAdded, {
        description: `${cardCount} ${cardText} ${t.decks.toDeckWithMedia}`,
      });

      // Очищаем буфер и сбрасываем статус
      setPendingWords([]);
      
      setTimeout(() => {
        setGenerationStatus('idle');
        setGenerationProgress({ current: 0, total: 0, currentWord: '' });
      }, 2000);
    } catch (error) {
      console.error('❌ Error generating cards:', error);
      showError(t.decks.couldNotAddCards, {
        description: t.toast.tryAgain,
      });
      setGenerationStatus('idle');
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Удаление слова
   */
  const handleDeleteWord = async (wordId: number) => {
    if (!deck) return;

    try {
      await deckService.removeWordFromDeck(deck.id, wordId);
      
      // Перезагружаем колоду, чтобы получить актуальные данные
      await loadDeck();
      
      showSuccess(t.decks.wordDeleted, {
        description: t.decks.wordRemovedFromDeck,
      });
    } catch (error) {
      console.error('Error deleting word:', error);
      showError(t.decks.couldNotDeleteWord, {
        description: t.toast.tryAgain,
      });
      throw error;
    }
  };

  /**
   * Перегенерация изображения для слова
   */
  const handleRegenerateImage = async (wordId: number, word: string, translation: string) => {
    if (!deck) return;

    try {
      showInfo(t.decks.generatingImage, {
        description: `${t.decks.creatingNewImageFor} "${word}"`,
      });

      await deckService.generateImage({
        word,
        translation,
        language: deck.target_lang,
        image_style: imageStyle,
        word_id: wordId, // Привязываем к слову в колоде
        provider: imageProvider, // Используем провайдер из настроек
      });

      // Перезагружаем колоду с обновлёнными данными
      await loadDeck();

      showSuccess(t.decks.imageUpdated, {
        description: `${t.decks.newImageFor} "${word}" ${t.decks.ready}`,
      });
    } catch (error) {
      console.error(`Error regenerating image for "${word}":`, error);
      showError(t.decks.couldNotCreateImage, {
        description: t.toast.tryAgain,
      });
    }
  };

  /**
   * Перегенерация аудио для слова
   */
  const handleRegenerateAudio = async (wordId: number, word: string) => {
    if (!deck) return;

    try {
      showInfo(t.decks.generatingAudio, {
        description: `${t.decks.creatingNewAudioFor} "${word}"`,
      });

      const provider = audioProvider === 'auto' ? undefined : audioProvider;

      await deckService.generateAudio({
        word,
        language: deck.target_lang,
        provider, // Используем провайдер из настроек
        word_id: wordId, // Привязываем к слову в колоде
      });

      // Перезагружаем колоду с обновлёнными данными
      await loadDeck();

      showSuccess(t.decks.audioUpdated, {
        description: `${t.decks.newAudioFor} "${word}" ${t.decks.ready}`,
      });
    } catch (error) {
      console.error(`Error regenerating audio for "${word}":`, error);
      showError(t.decks.couldNotCreateAudio, {
        description: t.toast.tryAgain,
      });
    }
  };

  /**
   * Редактирование изображения через миксин
   */
  const handleEditImage = async (wordId: number, mixin: string) => {
    if (!deck) return;

    try {
      showInfo(t.words.editImage, {
        description: `${t.words.editImageHint}: "${mixin}"`,
      });

      await deckService.editImage({
        word_id: wordId,
        mixin,
      });

      // Перезагружаем колоду с обновлёнными данными
      await loadDeck();

      showSuccess(t.decks.imageUpdated, {
        description: t.decks.ready,
      });
    } catch (error) {
      console.error(`Error editing image with mixin "${mixin}":`, error);
      showError(t.decks.couldNotCreateImage, {
        description: t.toast.tryAgain,
      });
    }
  };

  /**
   * Удаление изображения у слова
   */
  const handleDeleteImage = async (wordId: number) => {
    if (!deck) return;

    try {
      showInfo('Удаление изображения...', {
        description: 'Удаляем изображение',
      });

      // Удаляем изображение, установив image_file в пустую строку
      await deckService.updateWordMedia(deck.id, wordId, {
        image_file: '',
      });

      // Перезагружаем колоду с обновлёнными данными
      await loadDeck();

      showSuccess('Изображение удалено!', {
        description: 'Изображение успешно удалено',
      });
    } catch (error) {
      console.error('Error deleting image:', error);
      showError('Не удалось удалить изображение', {
        description: t.toast.tryAgain,
      });
    }
  };

  /**
   * Удаление аудио у слова
   */
  const handleDeleteAudio = async (wordId: number) => {
    if (!deck) return;

    try {
      showInfo('Удаление аудио...', {
        description: 'Удаляем аудио',
      });

      // Удаляем аудио, установив audio_file в пустую строку
      await deckService.updateWordMedia(deck.id, wordId, {
        audio_file: '',
      });

      // Перезагружаем колоду с обновлёнными данными
      await loadDeck();

      showSuccess(t.words.audioDeleted, {
        description: t.words.audioDeleted,
      });
    } catch (error) {
      console.error('Error deleting audio:', error);
      showError('Не удалось удалить аудио', {
        description: t.toast.tryAgain,
      });
    }
  };

  /**
   * Перенос карточки в другую колоду
   */
  const handleMoveCardToDeck = async (wordId: number, toDeckId: number, toDeckName: string) => {
    if (!deck) return;

    // Находим слово в текущей колоде
    const word = deck.words?.find(w => w.id === wordId);
    if (!word) {
      showError(t.decks.wordNotFound, {
        description: t.decks.tryRefreshPage,
      });
      return;
    }

    try {
      showInfo(t.decks.movingCard, {
        description: `${t.decks.movingToDeck} \"${toDeckName}\"`,
      });

      // Используем метод копирования и переноса (работает через существующие API)
      await deckService.copyAndMoveCard(
        {
          id: word.id,
          original_word: word.original_word,
          translation: word.translation,
          image_file: word.image_file,
          audio_file: word.audio_file,
        },
        deck.id,
        toDeckId
      );

      // Перезагружаем колоду, чтобы обновить список слов
      await loadDeck();

      showSuccess(t.decks.cardMoved, {
        description: `${t.decks.wordAddedToDeck} \"${toDeckName}\"`,
      });
    } catch (error) {
      console.error('Error moving card:', error);
      showError(t.decks.couldNotMoveCard, {
        description: t.toast.tryAgain,
      });
    }
  };

  /**
   * Инвертировать слово
   */
  const handleInvertWord = async (wordId: number) => {
    if (!deck) return;

    try {
      showInfo(t.words.invertingWord);

      const result = await deckService.invertWord(deck.id, wordId);

      showSuccess(t.words.wordInverted, {
        description: result.message,
      });

      // Перезагружаем колоду, чтобы обновить список слов
      await loadDeck();
    } catch (error: unknown) {
      console.error('Error inverting word:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : t.common.unknownError);
      showError(t.common.error, {
        description: message,
      });
    }
  };

  /**
   * Создать пустую карточку для слова
   */
  const handleCreateEmptyCard = async (wordId: number) => {
    if (!deck) return;

    try {
      showInfo(t.words.creatingEmptyCard);

      const result = await deckService.createEmptyCard(deck.id, wordId);

      showSuccess(t.words.emptyCardCreated, {
        description: result.message,
      });

      // Перезагружаем колоду, чтобы обновить список слов
      await loadDeck();
    } catch (error: unknown) {
      console.error('Error creating empty card:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : t.common.unknownError);
      showError(t.common.error, {
        description: message,
      });
    }
  };

  /**
   * Обновление слова или перевода
   */
  const handleWordUpdate = async (wordId: number, data: { original_word?: string; translation?: string }) => {
    if (!deck) return;

    try {
      await deckService.updateWordMedia(deck.id, wordId, data);
      
      // Перезагружаем колоду, чтобы получить актуальные данные
      await loadDeck();
      
      showSuccess(t.decks.wordUpdated || 'Word updated', {
        description: t.decks.changesSaved || 'Changes saved successfully',
      });
    } catch (error: unknown) {
      console.error('Error updating word:', error);
      
      // Обработка ошибок валидации от backend
      if (axios.isAxiosError(error) && error.response?.data?.errors) {
        const errors = error.response.data.errors;
        const errorMessage = errors.original_word || errors.translation || t.decks.couldNotUpdateWord || 'Could not update word';
        
        showError(errorMessage, {
          description: t.toast.tryAgain,
        });
      } else {
        showError(t.decks.couldNotUpdateWord || 'Could not update word', {
          description: t.toast.tryAgain,
        });
      }
      
      // Перезагружаем колоду, чтобы откатить изменения в UI
      await loadDeck();
      
      throw error;
    }
  };

  /**
   * Генерация .apkg файла
   */
  const handleGenerateApkg = async () => {
    if (!deck) return;

    if (!deck.words || deck.words.length === 0) {
      showError(t.decks.emptyDeck, {
        description: t.decks.addWordBeforeGeneration,
      });
      return;
    }

    setIsGenerating(true);

    try {
      setGenerationStatus('creating_deck');
      setGenerationProgress({ current: 0, total: 0, currentWord: '' });

      // 🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА ПЕРЕД ГЕНЕРАЦИЕЙ
      console.log('='.repeat(80));
      console.log('🚀 ГЕНЕРАЦИЯ .APKG ФАЙЛА - НАЧАЛО');
      console.log('='.repeat(80));
      console.log('📋 Информация о колоде:');
      console.log('  - ID колоды:', deck.id);
      console.log('  - Название:', deck.name);
      console.log('  - Количество слов:', deck.words?.length || 0);
      console.log('  - Целевой язык:', deck.target_lang);
      console.log('  - Исходный язык:', deck.source_lang);
      
      if (deck.words && deck.words.length > 0) {
        const wordsWithImage = deck.words.filter(w => w.image_file && w.image_file.trim() !== '').length;
        const wordsWithAudio = deck.words.filter(w => w.audio_file && w.audio_file.trim() !== '').length;
        
        console.log('');
        console.log('📊 Статистика медиа:');
        console.log('  - Слов с изображениями:', wordsWithImage, 'из', deck.words.length);
        console.log('  - Слов с аудио:', wordsWithAudio, 'из', deck.words.length);
        
        console.log('');
        console.log('📝 ПОЛНЫЙ СПИСОК СЛОВ С МЕДИА:');
        deck.words.forEach((word, index) => {
          console.log(`  ${index + 1}. "${word.original_word}" -> "${word.translation}"`);
          console.log(`     ID: ${word.id}`);
          console.log(`     Изображение: ${word.image_file || '❌ НЕТ'}`);
          console.log(`     Аудио: ${word.audio_file || '❌ НЕТ'}`);
        });
      }
      console.log('='.repeat(80));

      showInfo(t.decks.generatingApkg, {
        description: t.decks.collectingApkg,
      });

      // Генерация .apkg файла
      console.log('📡 Отправка запроса на бэкенд: POST /api/decks/${deck.id}/generate-apkg/');
      const { file_id } = await deckService.generateDeckApkg(deck.id);
      console.log('✅ Бэкенд вернул file_id:', file_id);

      // Скачивание файла
      console.log('📡 Скаивание файла: GET /api/decks/download/${file_id}/');
      const blob = await deckService.downloadDeck(file_id);

      // 🔍 ДИАГНОСТИКА: Проверяем размер файла
      const sizeMB = blob.size / 1024 / 1024;
      const sizeKB = blob.size / 1024;
      console.log('');
      console.log('📦 РЕЗУЛЬТАТ:');
      console.log(`  - Размер файла: ${sizeKB.toFixed(2)} KB (${sizeMB.toFixed(2)} MB, ${blob.size} bytes)`);
      console.log(`  - Тип файла: ${blob.type}`);
      
      if (sizeKB < 100) {
        console.error('');
        console.error('❌ КРИТИЧЕСКАЯ ОШИБКА: Размер файла слишком мал!');
        console.error('   Ожидаемый размер для колоды с медиа: минимум 500 KB - 5 MB');
        console.error(`   Текущий размер: ${sizeKB.toFixed(2)} KB`);
        console.error('');
        console.error('🔍 ДИАГНОСТИКА ПРОБЛЕМЫ:');
        
        if (deck.words && deck.words.length > 0) {
          const wordsWithImage = deck.words.filter(w => w.image_file && w.image_file.trim() !== '').length;
          const wordsWithAudio = deck.words.filter(w => w.audio_file && w.audio_file.trim() !== '').length;
          
          console.error(`   - Слов с изображениями во фронтенде: ${wordsWithImage} из ${deck.words.length}`);
          console.error(`   - Слов с аудио во фронтенде: ${wordsWithAudio} из ${deck.words.length}`);
          
          if (wordsWithImage > 0 || wordsWithAudio > 0) {
            console.error('');
            console.error('   ⚠️ Медиа-файлы ЕСТЬ во фронтенде, но НЕТ в .apkg!');
            console.error('   ❌ ПРОБЛЕМА НА БЭКЕНДЕ: Бэкенд не упаковывает медиа в .apkg файл');
            console.error('');
            console.error('   💡 РЕШЕНИЕ:');
            console.error('      1. Проверьте Django бэкенд: функцию generate_apkg()');
            console.error('      2. Убедитесь, что медиа-файлы копируются в .apkg архив');
            console.error('      3. Проверьте пути к медиа-файлам на сервере');
            console.error('      4. Проверьте логи Django на наличие ошибок');
          } else {
            console.error('');
            console.error('   ⚠️ Медиа-файлов НЕТ во фронтенде');
            console.error('   💡 Сгенерируйте медиа для слов перед экспортом .apkg');
          }
        }
        console.error('');
        console.error('='.repeat(80));
      } else {
        console.log('✅ Размер файла в норме - медиа, вероятно, включены');
      }

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${deck.name}.apkg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      showSuccess(t.decks.apkgReady, {
        description: `${t.decks.deckName} "${deck.name}" ${t.decks.apkgSaved}`,
      });

      setGenerationStatus('completed');
    } catch (error) {
      console.error('Error generating apkg:', error);
      showError(t.decks.couldNotGenerateApkg, {
        description: t.toast.tryAgain,
      });
      setGenerationStatus('idle');
    } finally {
      setIsGenerating(false);
    }
  };

  // Loading состояние
  if (isLoading) {
    return (
      <div className="container mx-auto max-w-6xl px-4 py-8">
        {/* Навигация */}
        <Skeleton className="mb-6 h-10 w-32" />

        {/* Заголовок */}
        <div className="mb-8">
          <Skeleton className="mb-4 h-10 w-80" />
          <Skeleton className="mb-2 h-5 w-48" />
          <Skeleton className="h-5 w-40" />
        </div>

        {/* Форма */}
        <Skeleton className="mb-6 h-40 w-full" />

        {/* Таблица */}
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  // Если колода не найдена
  if (!deck) {
    return null;
  }

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      {/* Навигация */}
      <Link
        to="/decks"
        className="mb-6 inline-flex items-center text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        {t.decks.backToDecks}
      </Link>

      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <div className="flex items-baseline gap-2 flex-1">
            <EditableTitle
              value={deck.name}
              onSave={handleSaveTitle}
              placeholder={t.decks.deckNamePlaceholder}
            />
            <span className="text-muted-foreground">({deck.words_count})</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(`/training/start?deck_id=${deck.id}`)}
            className="shrink-0"
          >
            <GraduationCap className="mr-1.5 h-4 w-4" />
            {t.trainingDashboard.train}
          </Button>
        </div>
      </div>

      {/* Таблица слов */}
      <div className="mb-6">
        <WordsTable
          words={deck.words}
          deckId={deck.id}
          onDeleteWord={handleDeleteWord}
          onRegenerateImage={handleRegenerateImage}
          onRegenerateAudio={handleRegenerateAudio}
          onEditImage={handleEditImage}
          onDeleteImage={handleDeleteImage}
          onDeleteAudio={handleDeleteAudio}
          onMoveCardToDeck={handleMoveCardToDeck}
          onInvertWord={handleInvertWord}
          onCreateEmptyCard={handleCreateEmptyCard}
          onWordUpdate={handleWordUpdate}
          allDecks={allDecks.filter(d => d.id !== deck.id)}
          targetLang={getLanguageName(deck.target_lang)}
          sourceLang={getLanguageName(deck.source_lang)}
        />
      </div>

      {/* Форма добавления слов */}
      <div className="mb-6">
        <SmartWordInput
          targetLang={deck.target_lang}
          sourceLang={deck.source_lang}
          onAddWords={handleAddWords}
          showChipsInput={true}
        />
      </div>

      {/* Превью добавленных слов (показываем только если есть слова в буфере) */}
      {pendingWords.length > 0 && (
        <div className="mb-6">
          <Card className="p-6">
            <h3 className="mb-4 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-purple-500" />
              {t.decks.wordsToAdd || 'Слова для добавления'} ({pendingWords.length})
            </h3>
            <div className="grid gap-3">
              {pendingWords.map((pair, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg border border-purple-200 bg-purple-50/50 p-3 dark:border-purple-800 dark:bg-purple-950/20"
                >
                  <div className="flex-1">
                    <div className="font-medium text-purple-900 dark:text-purple-100">
                      {pair.word}
                    </div>
                    <div className="text-sm text-purple-700 dark:text-purple-300">
                      {pair.translation}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Настройки медиа + кнопка генерации (показываем только если есть слова в буфере) */}
      {pendingWords.length > 0 && (
        <>
          <div className="mb-6">
            <MediaSettings
              generateImages={generateImages}
              generateAudio={generateAudio}
              imageStyle={imageStyle}
              imageProvider={imageProvider}
              audioProvider={audioProvider}
              onGenerateImagesChange={setGenerateImages}
              onGenerateAudioChange={setGenerateAudio}
              onImageStyleChange={setImageStyle}
              onImageProviderChange={setImageProvider}
              onAudioProviderChange={setAudioProvider}
              disabled={isGenerating}
            />
          </div>

          {/* Прогресс генерации */}
          <GenerationProgress
            status={generationStatus}
            current={generationProgress.current}
            total={generationProgress.total}
            currentWord={generationProgress.currentWord}
          />

          {/* Кнопка генерации карточек */}
          <div className="mb-6">
            <Button
              onClick={handleGenerateCards}
              disabled={isGenerating}
              variant="default"
              size="lg"
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  {t.decks.generating}
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-5 w-5" />
                  {t.decks.generateCards} ({pendingWords.length})
                </>
              )}
            </Button>
          </div>
        </>
      )}

      {/* Кнопка экспорта .apkg (внизу, после списка слов) */}
      {deck.words && deck.words.length > 0 && (
        <div className="flex justify-center">
          <Button
            onClick={handleGenerateApkg}
            disabled={isGenerating}
            variant="default"
            size="lg"
            className="w-full sm:w-auto"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {t.decks.generating}
              </>
            ) : (
              <>
                <Download className="mr-2 h-5 w-5" />
                {t.decks.generateApkg}
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
};

export default DeckEditorPage;