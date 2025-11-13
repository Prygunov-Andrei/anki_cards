import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { WordInput } from './WordInput';
import { LanguageSelector } from './LanguageSelector';
import { TranslationInput } from './TranslationInput';
import { GenerateButton } from './GenerateButton';
import { MediaGenerator } from './MediaGenerator';
import { Language, WordMedia } from '../types';

export const MainPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [words, setWords] = useState<string[]>([]);
  const [language, setLanguage] = useState<Language>(user?.preferred_language || 'pt');
  const [translations, setTranslations] = useState<Record<string, string>>({});
  const [deckName, setDeckName] = useState('');
  const [wordMedia, setWordMedia] = useState<Record<string, WordMedia>>({});

  const handleSuccess = () => {
    // Очищаем форму после успешной генерации
    setWords([]);
    setTranslations({});
    setDeckName('');
    setWordMedia({});
    alert('Карточки успешно сгенерированы и скачаны!');
  };

  const handleMediaChange = (word: string, media: WordMedia) => {
    console.log(`MainPage: handleMediaChange для слова "${word}":`, media);
    console.log(`MainPage: media.imagePath:`, media.imagePath);
    console.log(`MainPage: media.audioPath:`, media.audioPath);
    setWordMedia((prev) => {
      // Объединяем существующие данные с новыми, чтобы не потерять медиафайлы
      const existingMedia = prev[word] || {};
      const mergedMedia = {
        word: media.word || existingMedia.word || word,
        // Используем новые значения, если они есть, иначе сохраняем существующие
        imageUrl: media.imageUrl ?? existingMedia.imageUrl,
        audioUrl: media.audioUrl ?? existingMedia.audioUrl,
        imageId: media.imageId ?? existingMedia.imageId,
        audioId: media.audioId ?? existingMedia.audioId,
        imagePath: media.imagePath ?? existingMedia.imagePath,
        audioPath: media.audioPath ?? existingMedia.audioPath,
      };
      const updated = {
        ...prev,
        [word]: mergedMedia,
      };
      console.log(`MainPage: existingMedia для "${word}":`, existingMedia);
      console.log(`MainPage: mergedMedia для "${word}":`, mergedMedia);
      console.log(`MainPage: обновленный wordMedia:`, updated);
      return updated;
    });
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

          {/* Генерация медиафайлов для каждого слова */}
          {words.length > 0 && translations && Object.keys(translations).length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Медиафайлы (опционально)</h3>
              <div className="space-y-4">
                {words.map((word) => {
                  const translation = translations[word];
                  if (!translation) return null;
                  const handleMediaChangeForWord = (media: WordMedia) => {
                    console.log(`MainPage: handleMediaChangeForWord для "${word}" вызван с:`, media);
                    handleMediaChange(word, media);
                  };
                  return (
                    <MediaGenerator
                      key={word}
                      word={word}
                      translation={translation}
                      language={language}
                      onMediaChange={handleMediaChangeForWord}
                      initialMedia={wordMedia[word]}
                    />
                  );
                })}
              </div>
            </div>
          )}

          <GenerateButton
            words={words}
            language={language}
            translations={translations}
            deckName={deckName}
            wordMedia={wordMedia}
            onSuccess={handleSuccess}
          />
        </div>
      </main>
    </div>
  );
};

