# Literary Context System

Connects vocabulary cards to literary works (e.g. Chekhov short stories), providing contextual hints, scene images, and audio for each word.

## Architecture

### Pipeline

```
Word + Source
    |
    v
3-Tier Fragment Search (keyword -> semantic -> LLM)
    |
    v
SceneAnchor enrichment (scene description + image)
    |
    v
Hint text generation (LLM)
    |
    v
Hint audio generation (ElevenLabs -> OpenAI TTS -> gTTS)
    |
    v
WordContextMedia record
```

### Models

| Model | Purpose |
|-------|---------|
| `LiterarySource` | Corpus (e.g. "chekhov", "bible") |
| `LiteraryText` | Individual work within a source |
| `SceneAnchor` | Language-independent scene point; holds image + description |
| `LiteraryFragment` | Language-dependent text passage linked to an anchor |
| `WordContextMedia` | Per-word, per-source generated context (hint, sentences, audio) |
| `DeckContextJob` | Tracks async batch generation progress |
| `LiteraryContextSettings` | Singleton with system-wide defaults |

### Key relationships

- `SceneAnchor` is shared across languages - one image for all translations
- `LiteraryFragment` belongs to both `SceneAnchor` and `LiteraryText`
- `WordContextMedia` links a `Word` to a `LiterarySource` with generated content

## 3-Tier Search (`search.py`)

1. **Keyword match** - Direct word/key_words overlap in fragments
2. **Semantic match** - Cosine similarity on embeddings (threshold from settings)
3. **LLM match** - GPT selects best fragment when tiers 1-2 fail

Returns `(fragment, match_method, match_score)` or `(None, 'none', 0)`.

## Per-User Settings Override

Users can customize AI settings in their profile. `generation.py:_build_effective_config()` overlays non-empty user fields onto `LiteraryContextSettings` defaults:

- **LLM models**: `hint_generation_model`, `scene_description_model`, `matching_model`, `keyword_extraction_model`
- **Temperatures**: `hint_temperature`, `scene_description_temperature`, `matching_temperature`, `keyword_temperature`
- **Prompt templates**: `hint_prompt_template`, `scene_description_prompt`, `keyword_extraction_prompt`, `image_prompt_template`
- **Voice**: `elevenlabs_voice_id`

Empty user values fall back to system defaults.

## Audio Fallback Chain (`audio_generation.py`)

1. **ElevenLabs** - High quality, requires API key + voice ID
2. **OpenAI TTS** - Good quality fallback
3. **gTTS** - Free fallback (Google Translate TTS)

## Image Generation (`image_generation.py`)

Uses Gemini API (`gemini-3.1-flash-image-preview` model) to generate scene illustrations from anchor descriptions.

## API Endpoints

All under `/api/literary-context/`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `sources/` | List active literary sources |
| POST | `generate/` | Generate context for one word |
| POST | `generate-batch/` | Generate context for multiple words |
| POST | `generate-deck-context/` | Generate for entire deck (sync) |
| POST | `generate-deck-context-async/` | Start async deck generation job |
| GET | `job/<uuid>/status/` | Poll async job progress |
| GET | `word/<id>/media/` | Get word's context media |
| GET | `sources/<slug>/texts/` | List texts in a source (reader) |
| GET | `sources/<slug>/texts/<slug>/` | Get full text (reader) |
| POST | `word-from-reader/` | Create word card from reader selection |

### Async Job Flow

```
POST generate-deck-context-async/ {deck_id, source_slug}
  -> 202 {job_id: "uuid"}

GET job/<uuid>/status/
  -> {status: "running", progress: 45, current_word: "Hund"}
  -> {status: "completed", progress: 100, stats: {...}}
```

## Corpus Processing (`corpus_processing.py`)

- Fragment splitting with configurable size/overlap
- Keyword extraction per fragment via LLM
- Scene description generation via LLM
- Embedding generation for semantic search

## Management Commands

- `generate_scene_images` - Generate images for anchors missing them
- `index_corpus` - Split texts into fragments and generate keywords/embeddings

## Testing

```bash
cd backend && python -m pytest apps/literary_context/tests/ -v
```

Test files cover: generation pipeline, search tiers, image generation (Gemini mocks), overlay/serializer, async views, user settings override, audio generation.
