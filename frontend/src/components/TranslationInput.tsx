import React from 'react';

interface TranslationInputProps {
  words: string[];
  translations: Record<string, string>;
  onChange: (translations: Record<string, string>) => void;
}

export const TranslationInput: React.FC<TranslationInputProps> = ({
  words,
  translations,
  onChange,
}) => {
  const handleTranslationChange = (word: string, translation: string) => {
    onChange({
      ...translations,
      [word]: translation,
    });
  };

  if (words.length === 0) {
    return (
      <div className="text-gray-500 text-center py-8">
        Сначала добавьте слова для перевода
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-700">
        Введите переводы ({words.length} слов)
      </h3>
      <div className="space-y-3">
        {words.map((word) => (
          <div key={word} className="flex items-center gap-4">
            <div className="w-32 text-sm font-medium text-gray-700">
              {word}:
            </div>
            <input
              type="text"
              value={translations[word] || ''}
              onChange={(e) => handleTranslationChange(word, e.target.value)}
              placeholder="Введите перевод"
              required
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

