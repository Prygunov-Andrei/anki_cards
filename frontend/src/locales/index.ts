import { ru, TranslationKeys } from './ru';
import { en } from './en';
import { pt } from './pt';
import { de } from './de';
import { es } from './es';
import { fr } from './fr';
import { it } from './it';

/**
 * Поддерживаемые языки интерфейса - все 7 языков
 * 
 * ✅ Полностью поддерживаются бэкендом и фронтендом
 * 
 * Поддерживаемые языки:
 * - ru (Русский)
 * - en (English) 
 * - pt (Português)
 * - de (Deutsch)
 * - es (Español)
 * - fr (Français)
 * - it (Italiano)
 */
export const translations: Record<string, TranslationKeys> = {
  ru,
  en,
  pt,
  de,
  es,
  fr,
  it,
};

export type SupportedLocale = keyof typeof translations;

export { TranslationKeys } from './ru';