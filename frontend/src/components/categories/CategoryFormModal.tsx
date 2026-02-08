import React, { useState, useEffect } from 'react';
import type { Category, CategoryTree as CategoryTreeType } from '../../types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { useLanguage } from '../../contexts/LanguageContext';

/** Flatten tree for parent picker */
function flattenTree(
  nodes: CategoryTreeType[],
  depth = 0
): Array<{ id: number; name: string; depth: number }> {
  const result: Array<{ id: number; name: string; depth: number }> = [];
  for (const node of nodes) {
    result.push({ id: node.id, name: node.name, depth });
    if (node.children?.length) {
      result.push(...flattenTree(node.children, depth + 1));
    }
  }
  return result;
}

const EMOJI_ICONS = [
  '📚', '📖', '🏠', '🍎', '🎯', '💼', '🎨', '🔬',
  '⚽', '🎵', '✈️', '🍕', '🐱', '🌍', '💡', '⭐',
  '🔥', '❤️', '🚀', '🎓', '🏥', '💻', '🎭', '🌺',
];

interface CategoryFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: { name: string; parent?: number | null; icon?: string }) => Promise<void>;
  /** If provided, we're editing; else creating */
  editCategory?: Category | null;
  /** Parent pre-selected (when adding subcategory) */
  defaultParentId?: number | null;
  /** Tree for parent picker */
  categoriesTree: CategoryTreeType[];
}

export const CategoryFormModal: React.FC<CategoryFormModalProps> = ({
  open,
  onOpenChange,
  onSubmit,
  editCategory,
  defaultParentId,
  categoriesTree,
}) => {
  const { t } = useLanguage();
  const [name, setName] = useState('');
  const [parentId, setParentId] = useState<string>('none');
  const [icon, setIcon] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditing = !!editCategory;

  useEffect(() => {
    if (open) {
      if (editCategory) {
        setName(editCategory.name);
        setParentId(editCategory.parent ? String(editCategory.parent) : 'none');
        setIcon(editCategory.icon || '');
      } else {
        setName('');
        setParentId(defaultParentId ? String(defaultParentId) : 'none');
        setIcon('');
      }
    }
  }, [open, editCategory, defaultParentId]);

  const flatCategories = flattenTree(categoriesTree).filter(
    (c) => !editCategory || c.id !== editCategory.id
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      await onSubmit({
        name: name.trim(),
        parent: parentId === 'none' ? null : Number(parentId),
        icon: icon || undefined,
      });
      onOpenChange(false);
    } catch (error) {
      console.error('Category form error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? t.categories.form.editTitle : t.categories.form.createTitle}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? t.categories.form.editDescription
              : t.categories.form.createDescription}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="cat-name">{t.categories.form.name}</Label>
            <Input
              id="cat-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t.categories.form.namePlaceholder}
              autoFocus
              required
            />
          </div>

          {/* Parent */}
          <div className="space-y-2">
            <Label>{t.categories.form.parent}</Label>
            <Select value={parentId} onValueChange={setParentId}>
              <SelectTrigger>
                <SelectValue placeholder={t.categories.form.noParent} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">{t.categories.form.noParent}</SelectItem>
                {flatCategories.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {'  '.repeat(c.depth)}
                    {c.depth > 0 ? '└ ' : ''}
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Icon picker */}
          <div className="space-y-2">
            <Label>{t.categories.form.icon}</Label>
            <div className="flex flex-wrap gap-1.5">
              {EMOJI_ICONS.map((emoji) => (
                <button
                  key={emoji}
                  type="button"
                  onClick={() => setIcon(icon === emoji ? '' : emoji)}
                  className={`flex h-8 w-8 items-center justify-center rounded-md text-lg transition-all ${
                    icon === emoji
                      ? 'bg-blue-100 ring-2 ring-blue-500 dark:bg-blue-900/50'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  {emoji}
                </button>
              ))}
            </div>
            {icon && (
              <p className="text-xs text-muted-foreground">
                {t.categories.form.iconSelected} {icon}{' '}
                <button
                  type="button"
                  onClick={() => setIcon('')}
                  className="text-blue-500 underline"
                >
                  {t.categories.form.resetIcon}
                </button>
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              {t.categories.form.cancel}
            </Button>
            <Button type="submit" disabled={!name.trim() || isSubmitting}>
              {isSubmitting
                ? t.categories.form.saving
                : isEditing
                ? t.categories.form.save
                : t.categories.form.create}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
