# Literary Context Setup

## Prerequisites

- Python 3.9+, Django 4.2+
- PostgreSQL (production) or SQLite (development)
- OpenAI API key (`OPENAI_API_KEY`)
- Optional: ElevenLabs API key (`ELEVENLABS_API_KEY`)
- Optional: pgvector extension (for Tier B semantic search)

## Quick Start

### 1. Run migrations

```bash
cd backend
python manage.py migrate
```

### 2. Load a test corpus

```bash
# Load Chekhov sample texts
python manage.py load_chekhov_corpus

# Or load individual texts
python manage.py load_literary_text \
  --source-slug chekhov \
  --source-name "Chekhov Stories" \
  --source-language ru \
  --text-slug hameleon \
  --title "Hameleon" \
  --language ru \
  --file data/literary_sources/chekhov/hameleon.ru.txt
```

### 3. Index texts (creates SceneAnchors + Fragments + keywords)

```bash
python manage.py index_literary_text \
  --source-slug chekhov \
  --text-slug hameleon \
  --language ru

# Use --skip-llm to skip LLM calls (keywords and scene descriptions will be empty)
python manage.py index_literary_text \
  --source-slug chekhov \
  --text-slug hameleon \
  --language ru \
  --skip-llm
```

### 4. Generate embeddings (optional, requires pgvector)

```bash
python manage.py generate_embeddings --source-slug chekhov
```

### 5. Generate scene images (optional, costs tokens)

```bash
python manage.py generate_scene_images --source-slug chekhov --limit 5
```

### 6. Generate word contexts

```bash
python manage.py generate_batch_context \
  --source-slug chekhov \
  --user-id 1 \
  --language de
```

### 7. Check stats

```bash
python manage.py literary_context_stats
```

## pgvector Setup (Optional)

For Tier B semantic search, install pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Install the Python package:

```bash
pip install pgvector django-pgvector
```

The system gracefully degrades without pgvector -- Tier B is simply skipped.

## Running Tests

```bash
cd backend
python -m pytest apps/literary_context/tests/ -v
```
