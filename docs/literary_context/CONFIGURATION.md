# Literary Context Configuration

All parameters are managed via the `LiteraryContextSettings` singleton, editable in Django admin at `/admin/literary_context/literarycontextsettings/`.

## Matching Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `semantic_match_min_score` | 0.7 | Minimum cosine similarity for Tier B semantic search (0.0-1.0) |
| `llm_match_enabled` | True | Enable Tier C LLM-based matching |

## LLM Models

| Parameter | Default | Description |
|-----------|---------|-------------|
| `keyword_extraction_model` | gpt-4o-mini | Model for keyword extraction during indexing |
| `scene_description_model` | gpt-4o-mini | Model for scene description generation |
| `hint_generation_model` | gpt-4o-mini | Model for hint text generation |
| `matching_model` | gpt-4o | Model for Tier C LLM matching |
| `embedding_model` | text-embedding-3-small | Model for vector embeddings |
| `embedding_dimensions` | 1536 | Embedding vector dimensions |

## Temperature Settings

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `hint_temperature` | 0.8 | Higher = more creative hints |
| `keyword_temperature` | 0.3 | Lower = more consistent keyword extraction |
| `scene_description_temperature` | 0.5 | Balanced for scene descriptions |
| `matching_temperature` | 0.2 | Low = more deterministic matching |

## Token Costs (internal units)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `scene_image_cost` | 4 | Cost for DALL-E scene image |
| `hint_generation_cost` | 2 | Cost for hint text via LLM |
| `audio_generation_cost` | 2 | Cost for ElevenLabs audio |
| `llm_matching_cost` | 2 | Cost for Tier C matching |

## Fragment Splitting

| Parameter | Default | Description |
|-----------|---------|-------------|
| `default_fragment_size` | 500 | Target fragment size in characters |
| `fragment_overlap` | 50 | Overlap between consecutive fragments |

## Prompt Templates

All prompts support variable substitution:

- `image_prompt_template`: Variables: `{scene_description}`
- `hint_prompt_template`: Variables: `{fragment_content}`, `{word}`, `{translation}`, `{language_name}`
- `keyword_extraction_prompt`: Variables: `{fragment_content}`
- `scene_description_prompt`: Variables: `{fragment_content}`
- `sentence_extraction_prompt`: Variables: `{word}`, `{fragment_content}`

## Cache

Settings are cached for 5 minutes (300 seconds). Cache is automatically invalidated on save.

To manually clear:
```python
from django.core.cache import cache
cache.delete('literary_context_settings')
```
