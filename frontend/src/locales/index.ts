import { ru } from './ru';
import type { TranslationKeys } from './ru';
import { en } from './en';
import { pt } from './pt';
import { de } from './de';
import { es } from './es';
import { fr } from './fr';
import { it } from './it';
import { tr } from './tr';

/**
 * Поддерживаемые языки интерфейса - все 8 языков
 * 
 * Полностью поддерживаются бэкендом и фронтендом
 * 
 * Поддерживаемые языки:
 * - ru (Русский)
 * - en (English) 
 * - pt (Português)
 * - de (Deutsch)
 * - es (Español)
 * - fr (Français)
 * - it (Italiano)
 * - tr (Türkçe)
 */
export const translations: Record<string, TranslationKeys> = {
  ru,
  en,
  pt,
  de,
  es,
  fr,
  it,
  tr,
};

export type SupportedLocale = keyof typeof translations;

export type { TranslationKeys } from './ru';