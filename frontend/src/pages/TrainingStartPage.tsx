import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { trainingService } from '../services/training.service';
import { wordsService } from '../services/words.service';
import type { TrainingStats, WordsStats } from '../types';
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
import { Badge } from '../components/ui/badge';
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
  Layers,
  FolderTree,
} from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage } from '../contexts/LanguageContext';

export default function TrainingStartPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useLanguage();

  // Scope from URL params
  const deckId = searchParams.get('deck_id') ? parseInt(searchParams.get('deck_id')!) : undefined;
  const categoryId = searchParams.get('category_id')
    ? parseInt(searchParams.get('category_id')!)
    : undefined;

  const [stats, setStats] = useState<TrainingStats | null>(null);
  const [wordsStats, setWordsStats] = useState<WordsStats | null>(null);
  const [scopeName, setScopeName] = useState<string>('');
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

  // Determine scope label
  const isScoped = deckId !== undefined || categoryId !== undefined;
  const scopeLabel = deckId
    ? t.trainingDashboard.scope.deck
    : categoryId
      ? t.trainingDashboard.scope.category
      : t.trainingDashboard.scope.general;

  useEffect(() => {
    let cancelled = false;
    async function loadData() {
      try {
        setIsLoading(true);
        const [statsData, wordsData] = await Promise.all([
          trainingService.getStats('day').catch(() => null),
          wordsService.getWordsStats().catch(() => null),
        ]);

        // Load scope name from dashboard if scoped
        if (isScoped) {
          try {
            const dashboard = await trainingService.getDashboard();
            if (deckId) {
              const deck = dashboard.decks.find((d) => d.id === deckId);
              if (deck && !cancelled) setScopeName(deck.name);
            } else if (categoryId) {
              const cat = dashboard.categories.find((c) => c.id === categoryId);
              if (cat && !cancelled) setScopeName(`${cat.icon || '📂'} ${cat.name}`);
            }
          } catch {
            // Scope name is optional
          }
        }

        if (!cancelled) {
          setStats(statsData);
          setWordsStats(wordsData);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    loadData();
    return () => {
      cancelled = true;
    };
  }, [deckId, categoryId, isScoped]);

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
        },
      });
    } catch (error) {
      toast.error(t.trainingStart.errors.startFailed);
      console.error(error);
      setIsStarting(false);
    }
  };

  return (
    <div className="container mx-auto max-w-2xl px-4 py-6 pb-20">
      {/* Back to dashboard */}
      <Button
        variant="ghost"
        size="sm"
        className="mb-4 -ml-2"
        onClick={() => navigate('/training')}
      >
        <ArrowLeft className="mr-1 h-4 w-4" />
        {t.trainingDashboard.title}
      </Button>

      {/* Header */}
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
          <GraduationCap className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold">{t.trainingStart.title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t.trainingStart.subtitle}</p>

        {/* Scope indicator */}
        {isScoped && (
          <div className="mt-3 inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1.5">
            {deckId ? (
              <Layers className="h-3.5 w-3.5 text-indigo-500" />
            ) : (
              <FolderTree className="h-3.5 w-3.5 text-indigo-500" />
            )}
            <span className="text-xs font-medium">{scopeLabel}</span>
            {scopeName && (
              <Badge variant="secondary" className="text-[10px]">
                {scopeName}
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Quick stats */}
      {isLoading ? (
        <div className="mb-6 grid grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="mb-6 grid grid-cols-3 gap-3">
          <div className="flex flex-col items-center rounded-xl border bg-card p-4">
            <Flame className="mb-1 h-5 w-5 text-orange-500" />
            <span className="text-lg font-bold">{stats?.streak_days ?? 0}</span>
            <span className="text-xs text-muted-foreground">
              {t.trainingStart.stats.streakDays}
            </span>
          </div>
          <div className="flex flex-col items-center rounded-xl border bg-card p-4">
            <TrendingUp className="mb-1 h-5 w-5 text-green-500" />
            <span className="text-lg font-bold">
              {stats ? Math.round(stats.success_rate * 100) : 0}%
            </span>
            <span className="text-xs text-muted-foreground">
              {t.trainingStart.stats.successRate}
            </span>
          </div>
          <div className="flex flex-col items-center rounded-xl border bg-card p-4">
            <BookOpen className="mb-1 h-5 w-5 text-blue-500" />
            <span className="text-lg font-bold">{wordsStats?.total_words ?? 0}</span>
            <span className="text-xs text-muted-foreground">
              {t.trainingStart.stats.totalWords}
            </span>
          </div>
        </div>
      )}

      {/* Cards overview */}
      {!isLoading && stats?.cards_by_status && (
        <div className="mb-6 rounded-xl border bg-card p-4">
          <h3 className="mb-3 text-sm font-medium">{t.trainingStart.cardsOverview.title}</h3>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <span className="text-2xl font-bold text-orange-500">
                {stats.cards_by_status.learning}
              </span>
              <p className="text-xs text-muted-foreground">
                {t.trainingStart.cardsOverview.learning}
              </p>
            </div>
            <div>
              <span className="text-2xl font-bold text-green-500">
                {stats.cards_by_status.review}
              </span>
              <p className="text-xs text-muted-foreground">
                {t.trainingStart.cardsOverview.review}
              </p>
            </div>
            <div>
              <span className="text-2xl font-bold text-blue-500">
                {stats.cards_by_status.new}
              </span>
              <p className="text-xs text-muted-foreground">{t.trainingStart.cardsOverview.new}</p>
            </div>
          </div>
        </div>
      )}

      {/* Session settings */}
      <div className="mb-8 space-y-4 rounded-xl border bg-card p-4">
        <h3 className="text-sm font-medium">{t.trainingStart.sessionSettings.title}</h3>

        {/* Duration */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <Label>{t.trainingStart.sessionSettings.duration}</Label>
          </div>
          <Select value={duration} onValueChange={setDuration}>
            <SelectTrigger className="w-[140px]">
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
      <Button
        onClick={handleStart}
        disabled={isStarting || isLoading}
        size="lg"
        className="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 py-6 text-lg font-semibold shadow-lg transition-all hover:from-indigo-600 hover:to-purple-700 active:scale-[0.98]"
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
  );
}
