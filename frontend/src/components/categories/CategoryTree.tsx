import React, { useState } from 'react';
import type { CategoryTree as CategoryTreeType } from '../../types';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  MoreHorizontal,
  Pencil,
  Trash2,
  Plus,
  GraduationCap,
} from 'lucide-react';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { cn } from '../ui/utils';
import { useLanguage } from '../../contexts/LanguageContext';

interface CategoryTreeProps {
  categories: CategoryTreeType[];
  selectedId?: number | null;
  onSelect?: (category: CategoryTreeType) => void;
  onEdit?: (category: CategoryTreeType) => void;
  onDelete?: (category: CategoryTreeType) => void;
  onAddChild?: (parentCategory: CategoryTreeType) => void;
  onTrain?: (category: CategoryTreeType) => void;
  /** Compact mode for filter sidebar (no action buttons) */
  compact?: boolean;
  /** Depth level (internal) */
  depth?: number;
}

/**
 * Рекурсивный компонент для отображения дерева категорий.
 * Используется на странице CategoriesPage и как фильтр в WordsPage.
 */
export const CategoryTree: React.FC<CategoryTreeProps> = ({
  categories,
  selectedId,
  onSelect,
  onEdit,
  onDelete,
  onAddChild,
  onTrain,
  compact = false,
  depth = 0,
}) => {
  if (!categories.length) return null;

  return (
    <ul className={cn('space-y-0.5', depth === 0 && 'w-full')}>
      {categories.map((cat) => (
        <CategoryNode
          key={cat.id}
          category={cat}
          selectedId={selectedId}
          onSelect={onSelect}
          onEdit={onEdit}
          onDelete={onDelete}
          onAddChild={onAddChild}
          onTrain={onTrain}
          compact={compact}
          depth={depth}
        />
      ))}
    </ul>
  );
};

interface CategoryNodeProps {
  category: CategoryTreeType;
  selectedId?: number | null;
  onSelect?: (category: CategoryTreeType) => void;
  onEdit?: (category: CategoryTreeType) => void;
  onDelete?: (category: CategoryTreeType) => void;
  onAddChild?: (parentCategory: CategoryTreeType) => void;
  onTrain?: (category: CategoryTreeType) => void;
  compact: boolean;
  depth: number;
}

const CategoryNode: React.FC<CategoryNodeProps> = ({
  category,
  selectedId,
  onSelect,
  onEdit,
  onDelete,
  onAddChild,
  onTrain,
  compact,
  depth,
}) => {
  const { t } = useLanguage();
  const [isOpen, setIsOpen] = useState(depth < 1);
  const hasChildren = category.children && category.children.length > 0;
  const isSelected = selectedId === category.id;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  const handleSelect = () => {
    onSelect?.(category);
  };

  return (
    <li>
      <div
        className={cn(
          'group flex items-center rounded-md px-2 py-1.5 transition-colors cursor-pointer',
          isSelected
            ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400'
            : 'hover:bg-gray-50 dark:hover:bg-gray-800/50',
          depth > 0 && 'ml-4'
        )}
        onClick={handleSelect}
      >
        {/* Expand/collapse toggle */}
        <button
          onClick={handleToggle}
          className={cn(
            'mr-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded transition-colors',
            hasChildren
              ? 'hover:bg-gray-200 dark:hover:bg-gray-700'
              : 'invisible'
          )}
        >
          {hasChildren &&
            (isOpen ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            ))}
        </button>

        {/* Icon */}
        <span className="mr-2 flex-shrink-0 text-base">
          {category.icon ? (
            category.icon
          ) : isOpen && hasChildren ? (
            <FolderOpen className="h-4 w-4 text-amber-500" />
          ) : (
            <Folder className="h-4 w-4 text-amber-500" />
          )}
        </span>

        {/* Name + count */}
        <span className="flex-1 truncate text-sm font-medium">
          {category.name}
        </span>
        <span className="ml-2 flex-shrink-0 text-xs text-muted-foreground">
          {category.total_words_count || category.words_count || 0}
        </span>

        {/* Actions (only in full mode) */}
        {!compact && (onEdit || onDelete || onAddChild || onTrain) && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="ml-1 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreHorizontal className="h-3.5 w-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              {onTrain && (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    onTrain(category);
                  }}
                >
                  <GraduationCap className="mr-2 h-4 w-4" />
                  {t.trainingDashboard.train}
                </DropdownMenuItem>
              )}
              {onAddChild && (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    onAddChild(category);
                  }}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  {t.categories.tree.addSubcategory}
                </DropdownMenuItem>
              )}
              {onEdit && (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(category);
                  }}
                >
                  <Pencil className="mr-2 h-4 w-4" />
                  {t.categories.tree.edit}
                </DropdownMenuItem>
              )}
              {onDelete && (
                <DropdownMenuItem
                  className="text-red-600 focus:text-red-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(category);
                  }}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  {t.categories.tree.delete}
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Children (recursive) */}
      {hasChildren && isOpen && (
        <CategoryTree
          categories={category.children}
          selectedId={selectedId}
          onSelect={onSelect}
          onEdit={onEdit}
          onDelete={onDelete}
          onAddChild={onAddChild}
          onTrain={onTrain}
          compact={compact}
          depth={depth + 1}
        />
      )}
    </li>
  );
};
