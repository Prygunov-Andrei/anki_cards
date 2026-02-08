import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { categoriesService } from '../services/categories.service';
import type {
  CategoryTree as CategoryTreeType,
  Category,
  Word,
} from '../types';
import { CategoryTree } from '../components/categories/CategoryTree';
import { CategoryFormModal } from '../components/categories/CategoryFormModal';
import { NetworkErrorBanner } from '../components/NetworkErrorBanner';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
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
import { FolderTree, Plus, FolderOpen, BookOpen } from 'lucide-react';
import { toast } from 'sonner';

export default function CategoriesPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [tree, setTree] = useState<CategoryTreeType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // Selected category
  const [selectedCategory, setSelectedCategory] =
    useState<CategoryTreeType | null>(null);
  const [categoryWords, setCategoryWords] = useState<Word[]>([]);
  const [wordsLoading, setWordsLoading] = useState(false);

  // Modal states
  const [formOpen, setFormOpen] = useState(false);
  const [editCategory, setEditCategory] = useState<Category | null>(null);
  const [defaultParentId, setDefaultParentId] = useState<number | null>(null);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<CategoryTreeType | null>(
    null
  );

  const loadTree = useCallback(async () => {
    try {
      setIsLoading(true);
      setHasError(false);
      const data = await categoriesService.getTree();
      setTree(data);
    } catch (error) {
      console.error('Error loading categories:', error);
      setHasError(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function initialLoad() {
      try {
        setIsLoading(true);
        setHasError(false);
        const data = await categoriesService.getTree();
        if (!cancelled) setTree(data);
      } catch (error) {
        console.error('Error loading categories:', error);
        if (!cancelled) setHasError(true);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    initialLoad();
    return () => { cancelled = true; };
  }, []);

  // Load words when a category is selected
  useEffect(() => {
    if (!selectedCategory) {
      setCategoryWords([]);
      return;
    }
    let cancelled = false;
    const loadWords = async () => {
      setWordsLoading(true);
      try {
        const res = await categoriesService.getWords(selectedCategory.id);
        if (!cancelled) setCategoryWords(res.words);
      } catch {
        if (!cancelled) setCategoryWords([]);
      } finally {
        if (!cancelled) setWordsLoading(false);
      }
    };
    loadWords();
    return () => {
      cancelled = true;
    };
  }, [selectedCategory]);

  // CRUD handlers
  const handleCreate = () => {
    setEditCategory(null);
    setDefaultParentId(null);
    setFormOpen(true);
  };

  const handleAddChild = (parent: CategoryTreeType) => {
    setEditCategory(null);
    setDefaultParentId(parent.id);
    setFormOpen(true);
  };

  const handleEdit = (cat: CategoryTreeType) => {
    setEditCategory(cat as Category);
    setDefaultParentId(null);
    setFormOpen(true);
  };

  const handleDelete = (cat: CategoryTreeType) => {
    setDeleteTarget(cat);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await categoriesService.delete(deleteTarget.id);
      toast.success(t.categories.success.deleted.replace('{name}', deleteTarget.name));
      if (selectedCategory?.id === deleteTarget.id) {
        setSelectedCategory(null);
      }
      await loadTree();
    } catch (error) {
      toast.error(t.categories.errors.deleteFailed);
      console.error(error);
    } finally {
      setDeleteTarget(null);
    }
  };

  const handleFormSubmit = async (data: {
    name: string;
    parent?: number | null;
    icon?: string;
  }) => {
    if (editCategory) {
      await categoriesService.update(editCategory.id, data);
      toast.success(t.categories.success.updated.replace('{name}', data.name));
    } else {
      await categoriesService.create(data);
      toast.success(t.categories.success.created.replace('{name}', data.name));
    }
    await loadTree();
  };

  const handleSelect = (cat: CategoryTreeType) => {
    setSelectedCategory(
      selectedCategory?.id === cat.id ? null : cat
    );
  };

  /** Count all categories recursively */
  const countAll = (nodes: CategoryTreeType[]): number =>
    nodes.reduce((acc, n) => acc + 1 + countAll(n.children || []), 0);
  const totalCategories = countAll(tree);

  return (
    <div className="container mx-auto max-w-5xl px-4 py-6 pb-20">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderTree className="h-8 w-8 text-primary" />
          <h1 className="text-2xl font-bold">{t.categories.title}</h1>
          {!isLoading && (
            <span className="text-sm text-muted-foreground">
              ({totalCategories})
            </span>
          )}
        </div>
        <Button onClick={handleCreate} size="sm">
          <Plus className="mr-1.5 h-4 w-4" />
          {t.categories.createButton}
        </Button>
      </div>

      {hasError && <NetworkErrorBanner onRetry={loadTree} />}

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : tree.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed p-12 text-center text-muted-foreground">
          <FolderOpen className="h-16 w-16 opacity-30" />
          <div>
            <p className="mb-1 text-lg font-medium">{t.categories.emptyState.noCategories}</p>
            <p className="text-sm">
              {t.categories.emptyState.createFirst}
            </p>
          </div>
          <Button onClick={handleCreate}>
            <Plus className="mr-1.5 h-4 w-4" />
            {t.categories.emptyState.createButton}
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          {/* Left: tree */}
          <div className="lg:col-span-2">
            <div className="rounded-lg border bg-card p-3">
              <CategoryTree
                categories={tree}
                selectedId={selectedCategory?.id}
                onSelect={handleSelect}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onAddChild={handleAddChild}
                onTrain={(cat) => navigate(`/training/start?category_id=${cat.id}`)}
              />
            </div>
          </div>

          {/* Right: selected category info + words */}
          <div className="lg:col-span-3">
            {selectedCategory ? (
              <div className="rounded-lg border bg-card">
                <div className="flex items-center justify-between border-b p-4">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">
                      {selectedCategory.icon || '📁'}
                    </span>
                    <div>
                      <h2 className="text-lg font-semibold">
                        {selectedCategory.name}
                      </h2>
                      <p className="text-xs text-muted-foreground">
                        {selectedCategory.total_words_count || 0} {t.categories.details.wordCount}
                        {selectedCategory.children?.length > 0 &&
                          ` · ${selectedCategory.children.length} ${t.categories.details.subcategories}`}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(selectedCategory)}
                  >
                    {t.categories.details.editButton}
                  </Button>
                </div>

                {/* Words list */}
                <div className="p-4">
                  <h3 className="mb-3 flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
                    <BookOpen className="h-4 w-4" />
                    {t.categories.details.wordsTitle}
                  </h3>
                  {wordsLoading ? (
                    <div className="space-y-2">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <Skeleton key={i} className="h-12 w-full" />
                      ))}
                    </div>
                  ) : categoryWords.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      {t.categories.details.noWords}
                    </p>
                  ) : (
                    <ul className="space-y-1.5">
                      {categoryWords.map((word) => (
                        <li
                          key={word.id}
                          onClick={() => navigate(`/words/${word.id}`)}
                          className="flex cursor-pointer items-center justify-between rounded-md px-3 py-2 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
                        >
                          <div>
                            <span className="font-medium">
                              {word.original_word}
                            </span>
                            <span className="ml-2 text-sm text-muted-foreground">
                              {word.translation}
                            </span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {word.learning_status}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex h-full items-center justify-center rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <p>{t.categories.details.selectCategory}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create/Edit modal */}
      <CategoryFormModal
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={handleFormSubmit}
        editCategory={editCategory}
        defaultParentId={defaultParentId}
        categoriesTree={tree}
      />

      {/* Delete confirmation */}
      <AlertDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.categories.deleteDialog.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {t.categories.deleteDialog.description.replace('{name}', deleteTarget?.name || '')}
              {(deleteTarget?.children?.length ?? 0) > 0 &&
                ` ${t.categories.deleteDialog.subcategoriesWarning}`}
              {' '}{t.categories.deleteDialog.wordsNote}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.categories.deleteDialog.cancel}</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              {t.categories.deleteDialog.delete}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
