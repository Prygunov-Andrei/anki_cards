// User types
export interface User {
  id: number;
  username: string;
  email: string;
  preferred_language: Language;
}

// Language types
export type Language = 'pt' | 'de';

// Word types
export interface Word {
  id: number;
  original_word: string;
  translation: string;
  language: Language;
  created_at: string;
}

// Card generation types
export type ImageStyle = 'minimalistic' | 'balanced' | 'creative';

export interface CardGenerationRequest {
  words: string;
  language: Language;
  translations: Record<string, string>;
  audio_files?: Record<string, string>;
  image_files?: Record<string, string>;
  deck_name: string;
  image_style?: ImageStyle;
}

export interface CardGenerationResponse {
  file_id: string;
  download_url: string;
  deck_name: string;
  cards_count: number;
}

// API response types
export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
}

export interface AuthResponse {
  token: string;
  user_id: number;
  username?: string;
  email?: string;
  preferred_language?: Language;
}

// Media types
export interface MediaGenerationResponse {
  image_url?: string;
  audio_url?: string;
  image_id?: string;
  audio_id?: string;
  file_path?: string;
  dalle_prompt?: string; // Промпт, отправленный в DALL-E (для отладки)
}

export interface MediaUploadResponse {
  image_url?: string;
  audio_url?: string;
  image_id?: string;
  audio_id?: string;
  file_path?: string;
}

export interface WordMedia {
  word: string;
  imageUrl?: string;
  audioUrl?: string;
  imageId?: string;
  audioId?: string;
  imagePath?: string;
  audioPath?: string;
}

// Prompt types
export type PromptType =
  | 'image'
  | 'audio'
  | 'word_analysis'
  | 'translation'
  | 'deck_name'
  | 'part_of_speech'
  | 'category';

export interface UserPrompt {
  id: number;
  prompt_type: PromptType;
  prompt_type_display: string;
  custom_prompt: string;
  is_custom: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserPromptUpdate {
  custom_prompt: string;
}

