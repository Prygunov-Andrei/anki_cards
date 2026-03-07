import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { trainingService } from '../services/training.service';
import { wordsService } from '../services/words.service';
import type { TrainingStats, WordsStats, TrainingCardCounts, TrainingDashboard } from '../types';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import {
  GraduationCap,
  Play,
  Clock,
  BookOpen,
  RotateCcw,
  Sparkles,
  TrendingUp,
  Flame,
  ArrowLeft,
} from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuthContext } from '../contexts/AuthContext';
import { LiterarySourceSelector } from '../components/literary-context/LiterarySourceSelector';

export default function TrainingStartPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useLanguage();
  const { user, updateUser } = useAuthContext();

  // Scope from URL params
  const deckId = searchParams.get('deck_id') ? parseInt(searchParams.get('deck_id')!) : undefined;
  const categoryId = searchParams.get('category_id')
    ? parseInt(searchParams.get('category_id')!)
    : undefined;

  const [stats, setStats] = useState<TrainingStats | null>(null);
  const [wordsStats, setWordsStats] = useState<WordsStats | null>(null);
  const [dashboard, setDashboard] = useState<TrainingDashboard | null>(null);
  const [scopedCards, setScopedCards] = useState<TrainingCardCounts | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);

  // Session options
  const [duration, setDuration] = useState('20');
  const [includeNew, setIncludeNew] = useState(true);

  const DURATION_OPTIONS = [
    { value: '5', label: t.trainingStart.duration['5min'] },
    { value: '10', label: t.trainingStart.duration['10min'] },
    { value: '15', label: t.trainingStart.duration['15min'] },
    { value: '20', label: t.trainingStart.duration['20min'] },
    { value: '30', label: t.trainingStart.duration['30min'] },
    { value: '0', label: t.trainingStart.duration.unlimited },
  ];

  useEffect(() => {
    let cancelled = false;
    async function loadData() {
      try {
        setIsLoading(true);
        const [statsData, wordsData, dashboardData] = await Promise.all([
          trainingService.getStats('day').catch(() => null),
          wordsService.getWordsStats().catch(() => null),
          trainingService.getDashboard().catch(() => null),
        ]);

        if (!cancelled) {
          setStats(statsData);
          setWordsStats(wordsData);
          setDashboard(dashboardData);
        }

        // Load scope name + scoped card counts from dashboard
        try {
          const data = dashboardData;
          if (!data) return;

          if (deckId) {
            const deck = data.decks.find((d) => d.id === deckId);
            if (deck && !cancelled) {
              setScopedCards(deck.cards);
            }
          } else if (categoryId) {
            const cat = data.categories.find((c) => c.id === categoryId);
            if (cat && !cancelled) {
              setScopedCards(cat.cards);
            }
          } else if (!cancelled) {
            setScopedCards(null);
          }
        } catch {
          // Dashboard is optional, fallback to global stats
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    loadData();
    return () => {
      cancelled = true;
    };
  }, [deckId, categoryId]);

  const handleStart = async () => {
    setIsStarting(true);
    try {
      const durationNum = parseInt(duration);
      const session = await trainingService.getSession({
        deck_id: deckId,
        category_id: categoryId,
        duration: durationNum || undefined,
        new_cards: includeNew,
      });

      if (session.total_count === 0) {
        toast.info(t.trainingStart.errors.noCards);
        setIsStarting(false);
        return;
      }

      // Navigate to session with data in state
      navigate('/training/session', {
        state: {
          session,
          durationMinutes: durationNum,
          sessionStartedAt: Date.now(),
        },
      });
    } catch (error) {
      toast.error(t.trainingStart.errors.startFailed);
      console.error(error);
      setIsStarting(false);
    }
  };

  const quickStreak = dashboard?.quick_stats?.streak_days ?? stats?.streak_days ?? 0;
  const quickSuccess = dashboard?.quick_stats?.success_rate ?? stats?.success_rate ?? 0;
  const dueCount = scopedCards?.due ?? dashboard?.quick_stats?.total_due ?? 0;
  const totalCards =
    scopedCards?.total ??
    (stats
      ? (stats.cards_by_status.learning + stats.cards_by_status.review + stats.cards_by_status.new)
      : (wordsStats?.total_words ?? 0));
  const learningCount = scopedCards ? scopedCards.learning : stats?.cards_by_status?.learning ?? 0;
  const reviewCount = scopedCards ? scopedCards.review : stats?.cards_by_status?.review ?? 0;
  const newCount = scopedCards ? scopedCards.new : stats?.cards_by_status?.new ?? 0;

  return (
    <div className="container mx-auto max-w-2xl px-4 py-4 pb-20">
      {/* Back */}
      <Button
        variant="ghost"
        size="icon"
        className="mb-2 -ml-2"
        onClick={() => navigate('/training')}
        aria-label={t.common.back}
      >
        <ArrowLeft className="h-5 w-5" />
      </Button>

      {/* Compact stats */}
      {isLoading ? (
        <div className="mb-4 grid gap-3 md:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="mb-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border bg-card p-3">
            <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
              <div className="flex items-center gap-2">
                <Flame className="h-4 w-4 text-orange-500" />
                <span className="text-sm font-semibold tabular-nums">{quickStreak}</span>
                <span className="text-xs text-muted-foreground">{t.trainingStart.stats.streakDays}</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <span className="text-sm font-semibold tabular-nums">
                  {Math.round(quickSuccess * 100)}%
                </span>
                <span className="text-xs text-muted-foreground">{t.trainingStart.stats.successRate}</span>
              </div>
              <div className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-semibold tabular-nums">{totalCards}</span>
                <span className="text-xs text-muted-foreground">
                  {scopedCards ? t.trainingStart.stats.totalCards : t.trainingStart.stats.totalWords}
                </span>
              </div>
            </div>
          </div>
          <div className="rounded-xl border bg-card p-3">
            <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
              <div className="flex items-center gap-2">
                <GraduationCap className="h-4 w-4 text-orange-500" />
                <span className="text-sm font-semibold tabular-nums text-orange-600 dark:text-orange-400">
                  {learningCount}
                </span>
                <span className="text-xs text-muted-foreground">{t.trainingStart.cardsOverview.learning}</span>
              </div>
              <div className="flex items-center gap-2">
                <RotateCcw className="h-4 w-4 text-green-500" />
                <span className="text-sm font-semibold tabular-nums text-green-600 dark:text-green-400">
                  {reviewCount}
                </span>
                <span className="text-xs text-muted-foreground">{t.trainingStart.cardsOverview.review}</span>
              </div>
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-semibold tabular-nums text-blue-600 dark:text-blue-400">
                  {newCount}
                </span>
                <span className="text-xs text-muted-foreground">{t.trainingStart.cardsOverview.new}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-indigo-500" />
                <span className="text-sm font-semibold tabular-nums text-indigo-600 dark:text-indigo-400">
                  {dueCount}
                </span>
                <span className="text-xs text-muted-foreground">{t.trainingDashboard.due}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Literary context selector */}
      <div className="mb-4 rounded-xl border bg-card p-3">
        <LiterarySourceSelector
          activeSource={user?.active_literary_source ?? null}
          onSourceChange={(slug) => updateUser({ active_literary_source: slug })}
        />
      </div>

      <div className="grid gap-3 md:grid-cols-[1.2fr_1fr]">
        {/* Session settings */}
        <div className="space-y-2 rounded-xl border bg-card p-3">

          {/* Duration */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <Label>{t.trainingStart.sessionSettings.duration}</Label>
            </div>
            <Select value={duration} onValueChange={setDuration}>
              <SelectTrigger className="h-8 w-[132px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DURATION_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Include new */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-muted-foreground" />
              <Label>{t.trainingStart.sessionSettings.includeNew}</Label>
            </div>
            <Switch checked={includeNew} onCheckedChange={setIncludeNew} />
          </div>
        </div>

        {/* Start button */}
        <div className="rounded-xl border bg-card p-3">
          <Button
            onClick={handleStart}
            disabled={isStarting || isLoading}
            size="lg"
            className="w-full rounded-xl py-5 text-base font-bold shadow-lg transition-opacity hover:opacity-95"
            style={{
              background: 'linear-gradient(135deg, #4338ca 0%, #7e22ce 100%)',
              color: '#ffffff',
            }}
          >
            {isStarting ? (
              <>
                <RotateCcw className="mr-2 h-5 w-5 animate-spin" />
                {t.trainingStart.startButton.loading}
              </>
            ) : (
              <>
                <Play className="mr-2 h-5 w-5" />
                {t.trainingStart.startButton.start}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
