/**
 * Logger utility — only outputs in development mode.
 * Replaces direct console.log/warn/error calls throughout the app.
 */

const isDev = import.meta.env?.DEV ?? false;

export const logger = {
  log(...args: unknown[]) {
    if (isDev) console.log(...args);
  },
  warn(...args: unknown[]) {
    if (isDev) console.warn(...args);
  },
  error(...args: unknown[]) {
    if (isDev) console.error(...args);
  },
  debug(...args: unknown[]) {
    if (isDev) console.debug(...args);
  },
  info(...args: unknown[]) {
    if (isDev) console.info(...args);
  },
};
