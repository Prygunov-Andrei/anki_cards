import React, { useState, useEffect } from 'react';
import { Plus, X, Loader2, FolderTree } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { CategoryTree } from '../categories/CategoryTree';
import { categoriesService } from '../../services/categories.service';
import type { CategoryTree as CategoryTreeType } from '../../types';
import { toast } from 'sonner@2.0.3';
import { logger } from '../../utils/logger';

interface CategoryItem {
  id: number;
  name: string;
  icon: string;
}

interface WordCategoryManagerProps {
  wordId: number;
  currentCategories: CategoryItem[];
  onCategoriesChange: (categories: CategoryItem[]) => void;
}

/**
 * Компонент для управления категориями слова.
 * Показывает текущие категории как removable-бейджи
 * и кнопку "+" для добавления через Popover с деревом категорий.
 */
export const WordCategoryManager: React.FC<WordCategoryManagerProps> = ({
  wordId,
  currentCategories,
  onCategoriesChange,
}) => {
  const [categoryTree, setCategoryTree] = useState<CategoryTreeType[]>([]);
  const [isTreeLoading, setIsTreeLoading] = useState(false);
  const [operationLoading, setOperationLoading] = useState<number | null>(null);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  // Загрузка дерева категорий при открытии Popover
  useEffect(() => {
    if (isPopoverOpen && categoryTree.length === 0) {
      loadCategoryTree();
    }
  }, [isPopoverOpen]);

  const loadCategoryTree = async () => {
    setIsTreeLoading(true);
    try {
      const tree = await categoriesService.getTree();
      setCategoryTree(tree);
    } catch (error) {
      logger.error('Failed to load category tree:', error);
      toast.error('Ошибка загрузки категорий');
    } finally {
      setIsTreeLoading(false);
    }
  };

  const handleAddCategory = async (category: CategoryTreeType) => {
    // Проверяем, не добавлена ли уже
    if (currentCategories.some((c) => c.id === category.id)) {
      // Если уже есть — удаляем (toggle)
      await handleRemoveCategory(category.id);
      return;
    }

    setOperationLoading(category.id);
    try {
      await categoriesService.addWordToCategory(wordId, category.id);
      const newCategories = [
        ...currentCategories,
        { id: category.id, name: category.name, icon: category.icon },
      ];
      onCategoriesChange(newCategories);
      toast.success(`Добавлено в "${category.name}"`);
    } catch (error) {
      logger.error('Failed to add category:', error);
      toast.error('Ошибка добавления категории');
    } finally {
      setOperationLoading(null);
    }
  };

  const handleRemoveCategory = async (categoryId: number) => {
    setOperationLoading(categoryId);
    try {
      await categoriesService.removeWordFromCategory(wordId, categoryId);
      const newCategories = currentCategories.filter((c) => c.id !== categoryId);
      onCategoriesChange(newCategories);
      toast.success('Категория убрана');
    } catch (error) {
      logger.error('Failed to remove category:', error);
      toast.error('Ошибка удаления категории');
    } finally {
      setOperationLoading(null);
    }
  };

  // Проверяет, выбрана ли категория (для выделения в дереве)
  const isCategorySelected = (catId: number): boolean => {
    return currentCategories.some((c) => c.id === catId);
  };

  return (
    <div>
      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Категории
      </label>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        {/* Текущие категории */}
        {currentCategories.map((cat) => (
          <Badge
            key={cat.id}
            variant="outline"
            className="flex items-center gap-1.5 px-2.5 py-1 text-sm bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-950/30 dark:border-blue-800 dark:text-blue-400"
          >
            <span className="text-xs">{cat.icon || '📂'}</span>
            <span>{cat.name}</span>
            <button
              onClick={() => handleRemoveCategory(cat.id)}
              disabled={operationLoading === cat.id}
              className="ml-0.5 rounded-full p-0.5 hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors disabled:opacity-50"
            >
              {operationLoading === cat.id ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <X className="h-3 w-3" />
              )}
            </button>
          </Badge>
        ))}

        {/* Кнопка добавления */}
        <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1 border-dashed text-xs text-muted-foreground hover:text-foreground"
            >
              <Plus className="h-3.5 w-3.5" />
              Добавить
            </Button>
          </PopoverTrigger>
          <PopoverContent
            className="w-72 p-0"
            align="start"
            side="bottom"
          >
            <div className="border-b px-3 py-2">
              <p className="text-sm font-medium">Выберите категорию</p>
            </div>
            <div className="max-h-64 overflow-y-auto p-2">
              {isTreeLoading ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : categoryTree.length === 0 ? (
                <div className="flex flex-col items-center gap-2 py-6 text-center">
                  <FolderTree className="h-8 w-8 text-muted-foreground/50" />
                  <p className="text-sm text-muted-foreground">
                    Нет категорий
                  </p>
                </div>
              ) : (
                <CategoryTreeWithSelection
                  categories={categoryTree}
                  selectedCategoryIds={currentCategories.map((c) => c.id)}
                  onSelect={handleAddCategory}
                  operationLoading={operationLoading}
                />
              )}
            </div>
          </PopoverContent>
        </Popover>
      </div>

      {/* Подсказка при отсутствии категорий */}
      {currentCategories.length === 0 && (
        <p className="mt-1.5 text-xs text-muted-foreground">
          Слово пока не в категориях
        </p>
      )}
    </div>
  );
};

/**
 * Обёртка над CategoryTree с визуальным выделением уже добавленных категорий.
 * Использует рекурсивный рендеринг с галочками.
 */
interface CategoryTreeWithSelectionProps {
  categories: CategoryTreeType[];
  selectedCategoryIds: number[];
  onSelect: (category: CategoryTreeType) => void;
  operationLoading: number | null;
  depth?: number;
}

const CategoryTreeWithSelection: React.FC<CategoryTreeWithSelectionProps> = ({
  categories,
  selectedCategoryIds,
  onSelect,
  operationLoading,
  depth = 0,
}) => {
  return (
    <ul className="space-y-0.5">
      {categories.map((cat) => (
        <CategorySelectableNode
          key={cat.id}
          category={cat}
          selectedCategoryIds={selectedCategoryIds}
          onSelect={onSelect}
          operationLoading={operationLoading}
          depth={depth}
        />
      ))}
    </ul>
  );
};

interface CategorySelectableNodeProps {
  category: CategoryTreeType;
  selectedCategoryIds: number[];
  onSelect: (category: CategoryTreeType) => void;
  operationLoading: number | null;
  depth: number;
}

const CategorySelectableNode: React.FC<CategorySelectableNodeProps> = ({
  category,
  selectedCategoryIds,
  onSelect,
  operationLoading,
  depth,
}) => {
  const [isOpen, setIsOpen] = useState(depth < 2);
  const hasChildren = category.children && category.children.length > 0;
  const isSelected = selectedCategoryIds.includes(category.id);
  const isLoading = operationLoading === category.id;

  return (
    <li>
      <div
        className={`flex items-center rounded-md px-2 py-1.5 cursor-pointer transition-colors ${
          isSelected
            ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400'
            : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
        } ${depth > 0 ? 'ml-4' : ''}`}
        onClick={() => onSelect(category)}
      >
        {/* Expand/collapse */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen(!isOpen);
            }}
            className="mr-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            {isOpen ? (
              <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m6 9 6 6 6-6"/></svg>
            ) : (
              <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
            )}
          </button>
        ) : (
          <span className="mr-1 w-5 flex-shrink-0" />
        )}

        {/* Checkbox indicator */}
        <span className={`mr-2 flex h-4 w-4 flex-shrink-0 items-center justify-center rounded border transition-colors ${
          isSelected
            ? 'border-blue-500 bg-blue-500 text-white'
            : 'border-gray-300 dark:border-gray-600'
        }`}>
          {isLoading ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : isSelected ? (
            <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M20 6 9 17l-5-5"/></svg>
          ) : null}
        </span>

        {/* Icon */}
        <span className="mr-1.5 flex-shrink-0 text-sm">
          {category.icon || '📂'}
        </span>

        {/* Name */}
        <span className="flex-1 truncate text-sm">
          {category.name}
        </span>
      </div>

      {/* Children */}
      {hasChildren && isOpen && (
        <CategoryTreeWithSelection
          categories={category.children}
          selectedCategoryIds={selectedCategoryIds}
          onSelect={onSelect}
          operationLoading={operationLoading}
          depth={depth + 1}
        />
      )}
    </li>
  );
};
