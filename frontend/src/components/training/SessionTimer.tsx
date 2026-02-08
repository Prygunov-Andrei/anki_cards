import React, { useState, useEffect, useRef } from 'react';
import { Clock } from 'lucide-react';

interface SessionTimerProps {
  /** Duration in minutes. 0 or undefined = infinite */
  durationMinutes?: number;
  /** Called when time is up */
  onTimeUp?: () => void;
  /** Whether the timer is active */
  active?: boolean;
}

/**
 * Таймер тренировочной сессии.
 * Считает вверх (прошло) если duration не задан, или обратный отсчёт.
 */
export const SessionTimer: React.FC<SessionTimerProps> = ({
  durationMinutes,
  onTimeUp,
  active = true,
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hasCalledTimeUp = useRef(false);

  useEffect(() => {
    if (!active) return;

    intervalRef.current = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [active]);

  // Check if time is up
  useEffect(() => {
    if (
      durationMinutes &&
      durationMinutes > 0 &&
      elapsedSeconds >= durationMinutes * 60 &&
      !hasCalledTimeUp.current
    ) {
      hasCalledTimeUp.current = true;
      onTimeUp?.();
    }
  }, [elapsedSeconds, durationMinutes, onTimeUp]);

  const formatTime = (totalSeconds: number): string => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const isCountdown = durationMinutes && durationMinutes > 0;
  const displaySeconds = isCountdown
    ? Math.max(0, durationMinutes * 60 - elapsedSeconds)
    : elapsedSeconds;

  const isWarning = isCountdown && displaySeconds < 60;

  return (
    <div
      className={`flex items-center gap-1.5 text-sm font-mono ${
        isWarning ? 'text-red-500 animate-pulse' : 'text-muted-foreground'
      }`}
    >
      <Clock className="h-4 w-4" />
      <span>{formatTime(displaySeconds)}</span>
    </div>
  );
};
