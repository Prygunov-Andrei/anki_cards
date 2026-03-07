import React, { createContext, useContext, useReducer, useEffect, useCallback, ReactNode } from 'react';
import { useAuthContext } from './AuthContext';

/**
 * Пара слово-перевод (совместима с TranslationTable)
 */
export interface DraftTranslationPair {
  word: string;
  translation: string;
}

/**
 * Состояние черновика колоды — персистируется в localStorage
 */
export interface DraftDeckState {
  words: string[];
  translations: DraftTranslationPair[];
  wordIds: Record<string, number>;
  generatedImages: Record<string, string>;
  generatedAudio: Record<string, string>;
  deckName: string;
  generateImages: boolean;
  generateAudio: boolean;
  literarySourceSlug: string | null;
}

const INITIAL_STATE: DraftDeckState = {
  words: [],
  translations: [],
  wordIds: {},
  generatedImages: {},
  generatedAudio: {},
  deckName: '',
  generateImages: true,
  generateAudio: true,
  literarySourceSlug: null,
};

// Actions
type DraftAction =
  | { type: 'SET_WORDS'; payload: string[] }
  | { type: 'SET_TRANSLATIONS'; payload: DraftTranslationPair[] }
  | { type: 'SET_WORD_IDS'; payload: Record<string, number> }
  | { type: 'SET_GENERATED_IMAGES'; payload: Record<string, string> }
  | { type: 'SET_GENERATED_AUDIO'; payload: Record<string, string> }
  | { type: 'SET_DECK_NAME'; payload: string }
  | { type: 'SET_GENERATE_IMAGES'; payload: boolean }
  | { type: 'SET_GENERATE_AUDIO'; payload: boolean }
  | { type: 'SET_LITERARY_SOURCE'; payload: string | null }
  | { type: 'HYDRATE'; payload: DraftDeckState }
  | { type: 'CLEAR' };

function draftReducer(state: DraftDeckState, action: DraftAction): DraftDeckState {
  switch (action.type) {
    case 'SET_WORDS':
      return { ...state, words: action.payload };
    case 'SET_TRANSLATIONS':
      return { ...state, translations: action.payload };
    case 'SET_WORD_IDS':
      return { ...state, wordIds: action.payload };
    case 'SET_GENERATED_IMAGES':
      return { ...state, generatedImages: action.payload };
    case 'SET_GENERATED_AUDIO':
      return { ...state, generatedAudio: action.payload };
    case 'SET_DECK_NAME':
      return { ...state, deckName: action.payload };
    case 'SET_GENERATE_IMAGES':
      return { ...state, generateImages: action.payload };
    case 'SET_GENERATE_AUDIO':
      return { ...state, generateAudio: action.payload };
    case 'SET_LITERARY_SOURCE':
      return { ...state, literarySourceSlug: action.payload };
    case 'HYDRATE':
      return { ...action.payload };
    case 'CLEAR':
      return { ...INITIAL_STATE };
    default:
      return state;
  }
}

// Context
interface DraftDeckContextType {
  // State
  words: string[];
  translations: DraftTranslationPair[];
  wordIds: Record<string, number>;
  generatedImages: Record<string, string>;
  generatedAudio: Record<string, string>;
  deckName: string;
  generateImages: boolean;
  generateAudio: boolean;
  literarySourceSlug: string | null;
  hasDraft: boolean;

  // Setters
  setWords: (words: string[]) => void;
  setTranslations: (translations: DraftTranslationPair[]) => void;
  setWordIds: (wordIds: Record<string, number>) => void;
  setGeneratedImages: (images: Record<string, string>) => void;
  setGeneratedAudio: (audio: Record<string, string>) => void;
  setDeckName: (name: string) => void;
  setGenerateImages: (value: boolean) => void;
  setGenerateAudio: (value: boolean) => void;
  setLiterarySourceSlug: (slug: string | null) => void;

  // Functional updaters (for prev => next pattern)
  updateGeneratedImages: (updater: (prev: Record<string, string>) => Record<string, string>) => void;
  updateGeneratedAudio: (updater: (prev: Record<string, string>) => Record<string, string>) => void;

  // Actions
  clearDraft: () => void;
}

const DraftDeckContext = createContext<DraftDeckContextType | undefined>(undefined);

function getStorageKey(userId: number | undefined): string {
  return `draft_deck_v1_${userId || 'anon'}`;
}

function loadFromStorage(userId: number | undefined): DraftDeckState | null {
  try {
    const raw = localStorage.getItem(getStorageKey(userId));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Validate shape
    if (typeof parsed === 'object' && Array.isArray(parsed.words)) {
      return { ...INITIAL_STATE, ...parsed };
    }
    return null;
  } catch {
    return null;
  }
}

function saveToStorage(userId: number | undefined, state: DraftDeckState): void {
  try {
    localStorage.setItem(getStorageKey(userId), JSON.stringify(state));
  } catch {
    // localStorage full or unavailable — silently ignore
  }
}

function removeFromStorage(userId: number | undefined): void {
  try {
    localStorage.removeItem(getStorageKey(userId));
  } catch {
    // ignore
  }
}

export const DraftDeckProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuthContext();
  const userId = user?.id;

  const [state, dispatch] = useReducer(draftReducer, INITIAL_STATE);
  const hydratedRef = React.useRef(false);

  // Hydrate from localStorage on mount / user change
  useEffect(() => {
    const saved = loadFromStorage(userId);
    if (saved && (saved.words.length > 0 || Object.keys(saved.generatedImages).length > 0)) {
      dispatch({ type: 'HYDRATE', payload: saved });
    }
    hydratedRef.current = true;
  }, [userId]);

  // Persist to localStorage on state change (debounced)
  useEffect(() => {
    if (!hydratedRef.current) return;

    const timer = setTimeout(() => {
      saveToStorage(userId, state);
    }, 100);
    return () => clearTimeout(timer);
  }, [state, userId]);

  // Setters
  const setWords = useCallback((words: string[]) => {
    dispatch({ type: 'SET_WORDS', payload: words });
  }, []);

  const setTranslations = useCallback((translations: DraftTranslationPair[]) => {
    dispatch({ type: 'SET_TRANSLATIONS', payload: translations });
  }, []);

  const setWordIds = useCallback((wordIds: Record<string, number>) => {
    dispatch({ type: 'SET_WORD_IDS', payload: wordIds });
  }, []);

  const setGeneratedImages = useCallback((images: Record<string, string>) => {
    dispatch({ type: 'SET_GENERATED_IMAGES', payload: images });
  }, []);

  const setGeneratedAudio = useCallback((audio: Record<string, string>) => {
    dispatch({ type: 'SET_GENERATED_AUDIO', payload: audio });
  }, []);

  const setDeckName = useCallback((name: string) => {
    dispatch({ type: 'SET_DECK_NAME', payload: name });
  }, []);

  const setGenerateImages = useCallback((value: boolean) => {
    dispatch({ type: 'SET_GENERATE_IMAGES', payload: value });
  }, []);

  const setGenerateAudio = useCallback((value: boolean) => {
    dispatch({ type: 'SET_GENERATE_AUDIO', payload: value });
  }, []);

  const setLiterarySourceSlug = useCallback((slug: string | null) => {
    dispatch({ type: 'SET_LITERARY_SOURCE', payload: slug });
  }, []);

  // Functional updaters for generated media (prev => next pattern)
  const updateGeneratedImages = useCallback(
    (updater: (prev: Record<string, string>) => Record<string, string>) => {
      dispatch({ type: 'SET_GENERATED_IMAGES', payload: updater(state.generatedImages) });
    },
    [state.generatedImages]
  );

  const updateGeneratedAudio = useCallback(
    (updater: (prev: Record<string, string>) => Record<string, string>) => {
      dispatch({ type: 'SET_GENERATED_AUDIO', payload: updater(state.generatedAudio) });
    },
    [state.generatedAudio]
  );

  const clearDraft = useCallback(() => {
    dispatch({ type: 'CLEAR' });
    removeFromStorage(userId);
  }, [userId]);

  const hasDraft = state.words.length > 0
    || state.translations.length > 0
    || Object.keys(state.generatedImages).length > 0;

  const value: DraftDeckContextType = {
    ...state,
    hasDraft,
    setWords,
    setTranslations,
    setWordIds,
    setGeneratedImages,
    setGeneratedAudio,
    setDeckName,
    setGenerateImages,
    setGenerateAudio,
    setLiterarySourceSlug,
    updateGeneratedImages,
    updateGeneratedAudio,
    clearDraft,
  };

  return <DraftDeckContext.Provider value={value}>{children}</DraftDeckContext.Provider>;
};

export function useDraftDeck(): DraftDeckContextType {
  const context = useContext(DraftDeckContext);
  if (!context) {
    throw new Error('useDraftDeck must be used within a DraftDeckProvider');
  }
  return context;
}
