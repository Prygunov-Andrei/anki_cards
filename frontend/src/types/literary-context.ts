export interface LiterarySource {
  slug: string;
  name: string;
  description: string;
  cover: string | null;
  available_languages: string[];
  is_active: boolean;
}

export interface LiteraryContextInfo {
  source_slug: string;
  hint_text: string;
  sentences: Array<{ text: string; source: string }>;
  scene_description: string;
  match_method: 'keyword' | 'semantic' | 'llm' | 'none';
  is_fallback: boolean;
  image_url: string | null;
}

export interface WordContextMedia {
  id: number;
  source: LiterarySource;
  anchor: {
    id: number;
    scene_description: string;
    characters: string[];
    mood: string;
    image_file: string | null;
  } | null;
  hint_text: string;
  hint_audio: string | null;
  sentences: Array<{ text: string; source: string }>;
  audio_file: string | null;
  is_fallback: boolean;
  match_method: string;
  match_score: number | null;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface GenerateContextRequest {
  word_id: number;
  source_slug: string;
}

export interface GenerateBatchContextRequest {
  word_ids: number[];
  source_slug: string;
  skip_existing?: boolean;
}

export interface BatchContextStats {
  total: number;
  generated: number;
  skipped: number;
  fallback: number;
  errors: number;
  unmatched_words?: Array<{
    id: number;
    original_word: string;
    translation: string;
  }>;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_word: string;
  stats: BatchContextStats;
  unmatched_words: Array<{
    id: number;
    original_word: string;
    translation: string;
  }>;
  error_message: string;
}
