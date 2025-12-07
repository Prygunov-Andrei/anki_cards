import React, { useState, useRef, KeyboardEvent } from 'react';
import { Card } from './ui/card';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { X, AlertCircle, Loader2 } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';
import { useAuthContext } from '../contexts/AuthContext';

interface WordChipsInputProps {
  words: string[];
  onChange: (words: string[]) => void;
  disabled?: boolean;
  label?: string;
  placeholder?: string;
  targetLang?: string; // Опционально, для будущего использования
  deckName?: string; // Название колоды
  onDeckNameChange?: (name: string) => void; // Callback для изменения названия
  isProcessing?: boolean; // Индикатор обработки слов (для немецкого языка)
}

/**
 * Компонент WordChipsInput - ввод слов с тегами (chips)
 * Особенности:
 * - Создание тега по Enter или запятой
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
  deckName,
  onDeckNameChange,
  isProcessing = false,
}) => {
  const t = useTranslation();
  const { user } = useAuthContext();
  const [inputValue, setInputValue] = useState('');
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  
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
   * Добавление нового слова (или нескольких слов, разделенных запятой)
   * Умное разбиение: запятые внутри скобок игнорируются
   * Поддержка переносов строк как разделителей
   */
  const addWord = (word: string) => {
    const trimmed = word.trim();
    
    if (!trimmed) return;
    
    // Сначала разбиваем по переносам строк
    const lines = trimmed.split(/[\n\r]+/).map(line => line.trim()).filter(line => line.length > 0);
    
    // Затем каждую строку разбиваем по запятым (с учётом скобок)
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
        } else if (char === ',' && depth === 0) {
          // Запятая вне скобок - это разделитель
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

    // Enter или запятая - добавить слово
    if (e.key === 'Enter' || e.key === ',') {
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
    
    // Если вставленный текст содержит запятые или переносы строк, обрабатываем его специально
    if (pastedText.includes(',') || pastedText.includes('\n') || pastedText.includes('\r')) {
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
        {/* Поле названия колоды (опционально) */}
        {onDeckNameChange && (
          <Input
            id="deck-name-input"
            value={deckName || ''}
            onChange={(e) => onDeckNameChange(e.target.value)}
            placeholder={t.decks.enterDeckName}
            disabled={disabled}
          />
        )}

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

            return (
              <div
                key={`${word}-${index}`}
                className={`
                  flex items-center gap-1 rounded-md px-3 py-1.5 text-sm transition-all
                  ${isValid
                    ? 'bg-gradient-to-r from-cyan-100 to-blue-100 text-cyan-900 dark:from-cyan-900/30 dark:to-blue-900/30 dark:text-cyan-100'
                    : 'bg-gradient-to-r from-red-100 to-orange-100 text-red-900 dark:from-red-900/30 dark:to-orange-900/30 dark:text-red-100'
                  }
                  ${!disabled && 'hover:shadow-sm'}
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
                    className="w-20 bg-transparent outline-none"
                    disabled={disabled}
                  />
                ) : (
                  /* Обычный режим */
                  <span
                    onDoubleClick={() => startEditing(index)}
                    className={!disabled ? 'cursor-pointer' : ''}
                  >
                    {word}
                  </span>
                )}

                {/* Иконка предупреждения для невалидных слов */}
                {!isValid && !isEditing && (
                  <AlertCircle className="h-3.5 w-3.5" />
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