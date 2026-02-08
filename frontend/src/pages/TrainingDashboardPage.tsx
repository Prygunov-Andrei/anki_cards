import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainingService } from '../services/training.service';
import type { TrainingDashboard, TrainingDeckInfo, TrainingCategoryInfo, TrainingCardCounts } from '../types';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import {
  GraduationCap,
  Play,
  Flame,
  TrendingUp,
  Clock,
  Layers,
  FolderTree,
  FileQuestion,
  ChevronRight,
} from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage } from '../contexts/LanguageContext';

function CardCountsBadges({ cards, t }: { cards: TrainingCardCounts; t: Record<string, unknown> }) {
  const td = t as { cardStatus: { new: string; learning: string; review: string; mastered: string } };
  return (
    <div className="flex flex-wrap gap-1.5">
      {cards.new > 0 && (
        <Badge variant="outline" className="gap-1 border-blue-200 bg-blue-50/50 px-1.5 py-0 text-[10px] text-blue-600 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-400">
          {td.cardStatus.new}: {cards.new}
        </Badge>
      )}
      {cards.learning > 0 && (
        <Badge variant="outline" className="gap-1 border-orange-200 bg-orange-50/50 px-1.5 py-0 text-[10px] text-orange-600 dark:border-orange-800 dark:bg-orange-950/30 dark:text-orange-400">
          {td.cardStatus.learning}: {cards.learning}
        </Badge>
      )}
      {cards.review > 0 && (
        <Badge variant="outline" className="gap-1 border-green-200 bg-green-50/50 px-1.5 py-0 text-[10px] text-green-600 dark:border-green-800 dark:bg-green-950/30 dark:text-green-400">
          {td.cardStatus.review}: {cards.review}
        </Badge>
      )}
      {cards.mastered > 0 && (
        <Badge variant="outline" className="gap-1 border-purple-200 bg-purple-50/50 px-1.5 py-0 text-[10px] text-purple-600 dark:border-purple-800 dark:bg-purple-950/30 dark:text-purple-400">
          {td.cardStatus.mastered}: {cards.mastered}
        </Badge>
      )}
    </div>
  );
}

export default function TrainingDashboardPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const td = t.trainingDashboard;
  const [dashboard, setDashboard] = useState<TrainingDashboard | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [togglingIds, setTogglingIds] = useState<Set<string>>(new Set());

  const loadDashboard = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await trainingService.getDashboard();
      setDashboard(data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const toggleDeck = async (deck: TrainingDeckInfo) => {
    const key = `deck-${deck.id}`;
    if (togglingIds.has(key)) return;
    setTogglingIds((prev) => new Set(prev).add(key));
    try {
      if (deck.is_learning_active) {
        await trainingService.deactivateDeck(deck.id);
      } else {
        await trainingService.activateDeck(deck.id);
      }
      setDashboard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          decks: prev.decks.map((d) =>
            d.id === deck.id ? { ...d, is_learning_active: !d.is_learning_active } : d
          ),
        };
      });
    } catch {
      toast.error('Error toggling deck');
    } finally {
      setTogglingIds((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  const toggleCategory = async (cat: TrainingCategoryInfo) => {
    const key = `cat-${cat.id}`;
    if (togglingIds.has(key)) return;
    setTogglingIds((prev) => new Set(prev).add(key));
    try {
      if (cat.is_learning_active) {
        await trainingService.deactivateCategory(cat.id);
      } else {
        await trainingService.activateCategory(cat.id);
      }
      setDashboard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          categories: prev.categories.map((c) =>
            c.id === cat.id ? { ...c, is_learning_active: !c.is_learning_active } : c
          ),
        };
      });
    } catch {
      toast.error('Error toggling category');
    } finally {
      setTogglingIds((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  const toggleOrphans = async () => {
    if (!dashboard) return;
    const key = 'orphans';
    if (togglingIds.has(key)) return;
    setTogglingIds((prev) => new Set(prev).add(key));
    try {
      await trainingService.setIncludeOrphanWords(!dashboard.orphans.is_active);
      setDashboard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          orphans: { ...prev.orphans, is_active: !prev.orphans.is_active },
        };
      });
    } catch {
      toast.error('Error toggling orphan words');
    } finally {
      setTogglingIds((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  return (
    <div className="container mx-auto max-w-2xl px-4 py-6 pb-20">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
          <GraduationCap className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold">{td.title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{td.subtitle}</p>
      </div>

      {/* Quick Stats */}
      {isLoading ? (
        <div className="mb-6 grid grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      ) : dashboard ? (
        <div className="mb-6 grid grid-cols-3 gap-3">
          <div className="flex flex-col items-center rounded-xl border bg-card p-4">
            <Flame className="mb-1 h-5 w-5 text-orange-500" />
            <span className="text-lg font-bold">{dashboard.quick_stats.streak_days}</span>
            <span className="text-xs text-muted-foreground">{td.stats.streakDays}</span>
          </div>
          <div className="flex flex-col items-center rounded-xl border bg-card p-4">
            <TrendingUp className="mb-1 h-5 w-5 text-green-500" />
            <span className="text-lg font-bold">
              {Math.round(dashboard.quick_stats.success_rate * 100)}%
            </span>
            <span className="text-xs text-muted-foreground">{td.stats.successRate}</span>
          </div>
          <div className="flex flex-col items-center rounded-xl border bg-card p-4">
            <Clock className="mb-1 h-5 w-5 text-blue-500" />
            <span className="text-lg font-bold">{dashboard.quick_stats.total_due}</span>
            <span className="text-xs text-muted-foreground">{td.stats.totalDue}</span>
          </div>
        </div>
      ) : null}

      {/* General Training Button */}
      <Button
        onClick={() => navigate('/training/start')}
        size="lg"
        className="mb-8 w-full rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 py-6 text-lg font-semibold shadow-lg transition-all hover:from-indigo-600 hover:to-purple-700 active:scale-[0.98]"
      >
        <Play className="mr-2 h-5 w-5" />
        {td.generalTraining}
      </Button>

      {/* Decks Section */}
      <div className="mb-6">
        <div className="mb-3 flex items-center gap-2">
          <Layers className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            {td.decksSection}
          </h2>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-xl" />
            ))}
          </div>
        ) : dashboard && dashboard.decks.length > 0 ? (
          <div className="space-y-2">
            {dashboard.decks.map((deck) => (
              <div
                key={deck.id}
                className="flex items-center gap-3 rounded-xl border bg-card p-3 transition-colors hover:bg-accent/30"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium">{deck.name}</span>
                    {deck.cards.due > 0 && (
                      <Badge variant="secondary" className="shrink-0 text-[10px]">
                        {deck.cards.due} {td.due}
                      </Badge>
                    )}
                  </div>
                  <div className="mt-1">
                    <CardCountsBadges cards={deck.cards} t={td} />
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Switch
                    checked={deck.is_learning_active}
                    onCheckedChange={() => toggleDeck(deck)}
                    disabled={togglingIds.has(`deck-${deck.id}`)}
                    title={deck.is_learning_active ? td.deactivateTooltip : td.activateTooltip}
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => navigate(`/training/start?deck_id=${deck.id}`)}
                    title={td.train}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="rounded-xl border bg-card p-4 text-center text-sm text-muted-foreground">
            {td.noDecks}
          </p>
        )}
      </div>

      {/* Categories Section */}
      <div className="mb-6">
        <div className="mb-3 flex items-center gap-2">
          <FolderTree className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            {td.categoriesSection}
          </h2>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-16 rounded-xl" />
          </div>
        ) : dashboard && dashboard.categories.length > 0 ? (
          <div className="space-y-2">
            {dashboard.categories.map((cat) => (
              <div
                key={cat.id}
                className="flex items-center gap-3 rounded-xl border bg-card p-3 transition-colors hover:bg-accent/30"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{cat.icon || '📂'}</span>
                    <span className="truncate font-medium">{cat.name}</span>
                    {cat.cards.due > 0 && (
                      <Badge variant="secondary" className="shrink-0 text-[10px]">
                        {cat.cards.due} {td.due}
                      </Badge>
                    )}
                  </div>
                  <div className="mt-1 pl-6">
                    <CardCountsBadges cards={cat.cards} t={td} />
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Switch
                    checked={cat.is_learning_active}
                    onCheckedChange={() => toggleCategory(cat)}
                    disabled={togglingIds.has(`cat-${cat.id}`)}
                    title={cat.is_learning_active ? td.deactivateTooltip : td.activateTooltip}
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => navigate(`/training/start?category_id=${cat.id}`)}
                    title={td.train}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="rounded-xl border bg-card p-4 text-center text-sm text-muted-foreground">
            {td.noCategories}
          </p>
        )}
      </div>

      {/* Orphans Section */}
      {dashboard && dashboard.orphans.cards.total > 0 && (
        <div className="mb-6">
          <div className="mb-3 flex items-center gap-2">
            <FileQuestion className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              {td.orphansSection}
            </h2>
          </div>

          <div className="flex items-center gap-3 rounded-xl border bg-card p-3">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium">
                  {dashboard.orphans.cards.total} {td.orphanWords}
                </span>
                {dashboard.orphans.cards.due > 0 && (
                  <Badge variant="secondary" className="shrink-0 text-[10px]">
                    {dashboard.orphans.cards.due} {td.due}
                  </Badge>
                )}
              </div>
              <div className="mt-1">
                <CardCountsBadges cards={dashboard.orphans.cards} t={td} />
              </div>
            </div>
            <Switch
              checked={dashboard.orphans.is_active}
              onCheckedChange={toggleOrphans}
              disabled={togglingIds.has('orphans')}
              title={dashboard.orphans.is_active ? td.deactivateTooltip : td.activateTooltip}
            />
          </div>
        </div>
      )}
    </div>
  );
}
