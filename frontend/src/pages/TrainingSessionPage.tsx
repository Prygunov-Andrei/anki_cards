import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { trainingService } from '../services/training.service';
import { wordsService } from '../services/words.service';
import { aiGenerationService } from '../services/ai-generation.service';
import { deckService } from '../services/deck.service';
import type {
  CardListItem,
  TrainingSessionResponse,
  AnswerQuality,
} from '../types';
import { TrainingCard, type WordDetail } from '../components/training/TrainingCard';
import { TrainingCardMenu } from '../components/training/TrainingCardMenu';
import { getAudioUrl, getAbsoluteUrl } from '../utils/url-helpers';
import { AnswerButtons } from '../components/training/AnswerButtons';
import { SessionTimer } from '../components/training/SessionTimer';
import { Button } from '../components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { Trophy, ArrowRight, RotateCcw, Volume2, Lightbulb, BookOpen, Loader2, DoorOpen } from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage } from '../contexts/LanguageContext';
import { logger } from '../utils/logger';

interface LocationState {
  session: TrainingSessionResponse;
  durationMinutes: number;
  sessionStartedAt?: number;
  currentIndex?: number;
  isFlipped?: boolean;
  answered?: number;
  correct?: number;
  deckId?: number;
}

export default function TrainingSessionPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useLanguage();
  const state = location.state as LocationState | null;

  // Session data
  const [sessionId, setSessionId] = useState('');
  const [cards, setCards] = useState<CardListItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isAnswering, setIsAnswering] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [availableDecks, setAvailableDecks] = useState<Array<{ id: number; name: string }>>([]);

  // Lock page scroll while training session is open to avoid
  // iPad/iPhone rubber-band empty-space scrolling.
  useEffect(() => {
    const prevHtmlOverflow = document.documentElement.style.overflow;
    const prevBodyOverflow = document.body.style.overflow;
    const prevBodyOverscroll = document.body.style.overscrollBehavior;

    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
    document.body.style.overscrollBehavior = 'none';

    return () => {
      document.documentElement.style.overflow = prevHtmlOverflow;
      document.body.style.overflow = prevBodyOverflow;
      document.body.style.overscrollBehavior = prevBodyOverscroll;
    };
  }, []);

  // Whether there's an active session that should be protected from accidental navigation
  const isActiveSession = !!state?.session && !isFinished;

  // Block tab close / refresh via beforeunload
  useEffect(() => {
    if (!isActiveSession) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isActiveSession]);

  // Block browser back button via popstate interception
  useEffect(() => {
    if (!isActiveSession) return;

    // Push a sentry state so pressing Back pops it instead of leaving
    window.history.pushState({ trainingGuard: true }, '');

    const handler = () => {
      // User pressed Back — show confirmation dialog instead of navigating
      // Re-push sentry so that subsequent presses are also caught
      window.history.pushState({ trainingGuard: true }, '');
      setShowExitDialog(true);
    };

    window.addEventListener('popstate', handler);
    return () => {
      window.removeEventListener('popstate', handler);
      // Clean up the sentry entry if the component unmounts normally (e.g. confirmed exit)
      if (window.history.state?.trainingGuard) {
        window.history.back();
      }
    };
  }, [isActiveSession]);

  // Hint generation state
  const [isGeneratingHint, setIsGeneratingHint] = useState(false);

  // Stats for this session
  const [sessionStats, setSessionStats] = useState({
    answered: 0,
    correct: 0,
    newCount: 0,
    reviewCount: 0,
    learningCount: 0,
  });

  // Duration
  const [durationMinutes, setDurationMinutes] = useState(0);
  const [sessionStartedAt, setSessionStartedAt] = useState<number>(Date.now());

  // Word detail cache
  const [wordDetailCache, setWordDetailCache] = useState<Record<number, WordDetail>>({});

  // Card start time for time_spent
  const cardStartTime = useRef<number>(Date.now());

  // Audio player ref
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Initialize from navigation state
  useEffect(() => {
    if (!state?.session) {
      navigate('/training', { replace: true });
      return;
    }
    setSessionId(state.session.session_id);
    setCards(state.session.cards);
    setDurationMinutes(state.durationMinutes);
    setSessionStartedAt(state.sessionStartedAt ?? Date.now());
    setCurrentIndex(state.currentIndex ?? 0);
    setIsFlipped(state.isFlipped ?? false);
    setSessionStats((prev) => ({
      ...prev,
      answered: state.answered ?? 0,
      correct: state.correct ?? 0,
      newCount: state.session.new_count,
      reviewCount: state.session.review_count,
      learningCount: state.session.learning_count,
    }));
  }, [navigate, state]);

  // Deck list for "move to deck" menu
  useEffect(() => {
    let cancelled = false;
    const loadDecks = async () => {
      try {
        const decks = await deckService.getDecks();
        if (!cancelled) {
          setAvailableDecks(decks.map((d) => ({ id: d.id, name: d.name })));
        }
      } catch {
        // Non-critical for training flow
      }
    };
    loadDecks();
    return () => {
      cancelled = true;
    };
  }, []);

  // Preload word details for current + next card
  const currentCard = cards[currentIndex];

  const loadWordDetail = useCallback(
    async (card: CardListItem) => {
      if (wordDetailCache[card.id]) return;
      try {
        const word = await wordsService.getWord(card.word_id, state?.deckId);
        setWordDetailCache((prev) => ({
          ...prev,
          [card.id]: {
            etymology: word.etymology,
            hint_text: word.hint_text,
            hint_audio: word.hint_audio ?? undefined,
            sentences: word.sentences?.map(s => ({ text: s.sentence, source: s.source || 'ai' })),
            image_file: word.image_file ?? undefined,
            image_url: word.image_url ?? undefined,
            language: word.language,
          },
        }));
      } catch {
        // Silent fail — word details are supplementary
      }
    },
    [wordDetailCache, state?.deckId]
  );

  // Preload word details for current card (and next card for smoother UX)
  useEffect(() => {
    if (!currentCard) return;
    loadWordDetail(currentCard);
    const nextCard = cards[currentIndex + 1];
    if (nextCard) {
      loadWordDetail(nextCard);
    }
  }, [currentIndex, cards]);

  // Update card media (image/audio) in the cards array
  const updateCardMedia = useCallback((cardId: number, updates: { image_file?: string; audio_file?: string }) => {
    setCards((prev) =>
      prev.map((c) => (c.id === cardId ? { ...c, ...updates } : c))
    );
  }, []);

  // Update word detail cache
  const updateWordDetail = useCallback((cardId: number, updates: Partial<WordDetail>) => {
    setWordDetailCache((prev) => ({
      ...prev,
      [cardId]: { ...prev[cardId], ...updates },
    }));
  }, []);

  // Play audio helper
  const playAudio = useCallback((url: string) => {
    try {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      audioRef.current = new Audio(url);
      audioRef.current.play().catch(() => { /* autoplay blocked */ });
    } catch {
      // Silent fail
    }
  }, []);

  const handleFlip = () => {
    if (!isFlipped && currentCard) {
      setIsFlipped(true);
      // Auto-play word audio on flip
      const audioUrl = getAudioUrl(currentCard.audio_file);
      if (audioUrl) {
        playAudio(audioUrl);
      }
    }
  };

  // Handle hint button press (auto-generate if needed)
  const handleHintPress = async () => {
    if (!currentCard) return;
    const detail = wordDetailCache[currentCard.id];

    // If hint_audio exists, just play it
    if (detail?.hint_audio) {
      const hintUrl = getAbsoluteUrl(detail.hint_audio);
      if (hintUrl) {
        playAudio(hintUrl);
        return;
      }
    }

    // Otherwise, generate hint with audio
    setIsGeneratingHint(true);
    try {
      const result = await aiGenerationService.generateHint({
        word_id: currentCard.word_id,
        generate_audio: true,
      });

      // Update cache with new hint data
      updateWordDetail(currentCard.id, {
        hint_text: result.hint_text,
        hint_audio: result.hint_audio_url ?? undefined,
      });

      // Play the generated audio
      if (result.hint_audio_url) {
        const hintUrl = getAbsoluteUrl(result.hint_audio_url);
        if (hintUrl) {
          playAudio(hintUrl);
        }
      }
      toast.success(t.training.serviceZone.hintGenerated);
    } catch {
      toast.error(t.training.serviceZone.hintError);
    } finally {
      setIsGeneratingHint(false);
    }
  };

  // Handle listen button (play word audio)
  const handleListen = () => {
    if (!currentCard) return;
    const audioUrl = getAudioUrl(currentCard.audio_file);
    if (audioUrl) {
      playAudio(audioUrl);
    }
  };

  const buildTrainingReturnState = useCallback((): LocationState | null => {
    if (!sessionId || cards.length === 0) {
      return null;
    }
    return {
      session: {
        session_id: sessionId,
        cards,
        estimated_time: 0,
        new_count: sessionStats.newCount,
        review_count: sessionStats.reviewCount,
        learning_count: sessionStats.learningCount,
        total_count: cards.length,
      },
      durationMinutes,
      sessionStartedAt,
      currentIndex,
      isFlipped,
      answered: sessionStats.answered,
      correct: sessionStats.correct,
      deckId: state?.deckId,
    };
  }, [cards, currentIndex, durationMinutes, isFlipped, sessionId, sessionStartedAt, sessionStats, state?.deckId]);

  const handleDeleteWord = async (wordId: number) => {
    await wordsService.deleteWord(wordId);
    setCards((prev) => {
      const nextCards = prev.filter((c) => c.word_id !== wordId);
      if (nextCards.length === 0) {
        setIsFinished(true);
        return [];
      }
      const nextIndex = Math.min(currentIndex, nextCards.length - 1);
      setCurrentIndex(nextIndex);
      setIsFlipped(false);
      cardStartTime.current = Date.now();
      return nextCards;
    });
    toast.success(t.words.delete);
  };

  const handleMoveToDeck = async (wordId: number, deckId: number, deckName: string) => {
    const wordCard = cards.find((c) => c.word_id === wordId);
    if (!wordCard) return;
    await deckService.addWordsToDeck(deckId, [{
      word: wordCard.word_text,
      translation: wordCard.word_translation,
    }]);
    toast.success(`${t.words.moveToDeck}: ${deckName}`);
  };

  const handleAnswer = async (quality: AnswerQuality) => {
    if (!currentCard || isAnswering) return;
    setIsAnswering(true);

    const timeSpent = (Date.now() - cardStartTime.current) / 1000;

    try {
      await trainingService.submitAnswer({
        session_id: sessionId,
        card_id: currentCard.id,
        answer: quality,
        time_spent: timeSpent,
      });

      setSessionStats((prev) => ({
        ...prev,
        answered: prev.answered + 1,
        correct: quality >= 2 ? prev.correct + 1 : prev.correct,
      }));

      // Move to next card
      const nextIndex = currentIndex + 1;
      if (nextIndex >= cards.length) {
        setIsFinished(true);
      } else {
        setCurrentIndex(nextIndex);
        setIsFlipped(false);
        cardStartTime.current = Date.now();
      }
    } catch (error) {
      toast.error(t.trainingSession.errors.submitAnswer);
      logger.error(error);
    } finally {
      setIsAnswering(false);
    }
  };

  const handleTimeUp = () => {
    toast.info(t.trainingSession.errors.timeUp);
    setIsFinished(true);
  };

  const handleFinish = () => {
    navigate('/training');
  };

  const handleExit = () => {
    setShowExitDialog(true);
  };

  const confirmExit = () => {
    setShowExitDialog(false);
    navigate('/training');
  };

  const cancelExit = () => {
    setShowExitDialog(false);
  };

  // No session data
  if (!state?.session) {
    return null;
  }

  // Finished screen
  if (isFinished) {
    const successRate =
      sessionStats.answered > 0
        ? Math.round((sessionStats.correct / sessionStats.answered) * 100)
        : 0;

    return (
      <div className="container mx-auto max-w-lg px-4 py-8">
        <div className="flex flex-col items-center text-center">
          <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 shadow-lg">
            <Trophy className="h-10 w-10 text-white" />
          </div>
          <h1 className="mb-2 text-2xl font-bold">{t.trainingSession.finished.title}</h1>
          <p className="mb-8 text-muted-foreground">
            {t.trainingSession.finished.description}
          </p>

          <div className="mb-8 grid w-full grid-cols-3 gap-4">
            <div className="rounded-xl border bg-card p-4">
              <span className="text-2xl font-bold">{sessionStats.answered}</span>
              <p className="text-xs text-muted-foreground">{t.trainingSession.finished.stats.cards}</p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <span className="text-2xl font-bold text-green-500">
                {sessionStats.correct}
              </span>
              <p className="text-xs text-muted-foreground">{t.trainingSession.finished.stats.correct}</p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <span className="text-2xl font-bold text-blue-500">
                {successRate}%
              </span>
              <p className="text-xs text-muted-foreground">{t.trainingSession.finished.stats.successRate}</p>
            </div>
          </div>

          <div className="flex w-full gap-3">
            <Button
              variant="outline"
              className="flex-1"
              onClick={handleFinish}
            >
              <ArrowRight className="mr-2 h-4 w-4" />
              {t.trainingSession.finished.buttons.done}
            </Button>
            <Button
              className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-700 text-white hover:from-indigo-700 hover:to-purple-800"
              onClick={() => {
                navigate('/training');
              }}
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              {t.trainingSession.finished.buttons.again}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Current word audio available?
  const hasWordAudio = !!(currentCard && getAudioUrl(currentCard.audio_file));
  const currentDetail = currentCard ? wordDetailCache[currentCard.id] : null;

  // Training session
  return (
    <div
      className="mx-auto flex w-full max-w-lg flex-col overflow-hidden px-3 sm:px-4"
      style={{
        height: '100svh',
        minHeight: '100svh',
        maxHeight: '100svh',
        overscrollBehavior: 'none',
        paddingTop: 'calc(env(safe-area-inset-top, 0px) + 0.25rem)',
        paddingBottom: 'calc(env(safe-area-inset-bottom, 0px) + 0.25rem)',
      }}
    >
      {/* Card */}
      {currentCard && (
        <div className="mb-1 min-h-0 flex-1">
          <div className="h-full">
            <TrainingCard
              card={currentCard}
              isFlipped={isFlipped}
              onFlip={handleFlip}
              wordDetail={currentDetail ?? null}
              menuElement={
                <TrainingCardMenu
                  card={currentCard}
                  wordDetail={currentDetail ?? null}
                  availableDecks={availableDecks}
                  onDeleteWord={handleDeleteWord}
                  onMoveToDeck={handleMoveToDeck}
                  onUpdateWordDetail={updateWordDetail}
                  onUpdateCardMedia={updateCardMedia}
                />
              }
            />
          </div>
        </div>
      )}

      {/* Service zone — thin strip below the card */}
      <div className="mb-1 flex shrink-0 items-center justify-between rounded-xl border bg-card/50 px-2.5 py-1.5 sm:px-3 sm:py-2">
        {/* Left: counter + leave */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-muted-foreground">
            {sessionStats.answered + 1}/{cards.length}
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleExit();
            }}
            className="flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            <DoorOpen className="h-3.5 w-3.5" />
            {t.trainingSession.exitDialog.finish}
          </button>
        </div>

        {/* Center: timer */}
        <SessionTimer
          durationMinutes={durationMinutes}
          sessionStartedAt={sessionStartedAt}
          onTimeUp={handleTimeUp}
          active={!isFinished}
        />

        {/* Right: context-dependent buttons */}
        <div className="flex items-center gap-2">
          {!isFlipped ? (
            /* FRONT: Hint button */
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleHintPress();
              }}
              disabled={isGeneratingHint}
              className="flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:hover:bg-amber-900/50 transition-colors disabled:opacity-50"
            >
              {isGeneratingHint ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Lightbulb className="h-3.5 w-3.5" />
              )}
              {isGeneratingHint
                ? t.training.serviceZone.generating
                : t.training.serviceZone.hint}
            </button>
          ) : (
            /* BACK: Listen + Study buttons */
            <>
              {hasWordAudio && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleListen();
                  }}
                  className="flex items-center gap-1.5 rounded-full bg-indigo-100 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 transition-colors"
                >
                  <Volume2 className="h-3.5 w-3.5" />
                  {t.training.card.listen}
                </button>
              )}
              {currentCard?.is_in_learning_mode && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    const trainingState = buildTrainingReturnState();
                    navigate(`/words/${currentCard.word_id}`, {
                      state: trainingState
                        ? {
                            fromTraining: true,
                            trainingState,
                          }
                        : { fromTraining: true },
                    });
                  }}
                  className="flex items-center gap-1.5 rounded-full bg-orange-100 px-3 py-1.5 text-xs font-medium text-orange-700 hover:bg-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:hover:bg-orange-900/50 transition-colors"
                >
                  <BookOpen className="h-3.5 w-3.5" />
                  {t.training.card.learningMode}
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Answer buttons zone: always reserved to keep card size stable */}
      <div
        className="shrink-0"
        style={{ minHeight: 68 }}
        aria-hidden={!isFlipped}
      >
        <div
          className={isFlipped ? 'opacity-100' : 'opacity-0 pointer-events-none'}
        >
          <AnswerButtons
            onAnswer={handleAnswer}
            disabled={!isFlipped || isAnswering}
          />
        </div>
      </div>

      {/* Exit dialog */}
      <AlertDialog open={showExitDialog} onOpenChange={(open: boolean) => { if (!open) cancelExit(); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.trainingSession.exitDialog.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {t.trainingSession.exitDialog.descriptionTemplate
                .replace('{answered}', String(sessionStats.answered))
                .replace('{total}', String(cards.length))}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.trainingSession.exitDialog.continue}</AlertDialogCancel>
            <AlertDialogAction onClick={confirmExit}>
              {t.trainingSession.exitDialog.finish}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
