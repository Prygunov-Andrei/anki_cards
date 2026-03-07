import React, { useState, useEffect } from 'react';
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
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { useTranslation } from '../contexts/LanguageContext';
import { BookOpen } from 'lucide-react';
import { LiterarySource } from '../types/literary-context';
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
        console.error('Invalid decks data received:', data);
        setDecks([]);
      }
    } catch (error) {
      console.error('Error loading decks:', error);
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
      console.error('Error deleting deck:', error);
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
      console.log('='.repeat(80));
      console.log('🚀 ГЕНЕРАЦИЯ .APKG ФАЙЛА - НАЧАЛО');
      console.log('='.repeat(80));
      console.log('📋 Информация о колоде (базовая):');
      console.log('  - ID колоды:', deck.id);
      console.log('  - Название:', deck.name);
      console.log('  - Количество слов (words_count):', deck.words_count);
      console.log('  - Целевой язык:', deck.target_lang);
      console.log('  - Исходный язык:', deck.source_lang);
      console.log('');
      console.log('⚠️ ВНИМАНИЕ: На DecksPage нет детальной информации о словах');
      console.log('   Загружаем полную информацию о колоде...');
      
      // Загружаем полную информацию о колоде для диагностики
      const fullDeck = await deckService.getDeck(deck.id);
      
      console.log('');
      console.log('📦 Полная информация о колоде получена:');
      console.log('  - Количество слов (реальное):', fullDeck.words?.length || 0);
      
      if (fullDeck.words && fullDeck.words.length > 0) {
        const wordsWithImage = fullDeck.words.filter(w => w.image_file && w.image_file.trim() !== '').length;
        const wordsWithAudio = fullDeck.words.filter(w => w.audio_file && w.audio_file.trim() !== '').length;
        
        console.log('');
        console.log('📊 Статистика медиа:');
        console.log('  - Слов с изображениями:', wordsWithImage, 'из', fullDeck.words.length);
        console.log('  - Слов с аудио:', wordsWithAudio, 'из', fullDeck.words.length);
        
        console.log('');
        console.log('📝 ПОЛНЫЙ СПИСОК СЛОВ С МЕДИА:');
        fullDeck.words.forEach((word, index) => {
          console.log(`  ${index + 1}. "${word.original_word}" -> "${word.translation}"`);
          console.log(`     ID: ${word.id}`);
          console.log(`     Изображение: ${word.image_file || '❌ НЕТ'}`);
          console.log(`     Аудио: ${word.audio_file || '❌ НЕТ'}`);
        });
      } else {
        console.warn('⚠️ В колоде нет слов!');
      }
      console.log('='.repeat(80));

      // Генерация .apkg файла
      console.log('📡 Отправка запроса на бэкенд: POST /api/decks/' + deck.id + '/generate-apkg/');
      const { file_id } = await deckService.generateDeckApkg(deck.id);
      console.log('✅ Бэкенд вернул file_id:', file_id);

      // Скачивание файла
      console.log('📡 Скачивание файла: GET /api/decks/download/' + file_id + '/');
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
        
        if (fullDeck.words && fullDeck.words.length > 0) {
          const wordsWithImage = fullDeck.words.filter(w => w.image_file && w.image_file.trim() !== '').length;
          const wordsWithAudio = fullDeck.words.filter(w => w.audio_file && w.audio_file.trim() !== '').length;
          
          console.error(`   - Слов с изображениями во фронтенде: ${wordsWithImage} из ${fullDeck.words.length}`);
          console.error(`   - Слов с аудио во фронтенде: ${wordsWithAudio} из ${fullDeck.words.length}`);
          
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
            console.error('');
            console.error('   🔍 ПРОВЕРЬТЕ НА БЭКЕНДЕ:');
            console.error('      - Существуют ли файлы физически на диске?');
            console.error('      - Корректны ли пути к файлам?');
            console.error('      - Права доступа к медиа-файлам?');
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
        console.log('='.repeat(80));
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
      console.error('Error generating apkg:', error);
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
      console.error('Error merging decks:', error);
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
      console.error('Error inverting words:', error);
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
      console.error('Error loading deck details:', error);
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
      console.log('[Empty Cards] Full response:', result);
      console.log('[Empty Cards] empty_cards_count:', result.empty_cards_count);
      console.log('[Empty Cards] empty_cards:', result.empty_cards);
      console.log('[Empty Cards] skipped_cards:', result.skipped_cards);
      console.log('[Empty Cards] errors:', result.errors);

      // Детальное логирование пропущенных карточек
      if (result.skipped_cards && result.skipped_cards.length > 0) {
        console.log('[Empty Cards] Skipped cards details:');
        result.skipped_cards.forEach((card, index) => {
          console.log(`  ${index + 1}. Word ID: ${card.word_id}, Reason: ${card.reason}`);
        });
      }

      // Детальное логирование ошибок
      if (result.errors && result.errors.length > 0) {
        console.error('[Empty Cards] ⚠️ ERRORS DETAILS:');
        result.errors.forEach((error, index) => {
          console.error(`  ${index + 1}. Word ID: ${error.word_id}, Error: ${error.error}`);
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
        console.error('[Empty Cards] Errors occurred!');
        console.error('[Empty Cards] Errors:', result.errors);
        
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
        console.log('[Empty Cards] All cards were skipped!');
        console.log('[Empty Cards] Skipped cards:', result.skipped_cards);
        showInfo(t.words.emptyCardsAlreadyExist || 'Пустые карточки уже существуют', {
          description: `${result.skipped_cards.length} ${t.words.cardsSkipped || 'карточек пропущено'}: ${result.skipped_cards.map(c => c.reason).join(', ')}`,
        });
      } else {
        // Непонятная ситуация - 0 создано, 0 пропущено, 0 ошибок
        console.warn('[Empty Cards] Strange response - no cards created, skipped, or errors!');
        console.warn('[Empty Cards] This might be a backend issue!');
        showInfo(result.message);
      }

      // Обновляем список колод
      await loadDecks();
    } catch (error: unknown) {
      console.error('Error creating empty cards:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : t.common.unknownError);
      showError(t.common.error, {
        description: message,
      });
    }
  };

  /**
   * Сгенерировать литературный контекст для всех слов колоды
   */
  const handleGenerateLiteraryContext = async (deck: Deck, sourceSlug: string) => {
    if (deck.words_count === 0) {
      showError(t.decks.emptyDeck);
      return;
    }

    const source = literarySources.find(s => s.slug === sourceSlug);
    const sourceName = source?.name || sourceSlug;

    try {
      showInfo(`Генерация контекста для "${deck.name}"...`, {
        description: `${deck.words_count} слов, источник: ${sourceName}`,
      });

      const stats = await literaryContextService.generateDeckContext(deck.id, sourceSlug);

      if (stats.generated > 0) {
        showSuccess(`Контекст сгенерирован: ${stats.generated} слов`, {
          description: stats.skipped > 0 ? `Пропущено (уже есть): ${stats.skipped}` : undefined,
        });
      } else if (stats.skipped > 0) {
        showInfo(`Все ${stats.skipped} слов уже имеют литературный контекст`);
      } else {
        showInfo('Нет слов для генерации контекста');
      }
    } catch (error: unknown) {
      console.error('Error generating literary context:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : 'Неизвестная ошибка');
      showError('Ошибка генерации контекста', { description: message });
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

      <PageHelpButton pageKey="decks" />
    </div>
  );
}