import React, { useState, useRef } from 'react';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from './ui/dialog';
import { Camera, Loader2, X, Plus } from 'lucide-react';
import { mediaService } from '../services/media.service';
import { showError } from '../utils/toast-helpers';
import { useTranslation } from '../contexts/LanguageContext';
import { logger } from '../utils/logger';

interface PhotoWordExtractorProps {
  targetLang: string;
  sourceLang: string;
  onWordsExtracted: (words: string[]) => void;
  disabled?: boolean;
}

export const PhotoWordExtractor: React.FC<PhotoWordExtractorProps> = ({
  targetLang,
  sourceLang,
  onWordsExtracted,
  disabled = false,
}) => {
  const t = useTranslation();
  const pt = t.words?.photoExtraction ?? {} as Record<string, string>;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractedWords, setExtractedWords] = useState<string[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [hasResult, setHasResult] = useState(false);

  const handleCameraClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Показываем превью
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setIsOpen(true);
    setIsExtracting(true);
    setHasResult(false);
    setExtractedWords([]);

    try {
      const result = await mediaService.extractWordsFromPhoto({
        image: file,
        target_lang: targetLang,
        source_lang: sourceLang,
      });

      setExtractedWords(result.words);
      setHasResult(true);
    } catch (error: any) {
      logger.error('Error extracting words from photo:', error);
      const message = error?.response?.data?.error || pt.extractionError;
      showError(message);
      setIsOpen(false);
    } finally {
      setIsExtracting(false);
      // Очищаем input чтобы можно было повторно выбрать тот же файл
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRemoveWord = (index: number) => {
    setExtractedWords((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAddWords = () => {
    if (extractedWords.length > 0) {
      onWordsExtracted(extractedWords);
    }
    handleClose();
  };

  const handleClose = () => {
    setIsOpen(false);
    setExtractedWords([]);
    setPreviewUrl(null);
    setHasResult(false);
    setIsExtracting(false);
  };

  return (
    <>
      {/* Скрытый input для камеры */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelected}
        className="hidden"
      />

      {/* Кнопка камеры */}
      <Button
        variant="outline"
        size="lg"
        onClick={handleCameraClick}
        disabled={disabled}
        className="w-full gap-2"
      >
        <Camera className="h-8 w-8 sm:h-5 sm:w-5" />
        {pt.scanFromPhoto}
      </Button>

      {/* Диалог с результатами */}
      <Dialog open={isOpen} onOpenChange={(open) => { if (!open) handleClose(); }}>
        <DialogContent className="max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{pt.extractedWords}</DialogTitle>
            <DialogDescription>
              {isExtracting
                ? pt.extractingWords
                : hasResult && extractedWords.length > 0
                  ? `${extractedWords.length} ${pt.wordsFound}`
                  : hasResult
                    ? pt.noWordsFound
                    : ''
              }
            </DialogDescription>
          </DialogHeader>

          {/* Превью фото */}
          {previewUrl && (
            <div className="flex justify-center">
              <img
                src={previewUrl}
                alt="Captured"
                className="max-h-32 rounded-lg object-contain border"
              />
            </div>
          )}

          {/* Спиннер загрузки */}
          {isExtracting && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Список извлечённых слов */}
          {hasResult && extractedWords.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {extractedWords.map((word, index) => (
                <span
                  key={`${word}-${index}`}
                  className="inline-flex items-center gap-1 rounded-full bg-secondary px-3 py-1.5 text-sm font-medium"
                >
                  {word}
                  <button
                    onClick={() => handleRemoveWord(index)}
                    className="ml-1 rounded-full p-0.5 hover:bg-destructive/20 hover:text-destructive transition-colors"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Кнопки */}
          {hasResult && (
            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                {pt.cancel}
              </Button>
              {extractedWords.length > 0 && (
                <Button onClick={handleAddWords} className="gap-2">
                  <Plus className="h-4 w-4" />
                  {pt.addExtractedWords} ({extractedWords.length})
                </Button>
              )}
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};
