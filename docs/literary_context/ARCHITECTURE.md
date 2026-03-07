# Literary Context Architecture

## Overview

The Literary Context system generates word media (images, audio, hints, example sentences) from real literary works instead of synthetic AI content. Users select a literary source (e.g., Chekhov stories, Bible), and all word media is drawn from actual text passages.

## Data Model

```
LiterarySource (slug, name, source_language, available_languages)
  |
  +-- LiteraryText (slug, title, language, full_text)
  |     |
  |     +-- LiteraryFragment (content, key_words, embedding)
  |           |
  |           +-- anchor -> SceneAnchor
  |
  +-- SceneAnchor (text_slug, fragment_index, scene_description, image_file)
        |
        +-- fragments (LiteraryFragment) -- one per language
        +-- word_media (WordContextMedia)

WordContextMedia (word FK, source FK, anchor FK, fragment FK, hint_text, sentences, match_method)
```

### Key Design Decisions

1. **SceneAnchor** is language-independent. One scene = one image shared across all languages. This avoids generating N duplicate images for N languages.

2. **LiteraryFragment** is language-dependent. Each fragment links to its SceneAnchor, enabling cross-language image sharing.

3. **WordContextMedia** stores the generated media per word per source. The `unique_together = [word, source]` constraint ensures no duplicates.

4. **LiteraryContextSettings** is a singleton (pk=1) with Django cache. All tunable parameters (prompts, models, thresholds, costs) live here, editable via Django admin.

## Word Matching (3-Tier)

```
Word "Hund" -> Tier A: keyword match in key_words JSON
           -> Tier B: semantic similarity via pgvector (if available)
           -> Tier C: LLM-based matching (if enabled)
           -> fallback: is_fallback=True, no overlay
```

- **Tier A**: Always available. Exact match (1.0), partial (0.8), translation (0.7), content contains (0.6).
- **Tier B**: Requires pgvector extension. Cosine distance on OpenAI embeddings.
- **Tier C**: GPT selects best fragment from top-10 candidates. Configurable via `llm_match_enabled`.

## Context Overlay

When `user.active_literary_source` is set, the `LiteraryContextOverlayMixin` on `WordSerializer` overlays:
- `hint_text` from WordContextMedia
- `sentences` from the matched fragment
- `image_file` from the SceneAnchor

The overlay is transparent -- the same API endpoints return different data based on the user's active context.

## Audio Fallback Chain

```
ElevenLabs -> OpenAI TTS -> gTTS
```

Each level has graceful degradation via try/except. `HAS_ELEVENLABS` flag prevents import errors.

## File Layout

```
backend/apps/literary_context/
  models.py           -- 6 models (Source, Text, Anchor, Fragment, Media, Settings)
  search.py           -- 3-tier matching
  generation.py       -- WordContextMedia pipeline
  corpus_processing.py -- text splitting, keyword/scene extraction
  embedding_utils.py  -- OpenAI embeddings
  image_generation.py -- DALL-E scene images
  audio_generation.py -- ElevenLabs/OpenAI/gTTS fallback
  serializers.py      -- DRF serializers
  views.py            -- API endpoints
  admin.py            -- Admin with custom actions
  management/commands/ -- 7 management commands
  tests/              -- 145+ tests
```
