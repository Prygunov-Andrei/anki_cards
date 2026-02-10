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

export type LearningStatus = 'new' | 'learning' | 'reviewing' | 'mastered';

export type PartOfSpeech = 
  | 'noun' 
  | 'verb' 
  | 'adjective' 
  | 'adverb' 
  | 'pronoun' 
  | 'preposition' 
  | 'conjunction' 
  | 'interjection' 
  | 'article' 
  | 'numeral' 
  | 'particle' 
  | 'other';

export interface WordSentence {
  id?: number;
  sentence: string;
  translation?: string;
  audio_file?: string | null;
  source?: 'ai' | 'user'; // Для фронтенда, не сохраняется на бекенд
}

export interface Word {
  id: number;
  unique_id?: string;  // Составной ключ "word-{id}-{card_type}" для React-key
  card_id?: number | null;  // ID карточки (Card) в БД
  original_word: string;
  translation: string;
  language: string;
  card_type?: 'normal' | 'inverted' | 'empty';
  audio_file: string | null;
  image_file: string | null;
  image_url?: string | null;
  
  // Новые поля
  etymology: string;
  sentences: WordSentence[];
  notes: string;
  hint_text: string;
  hint_audio: string | null;
  part_of_speech: PartOfSpeech | '';
  stickers: string[];  // ["❤️", "⭐"]
  learning_status: LearningStatus;
  categories?: Array<{ id: number; name: string; icon: string }>;
  
  created_at: string;
  updated_at: string;
}

// Для создания слова (без id и timestamps)
export interface WordCreate {
  original_word: string;
  translation: string;
  language: string;
  audio_file?: File | null;
  image_file?: File | null;
  notes?: string;
  part_of_speech?: PartOfSpeech;
}

// Для обновления слова (все опционально)
export interface WordUpdate {
  original_word?: string;
  translation?: string;
  audio_file?: File | null;
  image_file?: File | null;
  etymology?: string;
  sentences?: WordSentence[];
  notes?: string;
  hint_text?: string;
  hint_audio?: File | null;
  part_of_speech?: PartOfSpeech;
  stickers?: string[];
  learning_status?: LearningStatus;
}

// ========== WORD RELATIONS ==========

export type RelationType = 'synonym' | 'antonym';

export interface WordRelation {
  id: number;
  word_from: number;
  word_to: number;
  word_to_details: Word;
  relation_type: RelationType;
  created_at: string;
}

export interface WordRelationsResponse {
  word_id: number;
  relations: WordRelation[];
  synonyms_count: number;
  antonyms_count: number;
}

export interface AddRelationRequest {
  word_id: number;
}

export interface AddRelationResponse {
  message: string;
  relation: WordRelation;
}

export interface DeleteRelationResponse {
  message: string;
  deleted_count: number;
}

// Расширенный Word с синонимами/антонимами
export interface WordWithRelations extends Word {
  synonyms: Word[];
  antonyms: Word[];
}

// ========== CATEGORY ==========

export interface Category {
  id: number;
  name: string;
  parent: number | null;
  icon: string;
  order: number;
  words_count: number;
  full_path?: string;
  created_at: string;
}

export interface CategoryTree extends Category {
  children: CategoryTree[];
  total_words_count: number;
}

export interface CategoryListItem {
  id: number;
  name: string;
  icon: string;
}

export interface CategoriesResponse {
  count: number;
  categories: CategoryTree[];
}

export interface CategoryCreateRequest {
  name: string;
  parent?: number | null;
  icon?: string;
  order?: number;
}

export interface CategoryUpdateRequest {
  name?: string;
  parent?: number | null;
  icon?: string;
  order?: number;
}

export interface CategoryWordsResponse {
  category_id: number;
  category_name: string;
  include_descendants: boolean;
  count: number;
  words: Word[];
}

export interface WordCategoryRequest {
  category_id: number;
}

// ========== WORDS CATALOG (Stage 8) ==========

export interface WordListItem extends Word {
  next_review: string | null;
  cards_count: number;
  categories: Array<{ id: number; name: string; icon: string }>;
  decks: Array<{
    id: number;
    name: string;
    target_lang: string;
    source_lang: string;
  }>;
}

export interface WordsListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: WordListItem[];
}

export interface WordsListParams {
  language?: string;
  learning_status?: LearningStatus;
  part_of_speech?: string;
  category_id?: number;
  deck_id?: number;
  search?: string;
  has_etymology?: boolean;
  has_hint?: boolean;
  has_sentences?: boolean;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface WordStats {
  word_id: number;
  cards_stats: {
    total_cards: number;
    normal_cards: number;
    inverted_cards: number;
    empty_cards: number;
    cloze_cards: number;
    in_learning_mode: number;
    due_for_review: number;
    mastered: number;
    next_review: string | null;
  };
  learning_status: string;
  has_etymology: boolean;
  has_hint: boolean;
  has_sentences: boolean;
  sentences_count: number;
  relations_count: { synonyms: number; antonyms: number };
  categories_count: number;
  decks_count: number;
}

export interface WordsStats {
  total_words: number;
  by_language: Record<string, number>;
  by_status: Record<string, number>;
  by_part_of_speech: Record<string, number>;
  with_etymology: number;
  with_hint: number;
  with_sentences: number;
  total_cards: number;
  due_for_review: number;
}

export type BulkActionType =
  | 'enter_learning'
  | 'delete'
  | 'add_to_deck'
  | 'add_to_category'
  | 'remove_from_category';

export interface BulkActionRequest {
  word_ids: number[];
  action: BulkActionType;
  params?: { deck_id?: number; category_id?: number };
}

export interface BulkActionResponse {
  action: string;
  processed: number;
  successful: number;
  failed: number;
  errors: Array<{ word_id: number; error: string }>;
}

export interface WordEnterLearningResponse {
  message: string;
  word_id: number;
  cards_updated: number;
  learning_status: string;
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
  [key: string]: unknown;
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
  | 'tr' // Turkish
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

// ═══════════════════════════════════════════════════════════════
// CARD TYPES (Этап 3)
// ═══════════════════════════════════════════════════════════════

export type CardType = 'normal' | 'inverted' | 'empty' | 'cloze';

export interface CardContent {
  text: string | null;
  translation?: string | null;
  image_url: string | null;
  audio_url: string | null;
}

export interface Card {
  id: number;
  word: Word;
  card_type: CardType;
  cloze_sentence: string;
  cloze_word_index: number;
  // SM-2
  ease_factor: number;
  interval: number;
  repetitions: number;
  lapses: number;
  consecutive_lapses: number;
  learning_step: number;
  // Планирование
  next_review: string | null;
  last_review: string | null;
  // Статусы
  is_in_learning_mode: boolean;
  is_auxiliary: boolean;
  is_suspended: boolean;
  // Контент
  front_content: CardContent;
  back_content: CardContent;
  is_due: boolean;
  // Мета
  created_at: string;
  updated_at: string;
}

export interface CardListItem {
  id: number;
  card_type: CardType;
  word_id: number;
  word_text: string;
  word_translation: string;
  image_file?: string | null;
  audio_file?: string | null;
  interval: number;
  ease_factor: number;
  next_review: string | null;
  is_in_learning_mode: boolean;
  is_auxiliary: boolean;
  is_suspended: boolean;
  is_due: boolean;
}

export interface CardCreateClozeRequest {
  sentence: string;
  word_index?: number;
}

export interface CardReview {
  id: number;
  card_type: CardType;
  front_content: CardContent;
  is_in_learning_mode: boolean;
}

export interface CardAnswer {
  id: number;
  card_type: CardType;
  front_content: CardContent;
  back_content: CardContent;
  is_in_learning_mode: boolean;
  word_etymology: string;
  word_notes: string;
  word_hint_text: string;
  word_sentences: Array<{ text: string; source: string }>;
}

// ═══════════════════════════════════════════════════════════════
// TRAINING SETTINGS TYPES (Этап 4)
// ═══════════════════════════════════════════════════════════════

export type AgeGroup = 'young' | 'adult' | 'senior';

export interface UserTrainingSettings {
  // Основное
  age_group: AgeGroup;
  age_group_display: string;
  
  // Ease Factor
  starting_ease: number;
  min_ease_factor: number;
  
  // Дельты EF
  again_ef_delta: number;
  hard_ef_delta: number;
  good_ef_delta: number;
  easy_ef_delta: number;
  
  // Модификаторы интервалов
  interval_modifier: number;
  hard_interval_modifier: number;
  easy_bonus: number;
  
  // Шаги обучения
  learning_steps: number[];
  graduating_interval: number;
  easy_interval: number;
  
  // Настройки сессии
  default_session_duration: number;
  
  // Пороги
  lapse_threshold: number;
  stability_threshold: number;
  calibration_interval: number;
  target_retention: number;
  
  // Калибровка (read-only)
  total_reviews: number;
  successful_reviews: number;
  last_calibration_at: number;
  
  // Мета
  created_at: string;
  updated_at: string;
}

export interface UserTrainingSettingsUpdate {
  age_group?: AgeGroup;
  starting_ease?: number;
  min_ease_factor?: number;
  again_ef_delta?: number;
  hard_ef_delta?: number;
  good_ef_delta?: number;
  easy_ef_delta?: number;
  interval_modifier?: number;
  hard_interval_modifier?: number;
  easy_bonus?: number;
  learning_steps?: number[];
  graduating_interval?: number;
  easy_interval?: number;
  default_session_duration?: number;
  lapse_threshold?: number;
  stability_threshold?: number;
  calibration_interval?: number;
  target_retention?: number;
}

export interface TrainingSettingsDefaults {
  age_group: AgeGroup;
  starting_ease: number;
  min_ease_factor: number;
  again_ef_delta: number;
  hard_ef_delta: number;
  good_ef_delta: number;
  easy_ef_delta: number;
  interval_modifier: number;
  hard_interval_modifier: number;
  easy_bonus: number;
  learning_steps: number[];
  graduating_interval: number;
  easy_interval: number;
  default_session_duration: number;
  lapse_threshold: number;
  stability_threshold: number;
  calibration_interval: number;
}

// ═══════════════════════════════════════════════════════════════
// TRAINING SESSION TYPES (Этап 10)
// ═══════════════════════════════════════════════════════════════

export type AnswerQuality = 0 | 1 | 2 | 3; // Again, Hard, Good, Easy

export interface TrainingSessionParams {
  deck_id?: number;
  category_id?: number;
  duration?: number;
  new_cards?: boolean;
}

export interface TrainingSessionResponse {
  session_id: string;
  cards: CardListItem[];
  estimated_time: number;
  new_count: number;
  review_count: number;
  learning_count: number;
  total_count: number;
}

export interface TrainingAnswerRequest {
  session_id?: string;
  card_id: number;
  answer: AnswerQuality;
  time_spent?: number;
}

export interface TrainingAnswerResponse {
  card_id: number;
  new_interval: number;
  new_ease_factor: number;
  next_review: string;
  entered_learning_mode: boolean;
  exited_learning_mode: boolean;
  learning_step: number;
  calibrated: boolean;
  card: CardListItem;
}

export interface TrainingStats {
  total_reviews: number;
  successful_reviews: number;
  success_rate: number;
  streak_days: number;
  cards_by_status: {
    learning: number;
    review: number;
    new: number;
    suspended: number;
  };
  reviews_by_day: Array<{
    date: string;
    total: number;
    successful: number;
    success_rate: number;
  }>;
}

// ═══════════════════════════════════════════════════════════════
// TRAINING DASHBOARD TYPES
// ═══════════════════════════════════════════════════════════════

export interface TrainingCardCounts {
  new: number;
  learning: number;
  review: number;
  mastered: number;
  total: number;
  due: number;
}

export interface TrainingDeckInfo {
  id: number;
  name: string;
  cover?: string | null;
  is_learning_active: boolean;
  cards: TrainingCardCounts;
}

export interface TrainingCategoryInfo {
  id: number;
  name: string;
  icon: string;
  parent_id: number | null;
  is_learning_active: boolean;
  cards: TrainingCardCounts;
}

export interface TrainingDashboard {
  quick_stats: {
    streak_days: number;
    success_rate: number;
    total_due: number;
  };
  decks: TrainingDeckInfo[];
  categories: TrainingCategoryInfo[];
  orphans: {
    is_active: boolean;
    cards: TrainingCardCounts;
  };
}

// ═══════════════════════════════════════════════════════════════
// AI GENERATION TYPES (Этап 7)
// ═══════════════════════════════════════════════════════════════

// Запросы для генерации AI контента
export interface GenerateEtymologyRequest {
  word_id: number;
  force_regenerate?: boolean;
}

export interface GenerateHintRequest {
  word_id: number;
  force_regenerate?: boolean;
  generate_audio?: boolean;
}

export interface GenerateSentenceRequest {
  word_id: number;
  count?: number; // 1-5
  context?: string;
}

export interface GenerateSynonymRequest {
  word_id: number;
  create_card?: boolean;
}

// Ответы от API для генерации AI контента
export interface GenerateEtymologyResponse {
  word_id: number;
  etymology: string;
  tokens_spent: number;
  balance_after: number;
}

export interface GenerateHintResponse {
  word_id: number;
  hint_text: string;
  hint_audio_url?: string | null;
  tokens_spent: number;
  balance_after: number;
}

export interface GenerateSentenceResponse {
  word_id: number;
  sentences: string[];
  tokens_spent: number;
  balance_after: number;
}

export interface GenerateSynonymResponse {
  original_word_id: number;
  synonym_word: Word;
  relation_created: boolean;
  tokens_spent: number;
  balance_after: number;
}

// ═══════════════════════════════════════════════════════════════
// Этап 13: Уведомления
// ═══════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════
// Этап 14: Кривые забывания
// ═══════════════════════════════════════════════════════════════

export interface ForgettingCurvePoint {
  interval_days: number;
  label: string;
  retention_rate: number;
  total_cards: number;
  successful: number;
}

export interface TheoreticalCurvePoint {
  day: number;
  retention: number;
}

export interface ForgettingCurveSummary {
  total_reviews: number;
  avg_retention: number;
  current_stability: number;
}

export interface ForgettingCurveResponse {
  points: ForgettingCurvePoint[];
  theoretical_curve: TheoreticalCurvePoint[];
  summary: ForgettingCurveSummary;
}

// ═══════════════════════════════════════════════════════════════
// Этап 13: Уведомления
// ═══════════════════════════════════════════════════════════════

export type NotificationFrequency = 'aggressive' | 'normal' | 'minimal' | 'off';

export interface NotificationSettings {
  browser_notifications_enabled: boolean;
  notification_frequency: NotificationFrequency;
  frequency_display: string;
  notify_cards_due: boolean;
  notify_streak_warning: boolean;
  notify_daily_goal: boolean;
  cards_due_threshold: number;
  quiet_hours_start: string;
  quiet_hours_end: string;
}

export interface NotificationCheckResponse {
  should_notify: boolean;
  cards_due: number;
  streak_at_risk: boolean;
  message: string;
  notification_type: 'cards_due' | 'streak_warning' | 'none';
}