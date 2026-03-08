import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHelpButton } from '../components/PageHelpButton';
import { Deck } from '../types';
import { deckService } from '../services/deck.service';
import { literaryContextService } from '../services/literary-context.service';
import { DeckCard } from '../components/DeckCard';
import { DeleteDeckModal } from '../components/DeleteDeckModal';
import { InvertWordsConfirmModal } from '../components/InvertWordsConfirmModal';
import { NetworkErrorBanner } from '../components/NetworkErrorBanner';
import { Skeleton } from '../components/ui/skeleton';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { logger } from '../utils/logger';
import { TIMEOUTS } from '../utils/timeouts';
import { usePolling } from '../hooks/usePolling';
import { useTranslation } from '../contexts/LanguageContext';
import { BookOpen, X, Loader2, ArrowRight } from 'lucide-react';
import { LiterarySource, JobStatus } from '../types/literary-context';
import axios from 'axios';

/**
 * Страница DecksPage - список всех колод пользователя
 */
export default function DecksPage() {
  const t = useTranslation();
  const [decks, setDecks] = useState<Deck[]>([]);
  const [literarySources, setLiterarySources] = useState<LiterarySource[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasNetworkError, setHasNetworkError] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedDeck, setSelectedDeck] = useState<Deck | null>(null);
  const [isInvertWordsModalOpen, setIsInvertWordsModalOpen] = useState(false);
  const [selectedDeckForInvert, setSelectedDeckForInvert] = useState<Deck | null>(null);
  const navigate = useNavigate();

  // Literary context generation progress
  const [contextJob, setContextJob] = useState<JobStatus | null>(null);
  const [contextJobDeckName, setContextJobDeckName] = useState('');
  const [contextJobSourceName, setContextJobSourceName] = useState('');
  const [pollingJobId, setPollingJobId] = useState<string | null>(null);

  usePolling<JobStatus>({
    fetcher: () => literaryContextService.getJobStatus(pollingJobId!),
    onData: setContextJob,
    shouldStop: (data) => data.status === 'completed' || data.status === 'failed',
    onComplete: () => {
      setPollingJobId(null);
      loadDecks();
    },
    interval: TIMEOUTS.UI_RESET,
    enabled: !!pollingJobId,
  });

  // Загрузка колод и литературных источников при монтировании
  useEffect(() => {
    loadDecks();
    literaryContextService.getSources().then(setLiterarySources).catch(() => {});
  }, []);

  /**
   * Загрузить список колод
   */
  const loadDecks = async () => {
    try {
      setIsLoading(true);
      setHasNetworkError(false);
      const data = await deckService.getDecks();
      // Проверяем, что данные действительно массив
      if (Array.isArray(data)) {
        setDecks(data);
      } else {
        logger.error('Invalid decks data received:', data);
        setDecks([]);
      }
    } catch (error) {
      logger.error('Error loading decks:', error);
      setHasNetworkError(true);
      // При ошибке устанавливаем пустой массив
      setDecks([]);
      showError(t.decks.couldNotLoadDecks, {
        description: t.errors.checkConnection,
      });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Удалить колоду
   */
  const handleDeleteDeck = async () => {
    if (!selectedDeck) return;

    try {
      await deckService.deleteDeck(selectedDeck.id);
      setDecks(decks.filter((d) => d.id !== selectedDeck.id));
      showSuccess(t.decks.deckDeleted, {
        description: `${t.toast.deckWith} "${selectedDeck.name}" ${t.decks.deckWasDeleted}`,
      });
      setIsDeleteModalOpen(false);
      setSelectedDeck(null);
    } catch (error) {
      logger.error('Error deleting deck:', error);
      showError(t.decks.couldNotDeleteDeck, {
        description: t.toast.tryAgain,
      });
    }
  };

  /**
   * Редактировать колоду
   */
  const handleEditDeck = (deck: Deck) => {
    navigate(`/decks/${deck.id}`);
  };

  /**
   * Генерация .apkg файла для колоды
   */
  const handleGenerateApkg = async (deck: Deck) => {
    // Проверяем только words_count, а не наличие массива words
    if (deck.words_count === 0) {
      showError(t.decks.emptyDeck, {
        description: t.decks.addWordBeforeGeneration,
      });
      return;
    }

    try {
      showInfo(t.decks.generatingApkg, {
        description: t.decks.collectingApkg,
      });

      // 🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА ПЕРЕД ГЕНЕРАЦИЕЙ
      logger.log('='.repeat(80));
      logger.log('🚀 ГЕНЕРАЦИЯ .APKG ФАЙЛА - НАЧАЛО');
      logger.log('='.repeat(80));
      logger.log('📋 Информация о колоде (базовая):');
      logger.log('  - ID колоды:', deck.id);
      logger.log('  - Название:', deck.name);
      logger.log('  - Количество слов (words_count):', deck.words_count);
      logger.log('  - Целевой язык:', deck.target_lang);
      logger.log('  - Исходный язык:', deck.source_lang);
      logger.log('');
      logger.log('⚠️ ВНИМАНИЕ: На DecksPage нет детальной информации о словах');
      logger.log('   Загружаем полную информацию о колоде...');
      
      // Загружаем полную информацию о колоде для диагностики
      const fullDeck = await deckService.getDeck(deck.id);
      
      logger.log('');
      logger.log('📦 Полная информация о колоде получена:');
      logger.log('  - Количество слов (реальное):', fullDeck.words?.length || 0);
      
      if (fullDeck.words && fullDeck.words.length > 0) {
        const wordsWithImage = fullDeck.words.filter(w => w.image_file && w.image_file.trim() !== '').length;
        const wordsWithAudio = fullDeck.words.filter(w => w.audio_file && w.audio_file.trim() !== '').length;
        
        logger.log('');
        logger.log('📊 Статистика медиа:');
        logger.log('  - Слов с изображениями:', wordsWithImage, 'из', fullDeck.words.length);
        logger.log('  - Слов с аудио:', wordsWithAudio, 'из', fullDeck.words.length);
        
        logger.log('');
        logger.log('📝 ПОЛНЫЙ СПИСОК СЛОВ С МЕДИА:');
        fullDeck.words.forEach((word, index) => {
          logger.log(`  ${index + 1}. "${word.original_word}" -> "${word.translation}"`);
          logger.log(`     ID: ${word.id}`);
          logger.log(`     Изображение: ${word.image_file || '❌ НЕТ'}`);
          logger.log(`     Аудио: ${word.audio_file || '❌ НЕТ'}`);
        });
      } else {
        logger.warn('⚠️ В колоде нет слов!');
      }
      logger.log('='.repeat(80));

      // Генерация .apkg файла
      logger.log('📡 Отправка запроса на бэкенд: POST /api/decks/' + deck.id + '/generate-apkg/');
      const { file_id } = await deckService.generateDeckApkg(deck.id);
      logger.log('✅ Бэкенд вернул file_id:', file_id);

      // Скачивание файла
      logger.log('📡 Скачивание файла: GET /api/decks/download/' + file_id + '/');
      const blob = await deckService.downloadDeck(file_id);

      // 🔍 ДИАГНОСТИКА: Проверяем размер файла
      const sizeMB = blob.size / 1024 / 1024;
      const sizeKB = blob.size / 1024;
      logger.log('');
      logger.log('📦 РЕЗУЛЬТАТ:');
      logger.log(`  - Размер файла: ${sizeKB.toFixed(2)} KB (${sizeMB.toFixed(2)} MB, ${blob.size} bytes)`);
      logger.log(`  - Тип файла: ${blob.type}`);
      
      if (sizeKB < 100) {
        logger.error('');
        logger.error('❌ КРИТИЧЕСКАЯ ОШИБКА: Размер файла слишком мал!');
        logger.error('   Ожидаемый размер для колоды с медиа: минимум 500 KB - 5 MB');
        logger.error(`   Текущий размер: ${sizeKB.toFixed(2)} KB`);
        logger.error('');
        logger.error('🔍 ДИАГНОСТИКА ПРОБЛЕМЫ:');
        
        if (fullDeck.words && fullDeck.words.length > 0) {
          const wordsWithImage = fullDeck.words.filter(w => w.image_file && w.image_file.trim() !== '').length;
          const wordsWithAudio = fullDeck.words.filter(w => w.audio_file && w.audio_file.trim() !== '').length;
          
          logger.error(`   - Слов с изображениями во фронтенде: ${wordsWithImage} из ${fullDeck.words.length}`);
          logger.error(`   - Слов с аудио во фронтенде: ${wordsWithAudio} из ${fullDeck.words.length}`);
          
          if (wordsWithImage > 0 || wordsWithAudio > 0) {
            logger.error('');
            logger.error('   ⚠️ Медиа-файлы ЕСТЬ во фронтенде, но НЕТ в .apkg!');
            logger.error('   ❌ ПРОБЛЕМА НА БЭКЕНДЕ: Бэкенд не упаковывает медиа в .apkg файл');
            logger.error('');
            logger.error('   💡 РЕШЕНИЕ:');
            logger.error('      1. Проверьте Django бэкенд: функцию generate_apkg()');
            logger.error('      2. Убедитесь, что медиа-файлы копируются в .apkg архив');
            logger.error('      3. Проверьте пути к медиа-файлам на сервере');
            logger.error('      4. Проверьте логи Django на наличие ошибок');
            logger.error('');
            logger.error('   🔍 ПРОВЕРЬТЕ НА БЭКЕНДЕ:');
            logger.error('      - Существуют ли файлы физически на диске?');
            logger.error('      - Корректны ли пути к файлам?');
            logger.error('      - Права доступа к медиа-файлам?');
          } else {
            logger.error('');
            logger.error('   ⚠️ Медиа-файлов НЕТ во фронтенде');
            logger.error('   💡 Сгенерируйте медиа для слов перед экспортом .apkg');
          }
        }
        logger.error('');
        logger.error('='.repeat(80));
      } else {
        logger.log('✅ Размер файла в норме - медиа, вероятно, включены');
        logger.log('='.repeat(80));
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
        description: `${t.toast.deckWith} "${deck.name}" ${t.decks.apkgSaved}`,
      });
    } catch (error) {
      logger.error('Error generating apkg:', error);
      showError(t.decks.couldNotGenerateApkg, {
        description: t.toast.tryAgain,
      });
    }
  };

  /**
   * Открыть модальное окно удаления
   */
  const openDeleteModal = (deck: Deck) => {
    setSelectedDeck(deck);
    setIsDeleteModalOpen(true);
  };

  /**
   * Объединить колоды
   */
  const handleMergeDecks = async (sourceDeckId: number, targetDeckId: number) => {
    try {
      showInfo(t.decks.mergingDecks);

      const result = await deckService.mergeDecks({
        deck_ids: [sourceDeckId, targetDeckId],
        target_deck_id: targetDeckId,
        delete_source_decks: true,
      });

      showSuccess(t.decks.decksMerged, {
        description: `${t.decks.mergedWords}: ${result.words_count}`,
      });

      // Обновляем список колод
      await loadDecks();
    } catch (error: unknown) {
      logger.error('Error merging decks:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : t.common.unknownError);
      showError(t.decks.couldNotMergeDecks, {
        description: message,
      });
    }
  };

  /**
   * Инвертировать все слова в колоде
   */
  const handleInvertAllWords = async () => {
    if (!selectedDeckForInvert) return;

    try {
      showInfo(t.words.invertingAllWords);

      const result = await deckService.invertAllWords(selectedDeckForInvert.id);

      showSuccess(
        `${result.inverted_cards_count} ${t.words.wordsInverted}`,
        {
          description: result.message,
        }
      );

      // Закрываем модалку
      setIsInvertWordsModalOpen(false);
      setSelectedDeckForInvert(null);

      // Обновляем список колод
      await loadDecks();
    } catch (error: unknown) {
      logger.error('Error inverting words:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : t.common.unknownError);
      showError(t.common.error, {
        description: message,
      });
    }
  };

  /**
   * Открыть модальное окно подтверждения инвертирования слов
   */
  const openInvertWordsModal = async (deck: Deck) => {
    try {
      // Загружаем полную информацию о колоде, чтобы получить слова с типами
      const fullDeck = await deckService.getDeck(deck.id);
      setSelectedDeckForInvert(fullDeck);
      setIsInvertWordsModalOpen(true);
    } catch (error) {
      logger.error('Error loading deck details:', error);
      // Если не удалось загрузить, используем базовую информацию
      setSelectedDeckForInvert(deck);
      setIsInvertWordsModalOpen(true);
    }
  };

  /**
   * Создать пустые карточки для всех слов в колоде
   */
  const handleCreateEmptyCards = async (deck: Deck) => {
    if (deck.words_count === 0) {
      showError(t.decks.emptyDeck, {
        description: t.decks.addWords,
      });
      return;
    }

    try {
      showInfo(t.words.creatingEmptyCards);

      const result = await deckService.createEmptyCards(deck.id);

      // Логируем полный ответ для отладки
      logger.log('[Empty Cards] Full response:', result);
      logger.log('[Empty Cards] empty_cards_count:', result.empty_cards_count);
      logger.log('[Empty Cards] empty_cards:', result.empty_cards);
      logger.log('[Empty Cards] skipped_cards:', result.skipped_cards);
      logger.log('[Empty Cards] errors:', result.errors);

      // Детальное логирование пропущенных карточек
      if (result.skipped_cards && result.skipped_cards.length > 0) {
        logger.log('[Empty Cards] Skipped cards details:');
        result.skipped_cards.forEach((card, index) => {
          logger.log(`  ${index + 1}. Word ID: ${card.word_id}, Reason: ${card.reason}`);
        });
      }

      // Детальное логирование ошибок
      if (result.errors && result.errors.length > 0) {
        logger.error('[Empty Cards] ⚠️ ERRORS DETAILS:');
        result.errors.forEach((error, index) => {
          logger.error(`  ${index + 1}. Word ID: ${error.word_id}, Error: ${error.error}`);
        });
      }

      // Проверяем результат
      if (result.empty_cards_count > 0) {
        showSuccess(
          `${result.empty_cards_count} ${t.words.emptyCardsCreated}`,
          {
            description: result.message,
          }
        );
      } else if (result.errors && result.errors.length > 0) {
        // Были ошибки - показываем их с приоритетом
        logger.error('[Empty Cards] Errors occurred!');
        logger.error('[Empty Cards] Errors:', result.errors);
        
        // Проверяем, это ошибка дубликата пустого слова?
        const isDuplicateEmptyWordError = result.errors.some(e => 
          e.error?.includes('duplicate key value') && 
          e.error?.includes('original_word')
        );
        
        if (isDuplicateEmptyWordError) {
          showError('⚠️ Ограничение функциональности', {
            description: `Создана 1 пустая карточка. Остальные ${result.errors.length} не созданы из-за технического ограничения. Используйте создание пустой карточки для каждого слова отдельно.`,
          });
        } else {
          showError(t.common.error, {
            description: `${result.errors.length} ошибок при создании карточек`,
          });
        }
      } else if (result.skipped_cards && result.skipped_cards.length > 0) {
        // Все карточки были пропущены (уже существуют)
        logger.log('[Empty Cards] All cards were skipped!');
        logger.log('[Empty Cards] Skipped cards:', result.skipped_cards);
        showInfo(t.words.emptyCardsAlreadyExist || 'Пустые карточки уже существуют', {
          description: `${result.skipped_cards.length} ${t.words.cardsSkipped || 'карточек пропущено'}: ${result.skipped_cards.map(c => c.reason).join(', ')}`,
        });
      } else {
        // Непонятная ситуация - 0 создано, 0 пропущено, 0 ошибок
        logger.warn('[Empty Cards] Strange response - no cards created, skipped, or errors!');
        logger.warn('[Empty Cards] This might be a backend issue!');
        showInfo(result.message);
      }

      // Обновляем список колод
      await loadDecks();
    } catch (error: unknown) {
      logger.error('Error creating empty cards:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : t.common.unknownError);
      showError(t.common.error, {
        description: message,
      });
    }
  };

  /**
   * Сгенерировать литературный контекст для всех слов колоды (async с прогрессом)
   */
  const handleGenerateLiteraryContext = async (deck: Deck, sourceSlug: string) => {
    if (deck.words_count === 0) {
      showError(t.decks.emptyDeck);
      return;
    }

    const source = literarySources.find(s => s.slug === sourceSlug);
    const sourceName = source?.name || sourceSlug;
    setContextJobDeckName(deck.name);
    setContextJobSourceName(sourceName);

    try {
      const { job_id } = await literaryContextService.generateDeckContextAsync(deck.id, sourceSlug);

      // Initialize job display
      setContextJob({
        job_id,
        status: 'pending',
        progress: 0,
        current_word: '',
        stats: { total: 0, generated: 0, skipped: 0, fallback: 0, errors: 0 },
        unmatched_words: [],
        error_message: '',
      });

      // Start polling via usePolling hook
      setPollingJobId(job_id);
    } catch (error: unknown) {
      logger.error('Error starting literary context generation:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : 'Неизвестная ошибка');
      showError('Ошибка генерации контекста', { description: message });
    }
  };

  const handleMoveUnmatched = useCallback(async () => {
    if (!contextJob?.unmatched_words?.length) return;

    try {
      // Create new deck for unmatched words
      const newDeckName = `${contextJobDeckName} (без рубашки)`;
      const newDeck = await deckService.createDeck({
        name: newDeckName,
        target_lang: 'de',
        source_lang: 'ru',
      });

      // Add unmatched words to new deck
      const wordData = contextJob.unmatched_words.map(w => ({
        word: w.original_word,
        translation: w.translation,
      }));
      await deckService.addWordsToDeck(newDeck.id, wordData);

      showSuccess(`${contextJob.unmatched_words.length} слов перемещено в "${newDeckName}"`);
      setContextJob(null);
      await loadDecks();
    } catch (error: unknown) {
      logger.error('Error moving unmatched words:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : 'Ошибка');
      showError('Не удалось переместить слова', { description: message });
    }
  }, [contextJob, contextJobDeckName]);

  const handleSetDeckLiterarySource = async (deck: Deck, sourceSlug: string | null, useGlobal: boolean) => {
    try {
      await deckService.setDeckLiterarySource(deck.id, sourceSlug, useGlobal);
      if (useGlobal) {
        showSuccess('Колода использует глобальную настройку');
      } else if (sourceSlug) {
        const source = literarySources.find(s => s.slug === sourceSlug);
        showSuccess(`Источник: ${source?.name || sourceSlug}`);
      } else {
        showSuccess('Стандартный контекст (без рубашки)');
      }
      await loadDecks();
    } catch (error: unknown) {
      logger.error('Error setting deck literary source:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : 'Неизвестная ошибка');
      showError('Ошибка', { description: message });
    }
  };

  // Состояние загрузки
  if (isLoading) {
    return (
      <div className="container mx-auto max-w-6xl px-4 py-8">
        {/* Skeleton сетка */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="overflow-hidden rounded-lg border bg-card">
              <Skeleton className="h-48 w-full" />
              <div className="p-5 space-y-3">
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-40" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Пустое состояние
  if (decks.length === 0) {
    return (
      <div className="container mx-auto max-w-6xl px-4 py-8">
        {/* Пустое состояние */}
        <div className="flex min-h-[50vh] flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-200 bg-gradient-to-br from-blue-50/50 to-purple-50/50 p-8 text-center dark:border-gray-800 dark:from-blue-950/20 dark:to-purple-950/20">
          <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-pink-400">
            <BookOpen className="h-12 w-12 text-white" strokeWidth={1.5} />
          </div>
          <h2 className="mb-2 text-gray-900 dark:text-gray-100">
            {t.decks.noDeck}
          </h2>
          <p className="mb-8 max-w-md text-gray-600 dark:text-gray-400">
            {t.decks.goToMainPage}
          </p>
        </div>
      </div>
    );
  }

  // Список колод
  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      {/* Баннер ошибки сети */}
      {hasNetworkError && <NetworkErrorBanner onRetry={loadDecks} />}

      {/* Сетка колод */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {decks.map((deck) => (
          <DeckCard
            key={deck.id}
            deck={deck}
            onEdit={handleEditDeck}
            onDelete={openDeleteModal}
            onGenerateApkg={handleGenerateApkg}
            onMerge={handleMergeDecks}
            onInvertAll={openInvertWordsModal}
            onCreateEmptyCards={handleCreateEmptyCards}
            onGenerateLiteraryContext={handleGenerateLiteraryContext}
            onSetDeckLiterarySource={handleSetDeckLiterarySource}
            literarySources={literarySources}
            availableDecks={decks.filter((d) => d.id !== deck.id)}
          />
        ))}
      </div>

      {/* Модальное окно удаления */}
      <DeleteDeckModal
        isOpen={isDeleteModalOpen}
        deck={selectedDeck}
        onConfirm={handleDeleteDeck}
        onCancel={() => {
          setIsDeleteModalOpen(false);
          setSelectedDeck(null);
        }}
      />

      {/* Модальное окно подтверждения инвертирования слов */}
      <InvertWordsConfirmModal
        isOpen={isInvertWordsModalOpen}
        deck={selectedDeckForInvert}
        onConfirm={handleInvertAllWords}
        onCancel={() => {
          setIsInvertWordsModalOpen(false);
          setSelectedDeckForInvert(null);
        }}
      />

      {/* Literary context generation progress modal */}
      {contextJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 w-full max-w-md rounded-xl border bg-card p-6 shadow-lg">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {contextJob.status === 'completed' ? 'Генерация завершена' :
                 contextJob.status === 'failed' ? 'Ошибка генерации' :
                 `Генерация: ${contextJobSourceName}`}
              </h3>
              {(contextJob.status === 'completed' || contextJob.status === 'failed') && (
                <button onClick={() => setContextJob(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>

            {(contextJob.status === 'pending' || contextJob.status === 'running') && (
              <>
                <Progress value={contextJob.progress} className="mb-3" />
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>
                    {contextJob.progress}%
                    {contextJob.current_word && ` — ${contextJob.current_word}`}
                  </span>
                </div>
              </>
            )}

            {contextJob.status === 'completed' && (
              <>
                <div className="mb-4 space-y-2 text-sm">
                  <p className="text-green-600 dark:text-green-400">
                    {contextJob.stats.generated} слов получили рубашку «{contextJobSourceName}»
                  </p>
                  {contextJob.stats.skipped > 0 && (
                    <p className="text-muted-foreground">Пропущено (уже есть): {contextJob.stats.skipped}</p>
                  )}
                  {contextJob.stats.errors > 0 && (
                    <p className="text-red-500">Ошибок: {contextJob.stats.errors}</p>
                  )}
                  {contextJob.unmatched_words.length > 0 && (
                    <p className="text-amber-600 dark:text-amber-400">
                      {contextJob.unmatched_words.length} слов не найдены в источнике
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  {contextJob.unmatched_words.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={handleMoveUnmatched}
                    >
                      <ArrowRight className="mr-1.5 h-4 w-4" />
                      Переместить несовпавшие
                    </Button>
                  )}
                  <Button
                    size="sm"
                    className="flex-1"
                    onClick={() => setContextJob(null)}
                  >
                    Готово
                  </Button>
                </div>
              </>
            )}

            {contextJob.status === 'failed' && (
              <p className="text-sm text-red-500">
                {contextJob.error_message || 'Неизвестная ошибка'}
              </p>
            )}
          </div>
        </div>
      )}

      <PageHelpButton pageKey="decks" />
    </div>
  );
}