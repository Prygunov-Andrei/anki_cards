import React, { useState, useRef, KeyboardEvent } from 'react';
import { Card } from './ui/card';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { X, AlertCircle, Loader2, Merge } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';
import { useAuthContext } from '../contexts/AuthContext';

interface WordChipsInputProps {
  words: string[];
  onChange: (words: string[]) => void;
  disabled?: boolean;
  label?: string;
  placeholder?: string;
  targetLang?: string;
  isProcessing?: boolean;
}

/**
 * Компонент WordChipsInput - ввод слов с тегами (chips)
 * Особенности:
 * - Создание тега по Enter или точке с запятой
 * - Редактирование по двойному клику
 * - Валидация странных символов
 * - iOS 25 стиль
 */
export const WordChipsInput: React.FC<WordChipsInputProps> = ({
  words,
  onChange,
  disabled = false,
  label,
  placeholder,
  targetLang,
  isProcessing = false,
}) => {
  const t = useTranslation();
  const { user } = useAuthContext();
  const [inputValue, setInputValue] = useState('');
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Drag & drop state
  const [dragSourceIndex, setDragSourceIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  // Mobile merge: selected chips for merge
  const [selectedForMerge, setSelectedForMerge] = useState<Set<number>>(new Set());
  
  // Используем переводы, если не переданы явно
  const finalLabel = label || t.words.wordsForStudy;
  
  // Формируем плейсхолдер с названием языка
  const actualTargetLang = targetLang || user?.learning_language || 'en';
  const targetLangName = t.languageNames[actualTargetLang as keyof typeof t.languageNames] || actualTargetLang.toUpperCase();
  const finalPlaceholder = placeholder || `${t.words.enterWordsPlaceholder} ${targetLangName} ${t.words.commaSeparated}`;

  /**
   * Плюрализация слов для счетчика
   */
  const getWordCountText = (count: number): string => {
    const nativeLang = user?.native_language || 'ru';
    
    // Русская плюрализация
    if (nativeLang === 'ru') {
      if (count === 1) return t.words.wordCount;
      if (count > 1 && count < 5) return t.words.wordCountTwo;
      return t.words.wordCountMany;
    }
    
    // Английская плюрализация
    if (nativeLang === 'en') {
      return count === 1 ? t.words.wordCount : t.words.wordCountMany;
    }
    
    // Для остальных языков используем простую плюрализацию
    return count === 1 ? t.words.wordCount : t.words.wordCountMany;
  };

  /**
   * Валидация слова - проверка на странные символы
   * Разрешены скобки и слэш для форм глаголов типа "rennen (rannte / gerant)"
   * Разрешены знаки препинания для фраз и предложений
   */
  const validateWord = (word: string): boolean => {
    // Разрешены: буквы (любые), цифры, дефис, апостроф, пробел, умлауты, скобки, слэш, 
    // длинное тире, среднее тире, знаки препинания (точка, запятая, вопросительный знак, восклицательный знак, многоточие, двоеточие, точка с запятой)
    const validPattern = /^[\p{L}\p{N}\s\-'äöüßÄÖÜàèéêëîïôùûüÿçñ()[\]{}/–—.,?!…:;]+$/u;
    return validPattern.test(word);
  };

  /**
   * Добавление нового слова (или нескольких слов, разделенных точкой с запятой)
   * Умное разбиение: точки с запятой внутри скобок игнорируются
   * Поддержка переносов строк как разделителей
   */
  const addWord = (word: string) => {
    const trimmed = word.trim();
    
    if (!trimmed) return;
    
    // Сначала разбиваем по переносам строк
    const lines = trimmed.split(/[\n\r]+/).map(line => line.trim()).filter(line => line.length > 0);
    
    // Затем каждую строку разбиваем по точкам с запятой (с учётом скобок)
    const wordsToAdd: string[] = [];
    
    for (const line of lines) {
      let currentWord = '';
      let depth = 0; // Уровень вложенности скобок
      
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '(' || char === '[' || char === '{') {
          depth++;
          currentWord += char;
        } else if (char === ')' || char === ']' || char === '}') {
          depth--;
          currentWord += char;
        } else if (char === ';' && depth === 0) {
          // Точка с запятой вне скобок - это разделитель
          const cleaned = currentWord.trim();
          if (cleaned && !words.includes(cleaned) && !wordsToAdd.includes(cleaned)) {
            wordsToAdd.push(cleaned);
          }
          currentWord = '';
        } else {
          currentWord += char;
        }
      }
      
      // Добавляем последнее слово из строки
      const cleaned = currentWord.trim();
      if (cleaned && !words.includes(cleaned) && !wordsToAdd.includes(cleaned)) {
        wordsToAdd.push(cleaned);
      }
    }
    
    if (wordsToAdd.length === 0) return;

    onChange([...words, ...wordsToAdd]);
    setInputValue('');
  };

  /**
   * Обработка нажатия клавиш
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;

    // Enter или точка с запятой - добавить слово
    if (e.key === 'Enter' || e.key === ';') {
      e.preventDefault();
      addWord(inputValue);
    }
    
    // Backspace на пустом поле - удалить последний тег
    if (e.key === 'Backspace' && !inputValue && words.length > 0) {
      onChange(words.slice(0, -1));
    }
  };

  /**
   * Обработка потери фокуса
   */
  const handleBlur = () => {
    if (inputValue.trim()) {
      addWord(inputValue);
    }
  };

  /**
   * Обработка вставки из буфера обмена
   */
  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const pastedText = e.clipboardData.getData('text');
    
    // Если вставленный текст содержит точки с запятой или переносы строк, обрабатываем его специально
    if (pastedText.includes(';') || pastedText.includes('\n') || pastedText.includes('\r')) {
      e.preventDefault();
      addWord(inputValue + pastedText); // Добавляем к существующему тексту
    }
  };

  /**
   * Удаление слова по индексу
   */
  const removeWord = (index: number) => {
    if (disabled) return;
    onChange(words.filter((_, i) => i !== index));
  };

  /**
   * Merge two chips into one phrase
   */
  const handleMergeChips = (sourceIdx: number, targetIdx: number) => {
    if (sourceIdx === targetIdx) return;
    const merged = `${words[sourceIdx]} ${words[targetIdx]}`.trim();
    const newWords = words.filter((_, i) => i !== sourceIdx && i !== targetIdx);
    const insertAt = targetIdx > sourceIdx ? targetIdx - 1 : targetIdx;
    newWords.splice(insertAt, 0, merged);
    onChange(newWords);
    setDragSourceIndex(null);
    setDragOverIndex(null);
    setSelectedForMerge(new Set());
  };

  /**
   * Mobile: toggle chip selection for merge
   */
  const toggleMergeSelection = (index: number) => {
    setSelectedForMerge((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  /**
   * Mobile: merge selected chips
   */
  const mergeSelectedChips = () => {
    if (selectedForMerge.size < 2) return;
    const indices = Array.from(selectedForMerge).sort((a, b) => a - b);
    const merged = indices.map((i) => words[i]).join(' ');
    const newWords = words.filter((_, i) => !selectedForMerge.has(i));
    newWords.splice(indices[0], 0, merged);
    onChange(newWords);
    setSelectedForMerge(new Set());
  };

  /**
   * Начало редактирования тега
   */
  const startEditing = (index: number) => {
    if (disabled) return;
    setEditingIndex(index);
    setEditValue(words[index]);
  };

  /**
   * Завершение редактирования тега
   */
  const finishEditing = () => {
    if (editingIndex === null) return;

    const trimmed = editValue.trim();
    
    if (trimmed && trimmed !== words[editingIndex]) {
      const newWords = [...words];
      newWords[editingIndex] = trimmed;
      onChange(newWords);
    }

    setEditingIndex(null);
    setEditValue('');
  };

  /**
   * Обработка нажатия клавиш при редактировании
   */
  const handleEditKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      finishEditing();
    } else if (e.key === 'Escape') {
      setEditingIndex(null);
      setEditValue('');
    }
  };

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Поле ввода с тегами */}
        <div
          className={`
            flex min-h-[120px] flex-wrap items-start gap-2 rounded-lg border bg-background p-3
            ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-text'}
            ${!disabled && 'hover:border-primary/50'}
            transition-colors
          `}
          onClick={() => !disabled && inputRef.current?.focus()}
        >
          {/* Теги (chips) */}
          {words.map((word, index) => {
            const isValid = validateWord(word);
            const isEditing = editingIndex === index;
            const isDragSource = dragSourceIndex === index;
            const isDragOver = dragOverIndex === index && dragSourceIndex !== index;
            const isSelectedForMerge = selectedForMerge.has(index);

            return (
              <div
                key={`${word}-${index}`}
                draggable={!disabled && editingIndex === null}
                onDragStart={(e) => {
                  setDragSourceIndex(index);
                  e.dataTransfer.effectAllowed = 'move';
                }}
                onDragEnd={() => {
                  setDragSourceIndex(null);
                  setDragOverIndex(null);
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.dataTransfer.dropEffect = 'move';
                }}
                onDragEnter={() => {
                  if (dragSourceIndex !== null && dragSourceIndex !== index) {
                    setDragOverIndex(index);
                  }
                }}
                onDragLeave={() => {
                  if (dragOverIndex === index) setDragOverIndex(null);
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  if (dragSourceIndex !== null) {
                    handleMergeChips(dragSourceIndex, index);
                  }
                }}
                className={`
                  flex items-center gap-1 rounded-md px-3 py-1.5 text-sm transition-all
                  ${isValid
                    ? 'bg-gradient-to-r from-cyan-100 to-blue-100 text-cyan-900 dark:from-cyan-900/30 dark:to-blue-900/30 dark:text-cyan-100'
                    : 'bg-gradient-to-r from-red-100 to-orange-100 text-red-900 dark:from-red-900/30 dark:to-orange-900/30 dark:text-red-100'
                  }
                  ${!disabled && 'hover:shadow-sm'}
                  ${isDragSource ? 'opacity-40 scale-95' : ''}
                  ${isDragOver ? 'ring-2 ring-blue-400 scale-105 bg-blue-50 dark:bg-blue-900/50' : ''}
                  ${isSelectedForMerge ? 'ring-2 ring-purple-400 dark:ring-purple-500' : ''}
                  ${!disabled && editingIndex === null ? 'cursor-grab active:cursor-grabbing' : ''}
                `}
              >
                {isEditing ? (
                  /* Режим редактирования */
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={handleEditKeyDown}
                    onBlur={finishEditing}
                    autoFocus
                    className="min-w-[80px] max-w-[400px] bg-transparent outline-none"
                    style={{ width: `${Math.max(80, editValue.length * 8 + 20)}px` }}
                    disabled={disabled}
                  />
                ) : (
                  /* Обычный режим */
                  <span
                    onDoubleClick={() => startEditing(index)}
                    onClick={() => {
                      if (selectedForMerge.size > 0) {
                        toggleMergeSelection(index);
                      }
                    }}
                    className={!disabled ? 'cursor-pointer' : ''}
                  >
                    {word}
                  </span>
                )}

                {/* Иконка предупреждения для невалидных слов */}
                {!isValid && !isEditing && (
                  <AlertCircle className="h-3.5 w-3.5" />
                )}

                {/* Mobile: merge selection toggle */}
                {!isEditing && selectedForMerge.size > 0 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleMergeSelection(index);
                    }}
                    disabled={disabled}
                    className={`
                      rounded-sm transition-colors md:hidden
                      ${isSelectedForMerge ? 'text-purple-600' : 'text-muted-foreground'}
                    `}
                  >
                    <Merge className="h-3.5 w-3.5" />
                  </button>
                )}

                {/* Кнопка удаления */}
                {!isEditing && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeWord(index);
                    }}
                    disabled={disabled}
                    className={`
                      rounded-sm transition-colors
                      ${!disabled && 'hover:bg-white/50 dark:hover:bg-black/30'}
                    `}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            );
          })}

          {/* Поле ввода нового слова */}
          <Input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            onPaste={handlePaste}
            placeholder={words.length === 0 ? finalPlaceholder : ''}
            disabled={disabled}
            className="flex-1 border-0 bg-transparent p-0 shadow-none focus-visible:ring-0"
          />
        </div>

        {/* Mobile merge controls */}
        {words.length >= 2 && !disabled && (
          <div className="flex items-center gap-2 md:hidden">
            {selectedForMerge.size === 0 ? (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs text-muted-foreground"
                onClick={() => toggleMergeSelection(0)}
              >
                <Merge className="mr-1 h-3 w-3" />
                {t.words.mergeWords || 'Merge words'}
              </Button>
            ) : (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  disabled={selectedForMerge.size < 2}
                  onClick={mergeSelectedChips}
                >
                  <Merge className="mr-1 h-3 w-3" />
                  {t.words.merge || 'Merge'} ({selectedForMerge.size})
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => setSelectedForMerge(new Set())}
                >
                  {t.common.cancel || 'Cancel'}
                </Button>
              </>
            )}
          </div>
        )}

        {/* Счетчик слов */}
        {words.length > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {words.length} {getWordCountText(words.length)}
            </span>
            
            {/* Предупреждение о невалидных словах */}
            {words.some((w) => !validateWord(w)) && (
              <div className="flex items-center gap-1 text-orange-600 dark:text-orange-400">
                <AlertCircle className="h-4 w-4" />
                <span>{t.words.checkInvalidWords}</span>
              </div>
            )}
            
            {/* Индикатор обработки слов (для немецкого языка) */}
            {isProcessing && (
              <div className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{t.words.processingWords}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};