import React, { useState, useEffect, useRef } from 'react';
import { WordTranslationPair } from '../components/TranslationTable';
import { ImageStyle } from '../components/ImageStyleSelector';
import { GenerationStatus } from '../components/GenerationProgress';
import { WordInputSection } from '../components/main/WordInputSection';
import { MainPageActionArea } from '../components/main/MainPageActionArea';
import { useAutoTranslate } from '../hooks/useAutoTranslate';
import { useTokenContext } from '../contexts/TokenContext';
import { useAuthContext } from '../contexts/AuthContext';
import { useTranslation } from '../contexts/LanguageContext';
import { useDraftDeck } from '../contexts/DraftDeckContext';
import { deckService } from '../services/deck.service';
import { mediaService } from '../services/media.service';
import { wordsService } from '../services/words.service';
import { showSuccess, showError, showInfo } from '../utils/toast-helpers';
import { logger } from '../utils/logger';
import { TIMEOUTS } from '../utils/timeouts';
import { getCardImageUrl, getAudioUrl, getRelativePath } from '../utils/url-helpers';
import { getTotalMediaCost } from '../utils/token-formatting';
import { literaryContextService } from '../services/literary-context.service';
import { LiterarySource } from '../types/literary-context';
import { PageHelpButton } from '../components/PageHelpButton';

/**
 * Main page - quick card generation
 * iOS 25 style, optimised for mobile
 */
export default function MainPage() {
  const t = useTranslation();
  const { balance, checkBalance, refreshBalance } = useTokenContext();
  const { user, updateUser } = useAuthContext();

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

  // Adapter: DraftTranslationPair[] <-> WordTranslationPair[]
  const translations: WordTranslationPair[] = draftTranslations;
  const setTranslations = (pairs: WordTranslationPair[]) => {
    setDraftTranslations(pairs.map(p => ({ word: p.word, translation: p.translation })));
  };

  // Literary sources for auto-naming
  const [literarySources, setLiterarySources] = useState<LiterarySource[]>([]);

  // Providers from user profile
  const imageStyle: ImageStyle = (user?.image_style as ImageStyle) || 'balanced';
  const imageProvider = user?.image_provider || 'openai';
  const audioProvider = user?.audio_provider || 'openai';
  const geminiModel = user?.gemini_model || 'gemini-2.5-flash-image';

  // UI states
  const [isGenerating, setIsGenerating] = useState(false);
  const [showInsufficientTokensModal, setShowInsufficientTokensModal] = useState(false);

  // Generation progress state
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus>('idle');
  const [generationProgress, setGenerationProgress] = useState({ current: 0, total: 0, currentWord: '' });

  // AbortController for generation cancellation
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  // Saved deck ID
  const [savedDeckId, setSavedDeckId] = useState<number | null>(null);

  // Languages from user profile
  const targetLang = user?.learning_language || 'en';
  const sourceLang = user?.native_language || 'ru';

  // Auto-translate hook
  const { isTranslating, isProcessingWords, handleWordsChange } = useAutoTranslate({
    words,
    translations,
    setWords,
    setTranslations,
    setWordIds,
    updateGeneratedImages,
    updateGeneratedAudio,
    targetLang,
    sourceLang,
    userLanguage: user?.learning_language || 'de',
    isGenerating,
    isProcessingWords: false,
    t,
  });

  // Ref for form reset timer cleanup on unmount
  const resetTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => {
    return () => {
      if (resetTimerRef.current) clearTimeout(resetTimerRef.current);
    };
  }, []);

  // Protect against tab close during generation
  useEffect(() => {
    if (!isGenerating) return;
    const handler = (e: BeforeUnloadEvent) => { e.preventDefault(); };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isGenerating]);

  // On draft restore with wordIds, check media on server
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
  }, []);

  // Notify about draft restoration
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
  }, []);

  // Load literary sources for auto-naming
  useEffect(() => {
    literaryContextService.getSources().then(setLiterarySources).catch(() => {});
  }, []);

  // Auto deck name
  const getDefaultDeckName = () => {
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    if (user?.active_literary_source && literarySources.length > 0) {
      const src = literarySources.find(s => s.slug === user.active_literary_source);
      return src ? `${src.name}_${date}` : `Deck_${date}`;
    }
    return `${t.decks.newDeck}_${date}`;
  };

  useEffect(() => {
    if (!deckName) {
      setDeckName(getDefaultDeckName());
    }
  }, [user?.active_literary_source, literarySources]);

  // Helper: convert imageProvider to backend format
  const getProviderParams = () => {
    if (imageProvider === 'openai') {
      return { provider: 'openai' as const, gemini_model: undefined };
    }
    if (imageProvider === 'gemini') {
      return { provider: 'gemini' as const, gemini_model: geminiModel as 'gemini-2.5-flash-image' | 'gemini-3.1-flash-image-preview' };
    }
    if (imageProvider === 'nano-banana') {
      return { provider: 'gemini' as const, gemini_model: 'gemini-3.1-flash-image-preview' as const };
    }
    return { provider: 'openai' as const, gemini_model: undefined };
  };

  const handleTranslationsChange = (pairs: WordTranslationPair[]) => {
    setTranslations(pairs);
    setWords(pairs.map(pair => pair.word));
  };

  const handlePhotoWordsExtracted = (photoWords: string[]) => {
    const existingLower = new Set(words.map((w) => w.toLowerCase()));
    const newWords = photoWords.filter((w) => !existingLower.has(w.toLowerCase()));
    if (newWords.length > 0) {
      handleWordsChange([...words, ...newWords]);
    }
  };

  const handleRegenerateImage = async (word: string) => {
    const pair = translations.find(t => t.word === word);
    if (!pair) return;
    try {
      showInfo('Generating image...', { description: `Creating new image for "${word}"` });
      const providerParams = getProviderParams();
      const { image_url } = await mediaService.generateImage({
        word: pair.word,
        translation: pair.translation,
        language: targetLang,
        image_style: imageStyle,
        ...providerParams,
      });
      const absoluteUrl = getCardImageUrl(image_url);
      if (absoluteUrl) {
        updateGeneratedImages(prev => ({ ...prev, [pair.word]: absoluteUrl }));
      }
      showSuccess('Image updated!', { description: `New image for "${word}" is ready` });
    } catch (error) {
      logger.error(`Error regenerating image for "${word}":`, error);
      showError('Could not create image', { description: 'Try again' });
    }
  };

  const handleRegenerateAudio = async (word: string) => {
    const pair = translations.find(t => t.word === word);
    if (!pair) return;
    try {
      showInfo('Generating audio...', { description: `Creating new audio for "${word}"` });
      const { audio_url } = await mediaService.generateAudio({
        word: pair.word,
        language: targetLang,
        provider: audioProvider as 'openai' | 'gtts',
      });
      const absoluteUrl = getAudioUrl(audio_url);
      if (absoluteUrl) {
        updateGeneratedAudio(prev => ({ ...prev, [pair.word]: absoluteUrl }));
      }
      showSuccess('Audio updated!', { description: `New audio for "${word}" is ready` });
    } catch (error) {
      logger.error(`Error generating audio for "${word}":`, error);
      showError('Could not create audio', { description: 'Try again' });
    }
  };

  const validateTranslations = (): boolean => {
    if (translations.length === 0) { showError('Add words for generation'); return false; }
    const emptyTranslations = translations.filter((pair) => !pair.translation.trim());
    if (emptyTranslations.length > 0) {
      showError('Fill in translations for all words', { description: `Missing translations: ${emptyTranslations.length}` });
      return false;
    }
    if (!generateImages && !generateAudio) {
      showError('Select at least one media type', { description: 'Enable image or audio generation' });
      return false;
    }
    return true;
  };

  const validateDeckCreation = (): boolean => {
    if (!deckName.trim()) { showError(t.toast.enterDeckName); return false; }
    if (translations.length === 0) { showError(t.toast.addWordsToGenerate); return false; }
    const hasMedia = Object.keys(generatedImages).length > 0 || Object.keys(generatedAudio).length > 0;
    if (!hasMedia) {
      showError(t.toast.generateMediaFirst, { description: t.toast.clickGenerateMedia });
      return false;
    }
    return true;
  };

  const handleCancelGeneration = () => {
    if (abortController) { abortController.abort(); setAbortController(null); }
    setIsGenerating(false);
    setGenerationStatus('idle');
    setGenerationProgress({ current: 0, total: 0, currentWord: '' });
    showInfo('Generation cancelled', { description: 'Process stopped' });
  };

  const handleGenerateMedia = async () => {
    if (!validateTranslations()) return;

    const wordsNeedingImages = generateImages ? translations.filter(p => !generatedImages[p.word]).length : 0;
    const wordsNeedingAudio = generateAudio ? translations.filter(p => !generatedAudio[p.word]).length : 0;
    const wordsToGenerate = Math.max(wordsNeedingImages, wordsNeedingAudio);
    const requiredTokens = getTotalMediaCost(
      wordsToGenerate,
      generateImages && wordsNeedingImages > 0,
      generateAudio && wordsNeedingAudio > 0,
      imageProvider === 'nano-banana' ? 'gemini' : (imageProvider as 'openai' | 'gemini'),
      geminiModel as 'gemini-2.5-flash-image' | 'gemini-3.1-flash-image-preview'
    );
    const hasEnoughTokens = await checkBalance(requiredTokens);
    if (!hasEnoughTokens || balance < requiredTokens) {
      setShowInsufficientTokensModal(true);
      return;
    }

    setIsGenerating(true);
    const controller = new AbortController();
    setAbortController(controller);

    try {
      let failedImageWords: string[] = [];

      // Stage 1: Generate images
      if (generateImages) {
        const pairsNeedingImages = translations.filter(p => !generatedImages[p.word]);
        setGenerationStatus('generating_images');
        setGenerationProgress({ current: 0, total: pairsNeedingImages.length, currentWord: '' });

        for (let i = 0; i < pairsNeedingImages.length; i++) {
          if (controller.signal.aborted) throw new Error('Generation cancelled');
          const pair = pairsNeedingImages[i];
          setGenerationProgress({ current: i + 1, total: pairsNeedingImages.length, currentWord: pair.word });

          try {
            const timeoutPromise = new Promise<never>((_, reject) => {
              setTimeout(() => reject(new Error('Image generation timeout')), TIMEOUTS.IMAGE_GENERATION);
            });
            const providerParams = getProviderParams();
            const imagePromise = mediaService.generateImage({
              word: pair.word, translation: pair.translation, language: targetLang,
              image_style: imageStyle, ...providerParams,
            }, controller.signal);
            const { image_url } = await Promise.race([imagePromise, timeoutPromise]);
            const absoluteUrl = getCardImageUrl(image_url);
            if (absoluteUrl) updateGeneratedImages(prev => ({ ...prev, [pair.word]: absoluteUrl }));
          } catch (error) {
            if (controller.signal.aborted) throw new Error('Generation cancelled');
            logger.error(`Error generating image for "${pair.word}":`, error);
            failedImageWords.push(pair.word);
            if (error instanceof Error && error.message === 'Image generation timeout') {
              logger.warn(`Timeout for image "${pair.word}" - will retry later`);
            }
          }
        }
      }

      // Stage 2: Generate audio
      let failedAudioWords: string[] = [];
      if (generateAudio) {
        const pairsNeedingAudio = translations.filter(p => !generatedAudio[p.word]);
        setGenerationStatus('generating_audio');
        setGenerationProgress({ current: 0, total: pairsNeedingAudio.length, currentWord: '' });

        for (let i = 0; i < pairsNeedingAudio.length; i++) {
          if (controller.signal.aborted) throw new Error('Generation cancelled');
          const pair = pairsNeedingAudio[i];
          setGenerationProgress({ current: i + 1, total: pairsNeedingAudio.length, currentWord: pair.word });

          try {
            const timeoutPromise = new Promise<never>((_, reject) => {
              setTimeout(() => reject(new Error('Audio generation timeout')), TIMEOUTS.AUDIO_GENERATION);
            });
            const audioPromise = mediaService.generateAudio({
              word: pair.word, language: targetLang, provider: audioProvider as 'openai' | 'gtts',
            }, controller.signal);
            const { audio_url } = await Promise.race([audioPromise, timeoutPromise]);
            const absoluteUrl = getAudioUrl(audio_url);
            if (absoluteUrl) updateGeneratedAudio(prev => ({ ...prev, [pair.word]: absoluteUrl }));
          } catch (error) {
            if (controller.signal.aborted) throw new Error('Generation cancelled');
            logger.error(`Error generating audio for "${pair.word}":`, error);
            failedAudioWords.push(pair.word);
            if (error instanceof Error && error.message === 'Audio generation timeout') {
              logger.warn(`Timeout for audio "${pair.word}" - will retry later`);
            }
          }
        }
      }

      // Stage 3: Retry failed words (up to 2 attempts)
      const maxRetries = 2;
      const retryDelay = TIMEOUTS.RETRY_DELAY;

      for (let retryAttempt = 1; retryAttempt <= maxRetries; retryAttempt++) {
        if (failedImageWords.length === 0 && failedAudioWords.length === 0) break;
        if (controller.signal.aborted) throw new Error('Generation cancelled');

        logger.log(`Retry attempt ${retryAttempt}/${maxRetries}:`, { images: failedImageWords.length, audio: failedAudioWords.length });
        await new Promise(resolve => setTimeout(resolve, retryDelay));

        if (failedImageWords.length > 0) {
          setGenerationStatus('generating_images');
          const currentFailedImages = [...failedImageWords];
          failedImageWords = [];
          for (let i = 0; i < currentFailedImages.length; i++) {
            if (controller.signal.aborted) throw new Error('Generation cancelled');
            const word = currentFailedImages[i];
            const pair = translations.find(t => t.word === word);
            if (!pair) continue;
            setGenerationProgress({ current: i + 1, total: currentFailedImages.length, currentWord: `\u{1F504} ${word}` });
            try {
              const timeoutPromise = new Promise<never>((_, reject) => {
                setTimeout(() => reject(new Error('Image generation timeout')), TIMEOUTS.IMAGE_GENERATION);
              });
              const imagePromise = mediaService.generateImage({
                word: pair.word, translation: pair.translation, language: targetLang,
                image_style: imageStyle, ...getProviderParams(),
              }, controller.signal);
              const { image_url } = await Promise.race([imagePromise, timeoutPromise]);
              const absoluteUrl = getCardImageUrl(image_url);
              if (absoluteUrl) {
                updateGeneratedImages(prev => ({ ...prev, [pair.word]: absoluteUrl }));
                logger.log(`Retry successful for image: "${word}"`);
              }
            } catch (error) {
              if (controller.signal.aborted) throw new Error('Generation cancelled');
              logger.error(`Retry ${retryAttempt} failed for image "${word}":`, error);
              failedImageWords.push(word);
            }
          }
        }

        if (failedAudioWords.length > 0) {
          setGenerationStatus('generating_audio');
          const currentFailedAudio = [...failedAudioWords];
          failedAudioWords = [];
          for (let i = 0; i < currentFailedAudio.length; i++) {
            if (controller.signal.aborted) throw new Error('Generation cancelled');
            const word = currentFailedAudio[i];
            const pair = translations.find(t => t.word === word);
            if (!pair) continue;
            setGenerationProgress({ current: i + 1, total: currentFailedAudio.length, currentWord: `\u{1F504} ${word}` });
            try {
              const timeoutPromise = new Promise<never>((_, reject) => {
                setTimeout(() => reject(new Error('Audio generation timeout')), TIMEOUTS.AUDIO_GENERATION);
              });
              const audioPromise = mediaService.generateAudio({
                word: pair.word, language: targetLang, provider: audioProvider as 'openai' | 'gtts',
              }, controller.signal);
              const { audio_url } = await Promise.race([audioPromise, timeoutPromise]);
              const absoluteUrl = getAudioUrl(audio_url);
              if (absoluteUrl) {
                updateGeneratedAudio(prev => ({ ...prev, [pair.word]: absoluteUrl }));
                logger.log(`Retry successful for audio: "${word}"`);
              }
            } catch (error) {
              if (controller.signal.aborted) throw new Error('Generation cancelled');
              logger.error(`Retry ${retryAttempt} failed for audio "${word}":`, error);
              failedAudioWords.push(word);
            }
          }
        }
      }

      setGenerationStatus('idle');
      setIsGenerating(false);
      setAbortController(null);

      const totalFailed = failedImageWords.length + failedAudioWords.length;
      const uniqueFailedWords = new Set([...failedImageWords, ...failedAudioWords]);

      if (totalFailed > 0) {
        logger.warn('Some media generation failed after retries:', { failedImages: failedImageWords, failedAudio: failedAudioWords, uniqueWords: Array.from(uniqueFailedWords) });
        showSuccess('Media generated!', {
          description: `${translations.length - uniqueFailedWords.size}/${translations.length} words successful. ${uniqueFailedWords.size > 0 ? `Failed: ${Array.from(uniqueFailedWords).join(', ')}` : ''}`,
        });
      } else {
        showSuccess('Media generated!', {
          description: 'Check media in the table. You can regenerate any of them.',
        });
      }

      await refreshBalance();
    } catch (error) {
      if (error instanceof Error && error.message === 'Generation cancelled') return;
      logger.error('Error generating media:', error);
      showError('Error generating media', { description: error instanceof Error ? error.message : 'Try again' });
      setGenerationStatus('idle');
      setIsGenerating(false);
      setAbortController(null);
    }
  };

  const handleCreateDeck = async () => {
    if (!validateDeckCreation()) return;
    setIsGenerating(true);

    try {
      setGenerationStatus('creating_deck');
      setGenerationProgress({ current: 0, total: 0, currentWord: '' });

      const translationsDict = translations.reduce((acc, pair) => {
        acc[pair.word] = pair.translation;
        return acc;
      }, {} as Record<string, string>);

      const imageFiles: Record<string, string> = {};
      const audioFiles: Record<string, string> = {};

      for (const [word, url] of Object.entries(generatedImages)) {
        const relativePath = getRelativePath(url as string);
        if (relativePath) imageFiles[word] = relativePath;
      }
      for (const [word, url] of Object.entries(generatedAudio)) {
        const relativePath = getRelativePath(url as string);
        if (relativePath) audioFiles[word] = relativePath;
      }

      logger.log('Sending to backend:');
      logger.log('  - Words:', translations.length);
      logger.log('  - Images:', Object.keys(imageFiles).length);
      logger.log('  - Audio:', Object.keys(audioFiles).length);

      const { file_id, deck_id } = await deckService.generateCards({
        words: translations.map((pair) => pair.word),
        translations: translationsDict,
        language: targetLang,
        deck_name: deckName,
        image_files: imageFiles,
        audio_files: audioFiles,
        save_to_decks: true,
      });

      if (deck_id) {
        setSavedDeckId(deck_id);
        logger.log(`Deck saved with ID: ${deck_id}`);

        // Attach media to words in the saved deck
        try {
          logger.log('Attaching media to deck words...');
          const createdDeck = await deckService.getDeck(deck_id);

          logger.log('Created deck:', { id: createdDeck.id, name: createdDeck.name, words_count: createdDeck.words_count, actual_words: createdDeck.words?.length || 0 });

          if (createdDeck.words && createdDeck.words.length > 0) {
            let attachedCount = 0;
            for (const word of createdDeck.words) {
              const mediaUpdates: { image_file?: string; audio_file?: string } = {};
              if (imageFiles[word.original_word]) mediaUpdates.image_file = imageFiles[word.original_word];
              if (audioFiles[word.original_word]) mediaUpdates.audio_file = audioFiles[word.original_word];

              if (Object.keys(mediaUpdates).length > 0) {
                const result = await mediaService.updateWordMedia(deck_id, word.id, mediaUpdates);
                attachedCount++;
                logger.log(`Media attached to "${word.original_word}":`, result.updated_fields);
              }
            }
            if (attachedCount > 0) logger.log(`Total media attached to ${attachedCount} words`);
          }
        } catch (error) {
          logger.error('Error attaching media to saved deck:', error);
        }
      }

      const blob = await deckService.downloadDeck(file_id);
      const sizeMB = blob.size / 1024 / 1024;
      logger.log(`apkg file size: ${sizeMB.toFixed(2)} MB (${blob.size} bytes)`);

      if (sizeMB < 1) {
        logger.warn('File size suspiciously small - media may be missing');
        showInfo('File downloaded, but size is suspiciously small', {
          description: `Size: ${sizeMB.toFixed(2)} MB. Media files may not be included. Check the file in Anki.`,
        });
      }

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${deckName}.apkg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setGenerationStatus('complete');

      if (deck_id) {
        showSuccess(t.toast.deckSavedAndDownloaded, {
          description: `${t.toast.deckWith} "${deckName}" ${t.toast.deckAvailableInMyDecks}`,
        });
      } else {
        showSuccess(t.toast.cardsCreated, {
          description: `${t.toast.deckWith} "${deckName}" ${t.toast.with} ${translations.length} ${translations.length === 1 ? t.toast.word : t.toast.words} ${t.toast.isReady}`,
        });
      }

      await refreshBalance();

      resetTimerRef.current = setTimeout(() => {
        clearDraft();
        setSavedDeckId(null);
        setGenerationStatus('idle');
        setGenerationProgress({ current: 0, total: 0, currentWord: '' });
      }, TIMEOUTS.UI_RESET);
    } catch (error) {
      logger.error('Error generating cards:', error);
      showError(t.toast.couldNotGenerateCards, { description: t.toast.tryAgain });
      setGenerationStatus('idle');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeleteWord = (word: string) => {
    const newTranslations = translations.filter((t) => t.word !== word);
    setTranslations(newTranslations);
    setWords(newTranslations.map((t) => t.word));
    const newImages = { ...generatedImages };
    delete newImages[word];
    setGeneratedImages(newImages);
    const newAudio = { ...generatedAudio };
    delete newAudio[word];
    setGeneratedAudio(newAudio);
  };

  const handleClearDraft = () => {
    if (window.confirm(t.draft.confirmClear)) {
      clearDraft();
      setSavedDeckId(null);
      setGenerationStatus('idle');
      setGenerationProgress({ current: 0, total: 0, currentWord: '' });
    }
  };

  const estimatedCost = getTotalMediaCost(
    translations.length,
    generateImages,
    generateAudio,
    imageProvider === 'nano-banana' ? 'gemini' : (imageProvider as 'openai' | 'gemini'),
    geminiModel as 'gemini-2.5-flash-image' | 'gemini-3.1-flash-image-preview'
  );

  const hasMedia = Object.keys(generatedImages).length > 0 || Object.keys(generatedAudio).length > 0;

  return (
    <div className="mx-auto max-w-4xl space-y-4 p-4 pb-24">
      <WordInputSection
        words={words}
        translations={translations}
        targetLang={targetLang}
        sourceLang={sourceLang}
        isGenerating={isGenerating}
        isTranslating={isTranslating}
        isProcessingWords={isProcessingWords}
        generatedImages={generatedImages}
        generatedAudio={generatedAudio}
        activeLiterarySource={user?.active_literary_source ?? null}
        onWordsChange={handleWordsChange}
        onTranslationsChange={handleTranslationsChange}
        onPhotoWordsExtracted={handlePhotoWordsExtracted}
        onDeleteWord={handleDeleteWord}
        onRegenerateImage={handleRegenerateImage}
        onRegenerateAudio={handleRegenerateAudio}
        onSourceChange={(slug: string | null) => updateUser({ active_literary_source: slug })}
        onClearDraft={handleClearDraft}
        t={t}
      />

      <MainPageActionArea
        translations={translations}
        generateImages={generateImages}
        generateAudio={generateAudio}
        setGenerateImages={setGenerateImages}
        setGenerateAudio={setGenerateAudio}
        isGenerating={isGenerating}
        generationStatus={generationStatus}
        generationProgress={generationProgress}
        hasMedia={hasMedia}
        deckName={deckName}
        setDeckName={setDeckName}
        savedDeckId={savedDeckId}
        estimatedCost={estimatedCost}
        balance={balance}
        showInsufficientTokensModal={showInsufficientTokensModal}
        setShowInsufficientTokensModal={setShowInsufficientTokensModal}
        onGenerateMedia={handleGenerateMedia}
        onCreateDeck={handleCreateDeck}
        onCancelGeneration={handleCancelGeneration}
        t={t}
      />

      <PageHelpButton pageKey="create" />
    </div>
  );
}
