import React from 'react';
import { SmartWordInput, WordTranslationPair } from '../SmartWordInput';
import { GenerationProgress, GenerationStatus } from '../GenerationProgress';
import { MediaSettings } from '../MediaSettings';
import { ImageStyle } from '../ImageStyleSelector';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Loader2, BookOpen, Plus } from 'lucide-react';
import { useTranslation } from '../../contexts/LanguageContext';

interface DeckEditorWordInputProps {
  targetLang?: string;
  sourceLang?: string;
  pendingWords: WordTranslationPair[];
  isGenerating: boolean;
  // Media settings
  generateImages: boolean;
  generateAudio: boolean;
  imageStyle: ImageStyle;
  imageProvider: 'auto' | 'openai' | 'gemini' | 'nano-banana';
  audioProvider: 'auto' | 'openai' | 'gtts';
  // Generation progress
  generationStatus: GenerationStatus;
  generationProgress: { current: number; total: number; currentWord: string };
  // Handlers
  onAddWords: (pairs: WordTranslationPair[]) => void;
  onGenerateCards: () => void;
  onGenerateImagesChange: (value: boolean) => void;
  onGenerateAudioChange: (value: boolean) => void;
  onImageStyleChange: (value: ImageStyle) => void;
  onImageProviderChange: (value: 'auto' | 'openai' | 'gemini' | 'nano-banana') => void;
  onAudioProviderChange: (value: 'auto' | 'openai' | 'gtts') => void;
}

export const DeckEditorWordInput: React.FC<DeckEditorWordInputProps> = ({
  targetLang,
  sourceLang,
  pendingWords,
  isGenerating,
  generateImages,
  generateAudio,
  imageStyle,
  imageProvider,
  audioProvider,
  generationStatus,
  generationProgress,
  onAddWords,
  onGenerateCards,
  onGenerateImagesChange,
  onGenerateAudioChange,
  onImageStyleChange,
  onImageProviderChange,
  onAudioProviderChange,
}) => {
  const t = useTranslation();

  return (
    <>
      {/* Форма добавления слов */}
      <div className="mb-6">
        <SmartWordInput
          targetLang={targetLang}
          sourceLang={sourceLang}
          onAddWords={onAddWords}
          showChipsInput={true}
        />
      </div>

      {/* Превью добавленных слов (показываем только если есть слова в буфере) */}
      {pendingWords.length > 0 && (
        <div className="mb-6">
          <Card className="p-6">
            <h3 className="mb-4 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-purple-500" />
              {t.decks.wordsToAdd || 'Слова для добавления'} ({pendingWords.length})
            </h3>
            <div className="grid gap-3">
              {pendingWords.map((pair, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg border border-purple-200 bg-purple-50/50 p-3 dark:border-purple-800 dark:bg-purple-950/20"
                >
                  <div className="flex-1">
                    <div className="font-medium text-purple-900 dark:text-purple-100">
                      {pair.word}
                    </div>
                    <div className="text-sm text-purple-700 dark:text-purple-300">
                      {pair.translation}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Настройки медиа + кнопка генерации (показываем только если есть слова в буфере) */}
      {pendingWords.length > 0 && (
        <>
          <div className="mb-6">
            <MediaSettings
              generateImages={generateImages}
              generateAudio={generateAudio}
              imageStyle={imageStyle}
              imageProvider={imageProvider}
              audioProvider={audioProvider}
              onGenerateImagesChange={onGenerateImagesChange}
              onGenerateAudioChange={onGenerateAudioChange}
              onImageStyleChange={onImageStyleChange}
              onImageProviderChange={onImageProviderChange}
              onAudioProviderChange={onAudioProviderChange}
              disabled={isGenerating}
            />
          </div>

          {/* Прогресс генерации */}
          <GenerationProgress
            status={generationStatus}
            current={generationProgress.current}
            total={generationProgress.total}
            currentWord={generationProgress.currentWord}
          />

          {/* Кнопка генерации карточек */}
          <div className="mb-6">
            <Button
              onClick={onGenerateCards}
              disabled={isGenerating}
              variant="default"
              size="lg"
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  {t.decks.generating}
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-5 w-5" />
                  {t.decks.generateCards} ({pendingWords.length})
                </>
              )}
            </Button>
          </div>
        </>
      )}
    </>
  );
};
