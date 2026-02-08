import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { trainingService } from '../services/training.service';
import { wordsService } from '../services/words.service';
import type {
  CardListItem,
  TrainingSessionResponse,
  AnswerQuality,
} from '../types';
import { TrainingCard, type WordDetail } from '../components/training/TrainingCard';
import { TrainingCardMenu } from '../components/training/TrainingCardMenu';
import { AudioRecorder } from '../components/training/AudioRecorder';
import { ImageUploadDialog } from '../components/training/ImageUploadDialog';
import { getAudioUrl } from '../utils/url-helpers';
import { AnswerButtons } from '../components/training/AnswerButtons';
import { SessionProgress } from '../components/training/SessionProgress';
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
import { X, Trophy, ArrowRight, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage } from '../contexts/LanguageContext';

interface LocationState {
  session: TrainingSessionResponse;
  durationMinutes: number;
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
  const [showAudioRecorder, setShowAudioRecorder] = useState(false);
  const [showImageUpload, setShowImageUpload] = useState(false);

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

  // Word detail cache
  const [wordDetailCache, setWordDetailCache] = useState<Record<number, WordDetail>>({});

  // Card start time for time_spent
  const cardStartTime = useRef<number>(Date.now());

  // Initialize from navigation state
  useEffect(() => {
    if (!state?.session) {
      navigate('/training', { replace: true });
      return;
    }
    setSessionId(state.session.session_id);
    setCards(state.session.cards);
    setDurationMinutes(state.durationMinutes);
    setSessionStats((prev) => ({
      ...prev,
      newCount: state.session.new_count,
      reviewCount: state.session.review_count,
      learningCount: state.session.learning_count,
    }));
  }, []);

  // Preload word details for current + next card
  const currentCard = cards[currentIndex];

  const loadWordDetail = useCallback(
    async (card: CardListItem) => {
      if (wordDetailCache[card.id]) return;
      try {
        const word = await wordsService.getWord(card.word_id);
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
    [wordDetailCache]
  );

  // Preload word details for current card (and next card for smoother UX)
  useEffect(() => {
    if (!currentCard) return;
    loadWordDetail(currentCard);
    // Preload next card
    const nextCard = cards[currentIndex + 1];
    if (nextCard) {
      loadWordDetail(nextCard);
    }
  }, [currentIndex, cards]);

  // Update card media (image/audio) in the cards array — used by TrainingCardMenu
  const updateCardMedia = useCallback((cardId: number, updates: { image_file?: string; audio_file?: string }) => {
    setCards((prev) =>
      prev.map((c) => (c.id === cardId ? { ...c, ...updates } : c))
    );
  }, []);

  // Update word detail cache — used by TrainingCardMenu after generation
  const updateWordDetail = useCallback((cardId: number, updates: Partial<WordDetail>) => {
    setWordDetailCache((prev) => ({
      ...prev,
      [cardId]: { ...prev[cardId], ...updates },
    }));
  }, []);

  // Auto-play audio on flip
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleFlip = () => {
    if (!isFlipped && currentCard) {
      setIsFlipped(true);
      // Auto-play word audio on flip
      const audioUrl = getAudioUrl(currentCard.audio_file);
      if (audioUrl) {
        try {
          if (audioRef.current) {
            audioRef.current.pause();
          }
          audioRef.current = new Audio(audioUrl);
          audioRef.current.play().catch(() => { /* autoplay blocked */ });
        } catch {
          // Silent fail
        }
      }
    }
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
      console.error(error);
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
              className="flex-1 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
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

  // Training session
  return (
    <div className="container mx-auto max-w-lg px-4 py-4">
      {/* Top bar */}
      <div className="mb-4 flex items-center justify-between">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleExit}
          className="rounded-full"
        >
          <X className="h-5 w-5" />
        </Button>
        <SessionTimer
          durationMinutes={durationMinutes}
          onTimeUp={handleTimeUp}
          active={!isFinished}
        />
      </div>

      {/* Progress */}
      <div className="mb-6">
        <SessionProgress
          current={sessionStats.answered}
          total={cards.length}
          newCount={sessionStats.newCount}
          reviewCount={sessionStats.reviewCount}
          learningCount={sessionStats.learningCount}
        />
      </div>

      {/* Card */}
      {currentCard && (
        <div className="mb-6">
          <TrainingCard
            card={currentCard}
            isFlipped={isFlipped}
            onFlip={handleFlip}
            wordDetail={wordDetailCache[currentCard.id] ?? null}
            menuElement={
              <TrainingCardMenu
                card={currentCard}
                wordDetail={wordDetailCache[currentCard.id] ?? null}
                onUpdateWordDetail={updateWordDetail}
                onUpdateCardMedia={updateCardMedia}
                onStartRecording={() => setShowAudioRecorder(true)}
                onStartImageUpload={() => setShowImageUpload(true)}
              />
            }
          />
        </div>
      )}

      {/* Answer buttons (visible only when flipped) */}
      {isFlipped && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
          <AnswerButtons
            onAnswer={handleAnswer}
            disabled={isAnswering}
          />
        </div>
      )}

      {/* Audio recorder modal */}
      {showAudioRecorder && currentCard && (
        <AudioRecorder
          wordId={currentCard.word_id}
          onRecorded={(audioUrl) => {
            updateCardMedia(currentCard.id, { audio_file: audioUrl });
          }}
          onClose={() => setShowAudioRecorder(false)}
        />
      )}

      {/* Image upload modal */}
      {showImageUpload && currentCard && (
        <ImageUploadDialog
          wordId={currentCard.word_id}
          onUploaded={(imageUrl) => {
            updateCardMedia(currentCard.id, { image_file: imageUrl });
            updateWordDetail(currentCard.id, { image_file: imageUrl, image_url: imageUrl });
          }}
          onClose={() => setShowImageUpload(false)}
        />
      )}

      {/* Exit dialog */}
      <AlertDialog open={showExitDialog} onOpenChange={setShowExitDialog}>
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
