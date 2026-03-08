import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../ui/button';
import { ImageIcon, RefreshCw } from 'lucide-react';
import { cn } from '../ui/utils';

interface WordCardImageProps {
  word: string;
  imageUrl?: string;
  regeneratingImage: boolean;
  disabled?: boolean;
  onImageClick: () => void;
  onRegenerateImage?: () => void;
}

export const WordCardImage: React.FC<WordCardImageProps> = ({
  word,
  imageUrl,
  regeneratingImage,
  disabled = false,
  onImageClick,
  onRegenerateImage,
}) => {
  const [imageRevealed, setImageRevealed] = useState(true);
  const revealTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    if (imageUrl) {
      setImageRevealed(true);
      clearTimeout(revealTimerRef.current);
      revealTimerRef.current = setTimeout(() => setImageRevealed(false), 8000);
    }
    return () => clearTimeout(revealTimerRef.current);
  }, [imageUrl]);

  const handleRevealImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setImageRevealed(true);
    clearTimeout(revealTimerRef.current);
    revealTimerRef.current = setTimeout(() => setImageRevealed(false), 8000);
  };

  // Loading indicator
  if (regeneratingImage) {
    return (
      <div className="relative aspect-video w-full overflow-hidden bg-gradient-to-br from-cyan-50 to-pink-50 dark:from-cyan-950/20 dark:to-pink-950/20 flex items-center justify-center">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-[#4FACFE] animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
          <div className="w-3 h-3 rounded-full bg-[#FF6B9D] animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1s' }}></div>
          <div className="w-3 h-3 rounded-full bg-[#FFD93D] animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1s' }}></div>
        </div>
      </div>
    );
  }

  // Image present
  if (imageUrl) {
    return (
      <div
        className="relative aspect-video w-full overflow-hidden bg-gradient-to-br from-cyan-50 to-pink-50 dark:from-cyan-950/20 dark:to-pink-950/20 cursor-pointer group"
        onClick={imageRevealed ? onImageClick : undefined}
      >
        <img
          src={imageUrl}
          alt={word}
          className="h-full w-full object-cover transition-transform group-hover:scale-105"
        />
        {/* Frosted glass overlay */}
        <div
          className={cn(
            "absolute inset-0 flex items-center justify-center transition-all duration-700",
            imageRevealed
              ? "bg-transparent backdrop-blur-0 opacity-0 pointer-events-none"
              : "bg-white/30 dark:bg-black/40 backdrop-blur-md opacity-100 cursor-pointer"
          )}
          onClick={handleRevealImage}
        >
          {!imageRevealed && (
            <ImageIcon className="h-8 w-8 text-white/70 drop-shadow" />
          )}
        </div>
        {/* Hover overlay (only when revealed) */}
        {imageRevealed && (
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center pointer-events-none">
            <ImageIcon className="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        )}
      </div>
    );
  }

  // Placeholder
  return (
    <div className="relative aspect-video w-full overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 flex flex-col items-center justify-center gap-2">
      <ImageIcon className="h-10 w-10 text-muted-foreground/40" />
      <span className="text-xs text-muted-foreground/60">Изображение</span>
      {onRegenerateImage && (
        <Button variant="ghost" size="sm" onClick={onRegenerateImage} disabled={disabled}>
          <RefreshCw className="mr-1 h-3 w-3" /> Сгенерировать
        </Button>
      )}
    </div>
  );
};
