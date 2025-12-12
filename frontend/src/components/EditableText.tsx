import React, { useState, useRef, useEffect } from 'react';
import { Input } from './ui/input';
import { Edit2 } from 'lucide-react';
import { displayWord } from '../utils/helpers';

interface EditableTextProps {
  value: string;
  onSave: (newValue: string) => Promise<void>;
  placeholder?: string;
  className?: string;
  inputClassName?: string;
  maxLength?: number;
}

/**
 * Компонент EditableText - inline редактирование текста
 * iOS 25 стиль, оптимизирован для мобильных устройств
 */
export const EditableText: React.FC<EditableTextProps> = ({
  value,
  onSave,
  placeholder = 'Введите текст',
  className = '',
  inputClassName = '',
  maxLength = 200,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [isSaving, setIsSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Синхронизация с внешним значением
  useEffect(() => {
    setEditValue(value);
  }, [value]);

  // Автофокус при входе в режим редактирования
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  /**
   * Сохранить изменения
   */
  const handleSave = async () => {
    const trimmedValue = editValue.trim();

    // Если значение не изменилось или пустое
    if (!trimmedValue || trimmedValue === value) {
      setEditValue(value);
      setIsEditing(false);
      return;
    }

    // Валидация длины
    if (trimmedValue.length > maxLength) {
      setEditValue(value);
      setIsEditing(false);
      return;
    }

    // Сохранение
    setIsSaving(true);
    try {
      await onSave(trimmedValue);
      setIsEditing(false);
    } catch (error) {
      console.error('Error saving text:', error);
      setEditValue(value);
      setIsEditing(false);
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Отменить редактирование
   */
  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  /**
   * Обработка нажатия клавиш
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  // Режим редактирования
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

  // Режим просмотра
  return (
    <button
      onClick={() => setIsEditing(true)}
      className={`group inline-flex items-center gap-1.5 text-left transition-colors hover:text-primary ${className}`}
    >
      <span>{displayWord(value)}</span>
      <Edit2 className="h-3.5 w-3.5 opacity-0 transition-opacity group-hover:opacity-60" />
    </button>
  );
};