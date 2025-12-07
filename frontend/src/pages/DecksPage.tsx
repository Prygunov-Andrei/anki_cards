import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Deck } from '../types';
import { deckService } from '../services/deck.service';
import { DeckCard } from '../components/DeckCard';
import { DeleteDeckModal } from '../components/DeleteDeckModal';
import { NetworkErrorBanner } from '../components/NetworkErrorBanner';
import { Skeleton } from '../components/ui/skeleton';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { useTranslation } from '../contexts/LanguageContext';
import { BookOpen } from 'lucide-react';

/**
 * Страница DecksPage - список всех колод пользователя
 */
export default function DecksPage() {
  const t = useTranslation();
  const [decks, setDecks] = useState<Deck[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasNetworkError, setHasNetworkError] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedDeck, setSelectedDeck] = useState<Deck | null>(null);
  const navigate = useNavigate();

  // Загрузка колод при монтировании
  useEffect(() => {
    loadDecks();
  }, []);

  /**
   * Загрузить список колод
   */
  const loadDecks = async () => {
    try {
      setIsLoading(true);
      setHasNetworkError(false);
      const data = await deckService.getDecks();
      setDecks(data);
    } catch (error) {
      console.error('Error loading decks:', error);
      setHasNetworkError(true);
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
   * Генерация .apkg файла
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

      // Генерация .apkg файла
      const { file_id } = await deckService.generateDeckApkg(deck.id);

      // Скачивание файла
      const blob = await deckService.downloadDeck(file_id);

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
    </div>
  );
}