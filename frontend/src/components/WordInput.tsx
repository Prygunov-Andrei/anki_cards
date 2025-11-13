import React, { useState, useEffect } from 'react';

interface WordInputProps {
  value: string[];
  onChange: (words: string[]) => void;
}

export const WordInput: React.FC<WordInputProps> = ({ value, onChange }) => {
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    // Синхронизируем inputValue с value при изменении извне
    if (value.length === 0) {
      setInputValue('');
    }
  }, [value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    setError('');
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddWords();
    }
  };

  const handleAddWords = () => {
    const words = inputValue
      .split(',')
      .map((w) => w.trim())
      .filter((w) => w.length > 0);

    if (words.length === 0) {
      setError('Введите хотя бы одно слово');
      return;
    }

    // Добавляем новые слова, исключая дубликаты
    const allWords = [...value, ...words];
    const uniqueWords = Array.from(new Set(allWords));
    onChange(uniqueWords);
    setInputValue('');
    setError('');
  };

  const handleRemoveWord = (wordToRemove: string) => {
    onChange(value.filter((word) => word !== wordToRemove));
  };

  return (
    <div className="space-y-2">
      <label htmlFor="words" className="block text-sm font-medium text-gray-700">
        Введите слова через запятую
      </label>
      <div className="flex gap-2">
        <input
          type="text"
          id="words"
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder="casa, palavra, livro"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={handleAddWords}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Добавить
        </button>
      </div>
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
      {value.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Добавленные слова ({value.length}):
          </p>
          <div className="flex flex-wrap gap-2">
            {value.map((word) => (
              <span
                key={word}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
              >
                {word}
                <button
                  type="button"
                  onClick={() => handleRemoveWord(word)}
                  className="ml-2 text-blue-600 hover:text-blue-800"
                  aria-label={`Удалить ${word}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

