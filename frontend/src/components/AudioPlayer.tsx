import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2 } from 'lucide-react';
import { Button } from './ui/button';
import { getAbsoluteUrl } from '../utils/url-helpers';

interface AudioPlayerProps {
  audioUrl: string;
  word: string;
  compact?: boolean;
}

/**
 * Компонент аудио-плеер с play/pause и прогресс-баром
 * iOS 25 стиль, компактный дизайн для встраивания в таблицу
 */
export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  audioUrl,
  word,
  compact = false,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [hasError, setHasError] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Преобразуем относительный URL в абсолютный
  const absoluteAudioUrl = getAbsoluteUrl(audioUrl) || audioUrl;

  // Не рендерим плеер если URL пустой или некорректный
  if (
    !absoluteAudioUrl || 
    absoluteAudioUrl === 'null' || 
    absoluteAudioUrl === 'undefined' ||
    absoluteAudioUrl.trim() === '' ||
    absoluteAudioUrl.endsWith('/null') ||
    absoluteAudioUrl.endsWith('/undefined')
  ) {
    return null;
  }

  /**
   * Инициализация аудио
   */
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    // Сбрасываем ошибку при изменении URL
    setHasError(false);
    setIsPlaying(false);
    setProgress(0);

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
    };

    const handleTimeUpdate = () => {
      setProgress((audio.currentTime / audio.duration) * 100);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setProgress(0);
    };

    const handleError = () => {
      setHasError(true);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
    };
  }, [absoluteAudioUrl]);

  /**
   * Переключить воспроизведение
   */
  const togglePlay = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Предотвращаем всплытие клика
    const audio = audioRef.current;
    if (!audio || hasError) return;

    try {
      if (isPlaying) {
        audio.pause();
        setIsPlaying(false);
      } else {
        await audio.play();
        setIsPlaying(true);
      }
    } catch (error) {
      console.error('Error playing audio:', error);
      setHasError(true);
      setIsPlaying(false);
    }
  };

  /**
   * Перемотка по клику на прогресс-бар
   */
  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    const audio = audioRef.current;
    if (!audio) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    audio.currentTime = percentage * audio.duration;
  };

  /**
   * Форматирование времени
   */
  const formatTime = (seconds: number) => {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Компактная версия (для таблицы)
  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <audio ref={audioRef} src={absoluteAudioUrl} preload="metadata" />
        <Button
          variant="ghost"
          size="sm"
          onClick={togglePlay}
          className="h-8 w-8 p-0 hover:bg-cyan-100"
        >
          {isPlaying ? (
            <Pause className="h-4 w-4 text-cyan-600" />
          ) : (
            <Play className="h-4 w-4 text-cyan-600" />
          )}
        </Button>
        {isPlaying && (
          <div className="h-1 w-12 overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full bg-gradient-to-r from-cyan-400 to-pink-400 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>
    );
  }

  // Полная версия (для модальных окон и отдельных страниц)
  return (
    <div className="w-full space-y-2">
      <audio ref={audioRef} src={absoluteAudioUrl} preload="metadata" />
      
      {/* Контролы */}
      <div className="flex items-center gap-3">
        {/* Кнопка play/pause */}
        <Button
          variant="outline"
          size="sm"
          onClick={togglePlay}
          className="h-10 w-10 rounded-full p-0 shadow-md hover:shadow-lg"
        >
          {isPlaying ? (
            <Pause className="h-5 w-5 text-cyan-600" />
          ) : (
            <Play className="h-5 w-5 text-cyan-600" />
          )}
        </Button>

        {/* Прогресс-бар */}
        <div className="flex-1">
          <div
            className="h-2 cursor-pointer overflow-hidden rounded-full bg-gray-200 hover:h-3 transition-all"
            onClick={handleProgressClick}
          >
            <div
              className="h-full bg-gradient-to-r from-cyan-400 via-pink-400 to-yellow-400 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};