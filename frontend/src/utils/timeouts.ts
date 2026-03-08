/**
 * Centralized timeout/interval constants (in milliseconds).
 */

// API request timeouts
export const TIMEOUTS = {
  /** Default API request timeout */
  API_DEFAULT: 30_000,
  /** Long operations: card generation, batch literary context */
  API_LONG: 300_000,
  /** Medium operations: audio generation, word analysis */
  API_MEDIUM: 120_000,
  /** Image generation/edit */
  API_IMAGE: 180_000,

  /** Promise-level timeout for image generation */
  IMAGE_GENERATION: 60_000,
  /** Promise-level timeout for audio generation */
  AUDIO_GENERATION: 45_000,

  /** UI reset delay, polling interval */
  UI_RESET: 2_000,
  /** Retry delay between generation attempts */
  RETRY_DELAY: 3_000,
  /** Search input debounce */
  SEARCH_DEBOUNCE: 400,

  /** Browser notification auto-close */
  NOTIFICATION_CLOSE: 10_000,
  /** Notification initial check delay */
  NOTIFICATION_INITIAL: 30_000,
  /** Notification periodic check interval (5 min) */
  NOTIFICATION_INTERVAL: 5 * 60 * 1_000,
} as const;

// Toast durations
export const TOAST_DURATION = {
  SUCCESS: 3_000,
  ERROR: 5_000,
  INFO: 3_000,
  WARNING: 4_000,
} as const;
