import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { WordInput } from './WordInput';
import { LanguageSelector } from './LanguageSelector';
import { TranslationInput } from './TranslationInput';
import { GenerateButton } from './GenerateButton';
import { Language } from '../types';

export const MainPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [words, setWords] = useState<string[]>([]);
  const [language, setLanguage] = useState<Language>(user?.preferred_language || 'pt');
  const [translations, setTranslations] = useState<Record<string, string>>({});
  const [deckName, setDeckName] = useState('');

  const handleSuccess = () => {
    // Очищаем форму после успешной генерации
    setWords([]);
    setTranslations({});
    setDeckName('');
    alert('Карточки успешно сгенерированы и скачаны!');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Anki Card Generator</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">Привет, {user?.username}!</span>
            <button
              onClick={logout}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Выйти
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
          <h2 className="text-xl font-semibold text-gray-900">Создание карточек</h2>

          <div>
            <label htmlFor="deckName" className="block text-sm font-medium text-gray-700 mb-1">
              Название колоды
            </label>
            <input
              type="text"
              id="deckName"
              value={deckName}
              onChange={(e) => setDeckName(e.target.value)}
              placeholder="Например: Португальские слова - 2024"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <LanguageSelector value={language} onChange={setLanguage} />

          <WordInput value={words} onChange={setWords} />

          {words.length > 0 && (
            <TranslationInput
              words={words}
              translations={translations}
              onChange={setTranslations}
            />
          )}

          <GenerateButton
            words={words}
            language={language}
            translations={translations}
            deckName={deckName}
            onSuccess={handleSuccess}
          />
        </div>
      </main>
    </div>
  );
};

