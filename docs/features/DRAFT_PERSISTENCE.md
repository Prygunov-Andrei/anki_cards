# Draft Persistence

## Overview

The word creation flow (MainPage) persists all user progress across navigation, tab switching, and page refresh. Three stages survive any user action:

1. **Word chips** - entered/extracted words
2. **Translations** - auto-translated or manually entered pairs
3. **Generated media** - images and audio URLs

## Architecture

### DraftDeckContext (`frontend/src/contexts/DraftDeckContext.tsx`)

React Context with `useReducer` + localStorage persistence.

**Persisted state:**
- `words: string[]` - word chips
- `translations: WordTranslationPair[]` - word-translation pairs
- `wordIds: Record<string, number>` - word -> backend Word.id mapping
- `generatedImages: Record<string, string>` - word -> image URL
- `generatedAudio: Record<string, string>` - word -> audio URL
- `deckName: string`
- `generateImages: boolean`
- `generateAudio: boolean`
- `literarySourceSlug: string | null`

**NOT persisted (transient):**
- isGenerating, abortController, generationProgress, generationStatus

**Storage key:** `draft_deck_v1_${userId}` (scoped per user)

**Sync:** `useEffect` with 100ms debounce writes state to localStorage on every change.

### Backend Endpoints

**`POST /api/words/bulk-create/`**
- Creates words via `get_or_create` (unique: user + original_word + language)
- Returns `id`, `is_new`, `has_image`, `has_audio`, `image_url`, `audio_url`
- Called after auto-translate to persist words immediately

**`POST /api/words/check-media/`**
- Checks media status for given word IDs (filtered by user)
- Used on mount to restore media state from server

### Media Generation Resumption

When "Magic" is clicked, the system:
1. Filters out words that already have images/audio
2. Only generates media for words missing it
3. Uses `checkMedia()` on mount to sync with server state

### Navigation Protection

- `beforeunload` event prevents accidental tab close during generation
- React Router `useBlocker` shows confirmation dialog during generation
- Outside of generation, navigation is free (data is in localStorage)

### Draft UI

- Toast notification on draft restoration ("N words loaded from draft")
- "Clear all" button with confirmation dialog
- Orange badge dot on "Create" nav item when draft exists

### Deck.literary_source

The Deck model has a `literary_source` FK that saves the active literary source when creating a deck. This preserves the "cover" (literary style) selection.

## Flow

1. User enters words -> saved to localStorage
2. User translates -> saved to localStorage + bulk-created on backend
3. User generates media -> progress saved incrementally
4. User navigates away -> data persists
5. User returns -> draft restored from localStorage, media checked against server
6. User downloads .apkg -> `clearDraft()` clears localStorage
