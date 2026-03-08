import React, { useState, useRef, useEffect } from 'react';
import { Input } from './ui/input';
import { Edit2 } from 'lucide-react';
import { displayWord } from '../utils/helpers';
import { logger } from '../utils/logger';

interface EditableTextProps {
  value: string;
  onSave: (newValue: string) => Promise<void>;
  placeholder?: string;
  className?: string;
  inputClassName?: string;
  maxLength?: number;
  minLength?: number;
  /** Custom view renderer. Defaults to displayWord(value). */
  renderView?: (value: string) => React.ReactNode;
  /** Icon size class. Defaults to "h-3.5 w-3.5". */
  iconSize?: string;
  /** Icon hover opacity class. Defaults to "group-hover:opacity-60". */
  iconHoverOpacity?: string;
}

/**
 * Unified inline-editable text component.
 * Replaces both EditableText and EditableTitle.
 */
export const EditableText: React.FC<EditableTextProps> = ({
  value,
  onSave,
  placeholder = 'Введите текст',
  className = '',
  inputClassName = '',
  maxLength = 200,
  minLength,
  renderView,
  iconSize = 'h-3.5 w-3.5',
  iconHoverOpacity = 'group-hover:opacity-60',
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [isSaving, setIsSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setEditValue(value);
  }, [value]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = async () => {
    const trimmedValue = editValue.trim();

    if (!trimmedValue || trimmedValue === value) {
      setEditValue(value);
      setIsEditing(false);
      return;
    }

    if (trimmedValue.length > maxLength || (minLength && trimmedValue.length < minLength)) {
      setEditValue(value);
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    try {
      await onSave(trimmedValue);
      setIsEditing(false);
    } catch (error) {
      logger.error('Error saving text:', error);
      setEditValue(value);
      setIsEditing(false);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (isEditing) {
    return (
      <div className={className}>
        <Input
          ref={inputRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          disabled={isSaving}
          placeholder={placeholder}
          maxLength={maxLength}
          className={inputClassName}
        />
      </div>
    );
  }

  return (
    <button
      onClick={() => setIsEditing(true)}
      className={`group inline-flex items-center gap-1.5 text-left transition-colors hover:text-primary ${className}`}
    >
      <span>{renderView ? renderView(value) : displayWord(value)}</span>
      <Edit2 className={`${iconSize} opacity-0 transition-opacity ${iconHoverOpacity}`} />
    </button>
  );
};
