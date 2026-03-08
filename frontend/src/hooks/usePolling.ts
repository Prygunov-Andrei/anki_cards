import { useRef, useEffect, useCallback } from 'react';

interface UsePollingOptions<T> {
  /** Async function to call on each poll */
  fetcher: () => Promise<T>;
  /** Callback when new data arrives */
  onData: (data: T) => void;
  /** Return true to stop polling */
  shouldStop?: (data: T) => boolean;
  /** Called when polling stops (via shouldStop) */
  onComplete?: () => void;
  /** Polling interval in ms */
  interval: number;
  /** Whether polling is active */
  enabled: boolean;
}

/**
 * Generic polling hook with auto-cleanup.
 * Replaces manual setInterval + useRef patterns.
 */
export function usePolling<T>({
  fetcher,
  onData,
  shouldStop,
  onComplete,
  interval,
  enabled,
}: UsePollingOptions<T>) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      stop();
      return;
    }

    stop(); // clear any existing interval

    intervalRef.current = setInterval(async () => {
      try {
        const data = await fetcher();
        onData(data);
        if (shouldStop?.(data)) {
          stop();
          onComplete?.();
        }
      } catch {
        // Polling error — will retry next interval
      }
    }, interval);

    return stop;
  }, [enabled, interval]); // eslint-disable-line react-hooks/exhaustive-deps

  return { stop };
}
