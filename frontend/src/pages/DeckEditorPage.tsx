import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Deck } from '../types';
import { deckService } from '../services/deck.service';
import { mediaService } from '../services/media.service';
import { WordTranslationPair } from '../components/SmartWordInput';
import { ImageStyle } from '../components/ImageStyleSelector';
import { GenerationStatus } from '../components/GenerationProgress';
import { Skeleton } from '../components/ui/skeleton';
import { DeckEditorHeader } from '../components/deck-editor/DeckEditorHeader';
import { DeckEditorWordInput } from '../components/deck-editor/DeckEditorWordInput';
import { DeckEditorWordList } from '../components/deck-editor/DeckEditorWordList';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { logger } from '../utils/logger';
import { TIMEOUTS } from '../utils/timeouts';
import { useTranslation } from '../contexts/LanguageContext';
import axios from 'axios';

/**
 * Страница DeckEditorPage - редактор колоды
 * Логика как на главной: добавляем слова → настройки медиа → генерация карточек → добавление в олоду
 * iOS 25 стиль, оптимизирован для iPhone 17 Air
 */
const DeckEditorPage: React.FC = () => {
  const t = useTranslation();
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

  useEffect(() => {
    loadDeck();
    loadAllDecks();
  }, [id]);

  const loadDeck = async () => {
    if (!id) { navigate('/decks'); return; }
    setIsLoading(true);
    try {
      const data = await deckService.getDeck(Number(id));
      setDeck(data);
    } catch (error) {
      logger.error('Error loading deck:', error);
      showError(t.decks.couldNotLoadDecks, { description: t.decks.tryRefreshPage });
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
      logger.error('Error loading all decks:', error);
      showError(t.decks.couldNotLoadDecksList, { description: t.decks.tryRefreshPage });
    }
  };

  const handleSaveTitle = async (newTitle: string) => {
    if (!deck) return;
    try {
      const updatedDeck = await deckService.updateDeck(deck.id, { name: newTitle });
      setDeck(updatedDeck);
      showSuccess(t.decks.titleUpdated, { description: `${t.decks.deckRenamedTo} "${newTitle}"` });
    } catch (error) {
      logger.error('Error updating deck title:', error);
      showError(t.decks.couldNotUpdateTitle, { description: t.toast.tryAgain });
      throw error;
    }
  };

  const handleAddWords = async (pairs: WordTranslationPair[]) => {
    setPendingWords(prev => [...prev, ...pairs]);
    const count = pairs.length;
    const wordText = count === 1 ? t.decks.wordAdded : count < 5 ? t.decks.wordsAdded : t.decks.wordsManyAdded;
    showSuccess(`${count} ${wordText}`, { description: t.decks.pressGenerateCards });
  };

  const handleGenerateCards = async () => {
    if (!deck || pendingWords.length === 0) return;

    logger.log('Starting card generation...', { deck: deck.id, pendingWords, generateImages, generateAudio, imageStyle });
    setIsGenerating(true);

    try {
      logger.log('Adding words to deck...');
      const addResult = await deckService.addWordsToDeck(deck.id, pendingWords);
      logger.log('Words added, result:', addResult);

      const addedWordIds = addResult.added_words || [];
      logger.log('Added word IDs:', addedWordIds);

      if (addedWordIds.length === 0) {
        logger.log('No words added!');
        setIsGenerating(false);
        setPendingWords([]);
        return;
      }

      logger.log('Reloading deck...');
      const updatedDeck = await deckService.getDeck(deck.id);
      setDeck(updatedDeck);

      const wordsById = new Map(updatedDeck.words?.map(w => [w.id, w]) || []);
      const newWords = addedWordIds.map(id => wordsById.get(id)).filter(Boolean);
      logger.log('Found new words:', newWords);

      if (newWords.length === 0) {
        logger.log('No new words found in deck!');
        setIsGenerating(false);
        setPendingWords([]);
        return;
      }

      const wordCount = newWords.length;
      const wordText = wordCount === 1 ? t.decks.word : t.decks.wordsTwo;
      showInfo(t.decks.generatingMedia, { description: `${t.decks.creatingMediaFor} ${wordCount} ${wordText}...` });

      // Генерация изображений
      if (generateImages) {
        logger.log('Starting image generation...');
        setGenerationStatus('generating_images');
        setGenerationProgress({ current: 0, total: newWords.length, currentWord: '' });

        for (let i = 0; i < newWords.length; i++) {
          const word = newWords[i];
          logger.log(`Generating image ${i + 1}/${newWords.length} for "${word.original_word}" (word_id: ${word.id})`);
          setGenerationProgress({ current: i + 1, total: newWords.length, currentWord: word.original_word });

          try {
            await mediaService.generateImage({
              word: word.original_word,
              translation: word.translation,
              language: deck.target_lang,
              image_style: imageStyle,
              word_id: word.id,
              provider: imageProvider,
            });
            logger.log(`Image generated for "${word.original_word}"`);
          } catch (error) {
            logger.error(`Error generating image for "${word.original_word}":`, error);
          }
        }
      }

      // Генерация аудио
      if (generateAudio) {
        logger.log('Starting audio generation...');
        setGenerationStatus('generating_audio');
        setGenerationProgress({ current: 0, total: newWords.length, currentWord: '' });

        for (let i = 0; i < newWords.length; i++) {
          const word = newWords[i];
          logger.log(`Generating audio ${i + 1}/${newWords.length} for "${word.original_word}" (word_id: ${word.id})`);
          setGenerationProgress({ current: i + 1, total: newWords.length, currentWord: word.original_word });

          try {
            const provider = audioProvider === 'auto' ? undefined : audioProvider;
            await mediaService.generateAudio({
              word: word.original_word,
              language: deck.target_lang,
              provider,
              word_id: word.id,
            });
            logger.log(`Audio generated for "${word.original_word}"`);
          } catch (error) {
            logger.error(`Error generating audio for "${word.original_word}":`, error);
          }
        }
      }

      // Перезагружаем колоду с обновленными медиа
      logger.log('Reloading deck with updated media...');
      const reloadedDeck = await deckService.getDeck(deck.id);
      logger.log('Reloaded deck words:', reloadedDeck.words);
      setDeck(reloadedDeck);

      setGenerationStatus('complete');
      const cardCount = newWords.length;
      const cardText = cardCount === 1 ? t.decks.cardAdded : cardCount < 5 ? t.decks.cardsAddedPlural : t.decks.cardsManyAdded;
      showSuccess(t.decks.cardsAdded, { description: `${cardCount} ${cardText} ${t.decks.toDeckWithMedia}` });

      setPendingWords([]);
      setTimeout(() => {
        setGenerationStatus('idle');
        setGenerationProgress({ current: 0, total: 0, currentWord: '' });
      }, TIMEOUTS.UI_RESET);
    } catch (error) {
      logger.error('Error generating cards:', error);
      showError(t.decks.couldNotAddCards, { description: t.toast.tryAgain });
      setGenerationStatus('idle');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeleteWord = async (wordId: number) => {
    if (!deck) return;
    try {
      await deckService.removeWordFromDeck(deck.id, wordId);
      await loadDeck();
      showSuccess(t.decks.wordDeleted, { description: t.decks.wordRemovedFromDeck });
    } catch (error) {
      logger.error('Error deleting word:', error);
      showError(t.decks.couldNotDeleteWord, { description: t.toast.tryAgain });
      throw error;
    }
  };

  const handleRegenerateImage = async (wordId: number, word: string, translation: string) => {
    if (!deck) return;
    try {
      showInfo(t.decks.generatingImage, { description: `${t.decks.creatingNewImageFor} "${word}"` });
      await mediaService.generateImage({
        word, translation, language: deck.target_lang, image_style: imageStyle,
        word_id: wordId, provider: imageProvider,
      });
      await loadDeck();
      showSuccess(t.decks.imageUpdated, { description: `${t.decks.newImageFor} "${word}" ${t.decks.ready}` });
    } catch (error) {
      logger.error(`Error regenerating image for "${word}":`, error);
      showError(t.decks.couldNotCreateImage, { description: t.toast.tryAgain });
    }
  };

  const handleRegenerateAudio = async (wordId: number, word: string) => {
    if (!deck) return;
    try {
      showInfo(t.decks.generatingAudio, { description: `${t.decks.creatingNewAudioFor} "${word}"` });
      const provider = audioProvider === 'auto' ? undefined : audioProvider;
      await mediaService.generateAudio({ word, language: deck.target_lang, provider, word_id: wordId });
      await loadDeck();
      showSuccess(t.decks.audioUpdated, { description: `${t.decks.newAudioFor} "${word}" ${t.decks.ready}` });
    } catch (error) {
      logger.error(`Error regenerating audio for "${word}":`, error);
      showError(t.decks.couldNotCreateAudio, { description: t.toast.tryAgain });
    }
  };

  const handleEditImage = async (wordId: number, mixin: string) => {
    if (!deck) return;
    try {
      showInfo(t.words.editImage, { description: `${t.words.editImageHint}: "${mixin}"` });
      await mediaService.editImage({ word_id: wordId, mixin });
      await loadDeck();
      showSuccess(t.decks.imageUpdated, { description: t.decks.ready });
    } catch (error) {
      logger.error(`Error editing image with mixin "${mixin}":`, error);
      showError(t.decks.couldNotCreateImage, { description: t.toast.tryAgain });
    }
  };

  const handleDeleteImage = async (wordId: number) => {
    if (!deck) return;
    try {
      showInfo('Удаление изображения...', { description: 'Удаляем изображение' });
      await mediaService.updateWordMedia(deck.id, wordId, { image_file: '' });
      await loadDeck();
      showSuccess('Изображение удалено!', { description: 'Изображение успешно удалено' });
    } catch (error) {
      logger.error('Error deleting image:', error);
      showError('Не удалось удалить изображение', { description: t.toast.tryAgain });
    }
  };

  const handleDeleteAudio = async (wordId: number) => {
    if (!deck) return;
    try {
      showInfo('Удаление аудио...', { description: 'Удаляем аудио' });
      await mediaService.updateWordMedia(deck.id, wordId, { audio_file: '' });
      await loadDeck();
      showSuccess(t.words.audioDeleted, { description: t.words.audioDeleted });
    } catch (error) {
      logger.error('Error deleting audio:', error);
      showError('Не удалось удалить аудио', { description: t.toast.tryAgain });
    }
  };

  const handleMoveCardToDeck = async (wordId: number, toDeckId: number, toDeckName: string) => {
    if (!deck) return;
    const word = deck.words?.find(w => w.id === wordId);
    if (!word) {
      showError(t.decks.wordNotFound, { description: t.decks.tryRefreshPage });
      return;
    }
    try {
      showInfo(t.decks.movingCard, { description: `${t.decks.movingToDeck} \"${toDeckName}\"` });
      await deckService.copyAndMoveCard(
        { id: word.id, original_word: word.original_word, translation: word.translation, image_file: word.image_file, audio_file: word.audio_file },
        deck.id, toDeckId,
      );
      await loadDeck();
      showSuccess(t.decks.cardMoved, { description: `${t.decks.wordAddedToDeck} \"${toDeckName}\"` });
    } catch (error) {
      logger.error('Error moving card:', error);
      showError(t.decks.couldNotMoveCard, { description: t.toast.tryAgain });
    }
  };

  const handleInvertWord = async (wordId: number) => {
    if (!deck) return;
    try {
      showInfo(t.words.invertingWord);
      const result = await deckService.invertWord(deck.id, wordId);
      showSuccess(t.words.wordInverted, { description: result.message });
      await loadDeck();
    } catch (error: unknown) {
      logger.error('Error inverting word:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : t.common.unknownError);
      showError(t.common.error, { description: message });
    }
  };

  const handleCreateEmptyCard = async (wordId: number) => {
    if (!deck) return;
    try {
      showInfo(t.words.creatingEmptyCard);
      const result = await deckService.createEmptyCard(deck.id, wordId);
      showSuccess(t.words.emptyCardCreated, { description: result.message });
      await loadDeck();
    } catch (error: unknown) {
      logger.error('Error creating empty card:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.error || error.message)
        : (error instanceof Error ? error.message : t.common.unknownError);
      showError(t.common.error, { description: message });
    }
  };

  const handleWordUpdate = async (wordId: number, data: { original_word?: string; translation?: string }) => {
    if (!deck) return;
    try {
      await mediaService.updateWordMedia(deck.id, wordId, data);
      await loadDeck();
      showSuccess(t.decks.wordUpdated || 'Word updated', { description: t.decks.changesSaved || 'Changes saved successfully' });
    } catch (error: unknown) {
      logger.error('Error updating word:', error);
      if (axios.isAxiosError(error) && error.response?.data?.errors) {
        const errors = error.response.data.errors;
        const errorMessage = errors.original_word || errors.translation || t.decks.couldNotUpdateWord || 'Could not update word';
        showError(errorMessage, { description: t.toast.tryAgain });
      } else {
        showError(t.decks.couldNotUpdateWord || 'Could not update word', { description: t.toast.tryAgain });
      }
      await loadDeck();
      throw error;
    }
  };

  const handleGenerateApkg = async () => {
    if (!deck) return;
    if (!deck.words || deck.words.length === 0) {
      showError(t.decks.emptyDeck, { description: t.decks.addWordBeforeGeneration });
      return;
    }

    setIsGenerating(true);
    try {
      setGenerationStatus('creating_deck');
      setGenerationProgress({ current: 0, total: 0, currentWord: '' });

      logger.log('APKG generation started for deck:', deck.id, deck.name);
      showInfo(t.decks.generatingApkg, { description: t.decks.collectingApkg });

      const { file_id } = await deckService.generateDeckApkg(deck.id);
      logger.log('Backend returned file_id:', file_id);

      const blob = await deckService.downloadDeck(file_id);
      logger.log('Downloaded file size:', blob.size, 'bytes');

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${deck.name}.apkg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      showSuccess(t.decks.apkgReady, { description: `${t.decks.deckName} "${deck.name}" ${t.decks.apkgSaved}` });
      setGenerationStatus('completed');
    } catch (error) {
      logger.error('Error generating apkg:', error);
      showError(t.decks.couldNotGenerateApkg, { description: t.toast.tryAgain });
      setGenerationStatus('idle');
    } finally {
      setIsGenerating(false);
    }
  };

  // Loading состояние
  if (isLoading) {
    return (
      <div className="container mx-auto max-w-6xl px-4 py-8">
        <Skeleton className="mb-6 h-10 w-32" />
        <div className="mb-8">
          <Skeleton className="mb-4 h-10 w-80" />
          <Skeleton className="mb-2 h-5 w-48" />
          <Skeleton className="h-5 w-40" />
        </div>
        <Skeleton className="mb-6 h-40 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!deck) return null;

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      <DeckEditorHeader
        deck={deck}
        onSaveTitle={handleSaveTitle}
      />

      <DeckEditorWordList
        deck={deck}
        allDecks={allDecks}
        isGenerating={isGenerating}
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
        onGenerateApkg={handleGenerateApkg}
      />

      <DeckEditorWordInput
        targetLang={deck.target_lang}
        sourceLang={deck.source_lang}
        pendingWords={pendingWords}
        isGenerating={isGenerating}
        generateImages={generateImages}
        generateAudio={generateAudio}
        imageStyle={imageStyle}
        imageProvider={imageProvider}
        audioProvider={audioProvider}
        generationStatus={generationStatus}
        generationProgress={generationProgress}
        onAddWords={handleAddWords}
        onGenerateCards={handleGenerateCards}
        onGenerateImagesChange={setGenerateImages}
        onGenerateAudioChange={setGenerateAudio}
        onImageStyleChange={setImageStyle}
        onImageProviderChange={setImageProvider}
        onAudioProviderChange={setAudioProvider}
      />
    </div>
  );
};

export default DeckEditorPage;
