import React, { useState, useEffect, useCallback } from 'react';
import { wordsService } from '../services/words.service';
import { categoriesService } from '../services/categories.service';
import type {
  WordListItem as WordListItemType,
  WordsListParams,
  WordsStats,
  CategoryTree as CategoryTreeType,
} from '../types';
import { WordListItem } from '../components/words/WordListItem';
import { CategoryTree } from '../components/categories/CategoryTree';
import { NetworkErrorBanner } from '../components/NetworkErrorBanner';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { BookOpen, ChevronLeft, ChevronRight, FolderTree, X } from 'lucide-react';

const PAGE_SIZE = 20;
const ORDERING_VALUES = [
  '-created_at', 'created_at', 'original_word', '-original_word',
  'learning_status', '-next_review', 'next_review',
];

const STATUS_VALUES = ['all', 'new', 'learning', 'reviewing', 'mastered'];

/**
 * Страница каталога слов (Этап 8)
 */
export default function WordsPage() {
  const { t } = useLanguage();

  const orderingLabels: Record<string, string> = {
    '-created_at': t.wordsCatalog.ordering.newestFirst,
    'created_at': t.wordsCatalog.ordering.oldestFirst,
    'original_word': t.wordsCatalog.ordering.wordAsc,
    '-original_word': t.wordsCatalog.ordering.wordDesc,
    'learning_status': t.wordsCatalog.ordering.status,
    '-next_review': t.wordsCatalog.ordering.nextReviewAsc,
    'next_review': t.wordsCatalog.ordering.nextReviewDesc,
  };

  const statusLabels: Record<string, string> = {
    'all': t.wordsCatalog.status.all,
    'new': t.wordsCatalog.status.new,
    'learning': t.wordsCatalog.status.learning,
    'reviewing': t.wordsCatalog.status.reviewing,
    'mastered': t.wordsCatalog.status.mastered,
  };

  const [words, setWords] = useState<WordListItemType[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [nextPage, setNextPage] = useState<string | null>(null);
  const [prevPage, setPrevPage] = useState<string | null>(null);
  const [stats, setStats] = useState<WordsStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasNetworkError, setHasNetworkError] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchDebounced, setSearchDebounced] = useState('');
  const [ordering, setOrdering] = useState('-created_at');
  const [learningStatus, setLearningStatus] = useState('all');
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [categoryName, setCategoryName] = useState<string>('');
  const [categoriesTree, setCategoriesTree] = useState<CategoryTreeType[]>([]);
  const [showCategoryFilter, setShowCategoryFilter] = useState(false);

  const loadList = useCallback(
    async (params?: Partial<WordsListParams>) => {
      try {
        setIsLoading(true);
        setHasNetworkError(false);
        const res = await wordsService.getList({
          page: params?.page ?? page,
          page_size: PAGE_SIZE,
          ordering: params?.ordering ?? ordering,
          learning_status:
            (params?.learning_status ?? learningStatus) === 'all'
              ? undefined
              : (params?.learning_status ?? learningStatus) || undefined,
          search: (params?.search ?? searchDebounced) || undefined,
          category_id: categoryId ?? undefined,
        });
        setWords(res.results);
        setTotalCount(res.count);
        setNextPage(res.next);
        setPrevPage(res.previous);
      } catch (error) {
        console.error('Error loading words:', error);
        setHasNetworkError(true);
        setWords([]);
      } finally {
        setIsLoading(false);
      }
    },
    [page, ordering, learningStatus, searchDebounced, categoryId]
  );

  useEffect(() => {
    let cancelled = false;
    async function doLoadList() {
      try {
        setIsLoading(true);
        setHasNetworkError(false);
        const res = await wordsService.getList({
          page,
          page_size: PAGE_SIZE,
          ordering,
          learning_status:
            learningStatus === 'all' ? undefined : learningStatus || undefined,
          search: searchDebounced || undefined,
          category_id: categoryId ?? undefined,
        });
        if (!cancelled) {
          setWords(res.results);
          setTotalCount(res.count);
          setNextPage(res.next);
          setPrevPage(res.previous);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Error loading words:', error);
          setHasNetworkError(true);
          setWords([]);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    doLoadList();
    return () => { cancelled = true; };
  }, [page, ordering, learningStatus, searchDebounced, categoryId]);

  useEffect(() => {
    let cancelled = false;
    async function doLoadStats() {
      try {
        const data = await wordsService.getWordsStats();
        if (!cancelled) setStats(data);
      } catch {
        if (!cancelled) setStats(null);
      }
    }
    doLoadStats();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function doLoadCategories() {
      try {
        const data = await categoriesService.getTree();
        if (!cancelled) setCategoriesTree(data);
      } catch {
        if (!cancelled) setCategoriesTree([]);
      }
    }
    doLoadCategories();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => setSearchDebounced(search), 400);
    return () => clearTimeout(timer);
  }, [search]);

  const handlePrev = () => {
    if (prevPage && page > 1) {
      setPage((p) => p - 1);
    }
  };

  const handleNext = () => {
    if (nextPage && page * PAGE_SIZE < totalCount) {
      setPage((p) => p + 1);
    }
  };

  return (
    <div className="container mx-auto max-w-4xl px-4 py-6 pb-20">
      <div className="mb-6 flex items-center gap-2">
        <BookOpen className="h-8 w-8 text-primary" />
        <h1 className="text-2xl font-bold">{t.wordsCatalog.title}</h1>
      </div>

      {hasNetworkError && (
        <NetworkErrorBanner onRetry={() => loadList()} />
      )}

      {stats && (
        <div className="mb-4 rounded-lg border bg-card p-4 text-sm text-muted-foreground">
          {t.wordsCatalog.stats.totalWords} <strong className="text-foreground">{stats.total_words}</strong>
          {stats.due_for_review > 0 && (
            <> · {t.wordsCatalog.stats.dueForReview} <strong className="text-foreground">{stats.due_for_review}</strong></>
          )}
        </div>
      )}

      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:flex-wrap">
        <Input
          placeholder={t.wordsCatalog.search.placeholder}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
        <Select value={learningStatus} onValueChange={setLearningStatus}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder={t.wordsCatalog.filters.status} />
          </SelectTrigger>
          <SelectContent>
            {STATUS_VALUES.map((value) => (
              <SelectItem key={value} value={value}>
                {statusLabels[value]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={ordering} onValueChange={setOrdering}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder={t.wordsCatalog.filters.ordering} />
          </SelectTrigger>
          <SelectContent>
            {ORDERING_VALUES.map((value) => (
              <SelectItem key={value} value={value}>
                {orderingLabels[value]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Category filter button */}
        {categoriesTree.length > 0 && (
          <Button
            variant={categoryId ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowCategoryFilter(!showCategoryFilter)}
            className="gap-1.5"
          >
            <FolderTree className="h-4 w-4" />
            {categoryId ? categoryName : t.wordsCatalog.filters.category}
            {categoryId && (
              <X
                className="h-3.5 w-3.5 ml-1"
                onClick={(e) => {
                  e.stopPropagation();
                  setCategoryId(null);
                  setCategoryName('');
                  setShowCategoryFilter(false);
                  setPage(1);
                }}
              />
            )}
          </Button>
        )}
      </div>

      {/* Category tree filter (expandable) */}
      {showCategoryFilter && categoriesTree.length > 0 && (
        <div className="mb-4 rounded-lg border bg-card p-3">
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            {t.wordsCatalog.filters.categoryFilter}
          </p>
          <CategoryTree
            categories={categoriesTree}
            selectedId={categoryId}
            onSelect={(cat) => {
              if (categoryId === cat.id) {
                setCategoryId(null);
                setCategoryName('');
              } else {
                setCategoryId(cat.id);
                setCategoryName(cat.name);
              }
              setPage(1);
              setShowCategoryFilter(false);
            }}
            compact
          />
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : words.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
          {t.wordsCatalog.emptyState.noWords}
        </div>
      ) : (
        <>
          <div className="space-y-2">
            {words.map((w) => (
              <WordListItem key={w.id} word={w} />
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrev}
              disabled={!prevPage}
            >
              <ChevronLeft className="h-4 w-4" />
              {t.wordsCatalog.pagination.back}
            </Button>
            <span className="text-sm text-muted-foreground">
              {((page - 1) * PAGE_SIZE + 1)}–{Math.min(page * PAGE_SIZE, totalCount)} из {totalCount}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleNext}
              disabled={!nextPage}
            >
              {t.wordsCatalog.pagination.next}
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
