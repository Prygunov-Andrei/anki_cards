import React, { useState, useRef, useEffect } from 'react';
import { Input } from './ui/input';
import { Edit2 } from 'lucide-react';

interface EditableTitleProps {
  value: string;
  onSave: (newValue: string) => Promise<void>;
  placeholder?: string;
  className?: string;
}

/**
 * Компонент EditableTitle - inline редактирование заголовка
 * iOS 25 стиль, оптимизирован для мобильных устройств
 */
export const EditableTitle: React.FC<EditableTitleProps> = ({
  value,
  onSave,
  placeholder = 'Введите название',
  className = '',
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

    // Валидация
    if (trimmedValue.length < 3) {
      setEditValue(value);
      setIsEditing(false);
      return;
    }

    if (trimmedValue.length > 100) {
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
      console.error('Error saving title:', error);
      setEditValue(value);
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
          className="text-2xl font-semibold"
        />
      </div>
    );
  }

  // Режим просмотра
  return (
    <button
      onClick={() => setIsEditing(true)}
      className={`group flex items-center gap-2 text-left transition-colors hover:text-primary ${className}`}
    >
      <h1 className="text-2xl font-semibold">{value}</h1>
      <Edit2 className="h-5 w-5 opacity-0 transition-opacity group-hover:opacity-100" />
    </button>
  );
};
