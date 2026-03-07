# Literary Context API

All endpoints require authentication.

## Endpoints

### GET /api/literary-context/sources/

List active literary sources.

**Response:**
```json
[
  {
    "slug": "chekhov",
    "name": "Chekhov Stories",
    "description": "Short stories by Anton Chekhov",
    "cover": "/media/literary_sources/chekhov.jpg",
    "source_language": "ru",
    "available_languages": ["ru", "de", "en"],
    "is_active": true
  }
]
```

### POST /api/literary-context/generate/

Generate literary context for a single word.

**Request:**
```json
{
  "word_id": 42,
  "source_slug": "chekhov"
}
```

**Response (201):**
```json
{
  "id": 1,
  "word": 42,
  "source": "chekhov",
  "anchor": {
    "scene_description": "A town square...",
    "mood": "comedic",
    "image_url": "/media/literary_scenes/abc.jpg"
  },
  "hint_text": "Think of the scene at the market...",
  "sentences": [{"text": "Der Hund lief...", "source": "chekhov"}],
  "is_fallback": false,
  "match_method": "keyword",
  "match_score": 1.0
}
```

### POST /api/literary-context/generate-batch/

Generate context for multiple words.

**Request:**
```json
{
  "word_ids": [42, 43, 44],
  "source_slug": "chekhov",
  "skip_existing": true
}
```

**Response:**
```json
{
  "total": 3,
  "generated": 2,
  "skipped": 1,
  "fallback": 0,
  "errors": 0
}
```

### GET /api/literary-context/word/{word_id}/media/

Get all context media for a word (across all sources).

**Response:**
```json
[
  {
    "id": 1,
    "source": "chekhov",
    "hint_text": "...",
    "sentences": [...],
    "is_fallback": false,
    "match_method": "keyword",
    "match_score": 1.0
  }
]
```

## Context Overlay

When `user.active_literary_source` is set, `GET /api/words/{id}/` responses include:

```json
{
  "id": 42,
  "original_word": "Hund",
  "hint_text": "Overlaid hint from Chekhov...",
  "sentences": [{"text": "...", "source": "chekhov"}],
  "image_file": "/media/literary_scenes/abc.jpg",
  "literary_context": {
    "source_slug": "chekhov",
    "scene_description": "A town square...",
    "is_fallback": false,
    "match_method": "keyword",
    "image_url": "/media/literary_scenes/abc.jpg"
  }
}
```

Switch context via `PATCH /api/auth/profile/`:

```json
{"active_literary_source": "chekhov"}
```

Clear context:

```json
{"active_literary_source": null}
```
