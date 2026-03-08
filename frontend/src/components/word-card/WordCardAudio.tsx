import React from 'react';
import { AudioPlayer } from '../AudioPlayer';

interface WordCardAudioProps {
  audioUrl?: string;
  word: string;
  regeneratingAudio: boolean;
}

export const WordCardAudio: React.FC<WordCardAudioProps> = ({
  audioUrl,
  word,
  regeneratingAudio,
}) => {
  return (
    <div className="flex items-center gap-2">
      {/* Audio player */}
      {!regeneratingAudio && audioUrl && audioUrl !== 'null' && audioUrl !== 'undefined' && audioUrl.trim() !== '' && (
        <div className="flex-1">
          <AudioPlayer
            audioUrl={audioUrl}
            word={word}
            compact={false}
          />
        </div>
      )}

      {/* Loading indicator */}
      {regeneratingAudio && (
        <div className="flex-1 flex items-center justify-center py-2">
          <div className="flex gap-2">
            <div className="w-2 h-2 rounded-full bg-[#4FACFE] animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
            <div className="w-2 h-2 rounded-full bg-[#FF6B9D] animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1s' }}></div>
            <div className="w-2 h-2 rounded-full bg-[#FFD93D] animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1s' }}></div>
          </div>
        </div>
      )}
    </div>
  );
};
