import React from 'react';
import { Button } from '../ui/button';
import { WordChipsInput } from '../WordChipsInput';
import { PhotoWordExtractor } from '../PhotoWordExtractor';
import { TranslationTable, WordTranslationPair } from '../TranslationTable';
import { GeneratedWordsGrid } from '../GeneratedWordsGrid';
import { CompactLiterarySourceSelector } from '../literary-context/CompactLiterarySourceSelector';
import { Loader2 } from 'lucide-react';

interface WordInputSectionProps {
  words: string[];
  translations: WordTranslationPair[];
  targetLang: string;
  sourceLang: string;
  isGenerating: boolean;
  isTranslating: boolean;
  isProcessingWords: boolean;
  generatedImages: Record<string, string>;
  generatedAudio: Record<string, string>;
  activeLiterarySource: string | null;
  onWordsChange: (newWords: string[]) => Promise<void>;
  onTranslationsChange: (pairs: WordTranslationPair[]) => void;
  onPhotoWordsExtracted: (photoWords: string[]) => void;
  onDeleteWord: (word: string) => void;
  onRegenerateImage: (word: string) => Promise<void>;
  onRegenerateAudio: (word: string) => Promise<void>;
  onSourceChange: (slug: string | null) => void;
  onClearDraft: () => void;
  t: Record<string, any>;
}

export function WordInputSection({
  words,
  translations,
  targetLang,
  sourceLang,
  isGenerating,
  isTranslating,
  isProcessingWords,
  generatedImages,
  generatedAudio,
  activeLiterarySource,
  onWordsChange,
  onTranslationsChange,
  onPhotoWordsExtracted,
  onDeleteWord,
  onRegenerateImage,
  onRegenerateAudio,
  onSourceChange,
  onClearDraft,
  t,
}: WordInputSectionProps) {
  return (
    <>
      {/* 1. Photo button */}
      <div className="flex items-center gap-2">
        <PhotoWordExtractor
          targetLang={targetLang}
          sourceLang={sourceLang}
          onWordsExtracted={onPhotoWordsExtracted}
          disabled={isGenerating}
        />
      </div>

      {/* 2. Word chips input */}
      <WordChipsInput
        words={words}
        onChange={onWordsChange}
        disabled={isGenerating}
        isProcessing={isProcessingWords}
      />

      {/* 2.5. Clear draft button */}
      {words.length > 0 && !isGenerating && (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            className="text-destructive hover:text-destructive"
            onClick={onClearDraft}
          >
            {t.draft.clearAll}
          </Button>
        </div>
      )}

      {/* 3. Compact literary source selector */}
      {words.length > 0 && (
        <CompactLiterarySourceSelector
          activeSource={activeLiterarySource}
          onSourceChange={onSourceChange}
        />
      )}

      {/* 4. Auto-translate indicator */}
      {isTranslating && (
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          {t.toast.autoTranslating}
        </div>
      )}

      {/* 5. Translation table */}
      {words.length > 0 && (
        <TranslationTable
          words={words}
          translations={translations}
          onTranslationsChange={onTranslationsChange}
          targetLang={targetLang}
          sourceLang={sourceLang}
          disabled={isGenerating}
          imageFiles={generatedImages}
          audioFiles={generatedAudio}
        />
      )}

      {/* 6. Generated words grid */}
      {words.length > 0 && (
        <GeneratedWordsGrid
          words={translations}
          imageFiles={generatedImages}
          audioFiles={generatedAudio}
          onDeleteWord={onDeleteWord}
          onRegenerateImage={onRegenerateImage}
          onRegenerateAudio={onRegenerateAudio}
          disabled={isGenerating}
        />
      )}
    </>
  );
}
