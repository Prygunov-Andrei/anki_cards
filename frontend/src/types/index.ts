/**
 * TypeScript типы для проекта ANKI Generator
 */

// ========== USER ==========

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  avatar?: string | null;
  native_language?: string;
  learning_language?: string;
  theme?: 'light' | 'dark';
  mode?: 'simple' | 'advanced';
  image_provider?: 'openai' | 'gemini' | 'nano-banana'; // Провайдер генерации изображений
  gemini_model?: 'gemini-2.5-flash-image' | 'nano-banana-pro-preview'; // Модель Gemini для генерации изображений (deprecated, используется image_provider)
  audio_provider?: 'openai' | 'gtts'; // Провайдер генерации аудио
}

// ========== WORD ==========

export interface Word {
  id: number;
  original_word: string;
  translation: string;
  language: string;
  audio_file: string | null;
  image_file: string | null;
  card_type?: 'normal' | 'inverted' | 'empty';
}

// ========== DECK ==========

export interface Deck {
  id: number;
  name: string;
  cover: string | null;
  target_lang?: string; // Может быть undefined при загрузке
  source_lang?: string; // Может быть undefined при загрузке
  words?: Word[]; // Может быть undefined при загрузке
  words_count: number; // Общее количество карточек
  unique_words_count?: number; // Количество уникальных слов (normal + inverted, без empty)
  created_at: string;
  updated_at: string;
}

// ========== API RESPONSES ==========

export interface AuthResponse {
  token: string;
  user: User;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  native_language: string;
  learning_language: string;
}

export interface ApiError {
  detail?: string;
  message?: string;
  [key: string]: any;
}

// ========== DECK GENERATION ==========

export interface DeckGenerationRequest {
  topic: string;
  words_count: number;
  target_lang: string;
  source_lang: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
}

export interface DeckGenerationResponse {
  deck_id: number;
  status: 'processing' | 'completed' | 'failed';
  message: string;
}

// ========== LANGUAGES ==========

export type SupportedLanguage = 
  | 'en' // English
  | 'ru' // Russian
  | 'es' // Spanish
  | 'fr' // French
  | 'de' // German
  | 'it' // Italian
  | 'pt' // Portuguese
  | 'zh' // Chinese
  | 'ja' // Japanese
  | 'ko'; // Korean

export interface Language {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  flag: string;
}

// ========== TOKENS ==========

export interface TokenBalance {
  balance: number; // Теперь может быть дробным (например, 5.5)
}

export interface TokenTransaction {
  id: number;
  transaction_type: 'earned' | 'spent' | 'refund';
  amount: number; // Теперь может быть дробным (например, -0.5 или +1.0)
  description: string;
  created_at: string;
}

// ========== IMAGE GENERATION ==========

export interface ImageGenerationRequest {
  word: string;
  translation: string;
  language: 'pt' | 'de' | 'en' | 'es' | 'fr' | 'it' | 'zh' | 'ja' | 'ko';
  image_style?: 'minimalistic' | 'balanced' | 'creative';
  provider?: 'openai' | 'gemini';
  gemini_model?: 'gemini-2.5-flash-image' | 'nano-banana-pro-preview';
  word_id?: number;
}

export interface ImageGenerationResponse {
  image_url: string;
  word: string;
}

// Типы моделей Gemini
export type GeminiModel = 'gemini-2.5-flash-image' | 'nano-banana-pro-preview';

// Информация о модели Gemini
export interface GeminiModelInfo {
  id: GeminiModel;
  name: string;
  description: string;
  cost: number; // Стоимость в токенах
  speed: string; // Время генерации
  icon: string; // Emoji иконка
}