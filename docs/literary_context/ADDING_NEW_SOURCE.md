# Adding a New Literary Source

## Step 1: Prepare Text Files

Create text files in `backend/apps/literary_context/fixtures/<source>/`:

```
backend/apps/literary_context/fixtures/tolstoy/
  anna_karenina_ch1.ru.txt    # Russian original
  anna_karenina_ch1.de.txt    # German translation
  anna_karenina_ch1.en.txt    # English translation
```

File naming: `{text_slug}.{language_code}.txt`

Requirements:
- Plain text (UTF-8)
- Paragraph-separated by double newlines
- 1000+ characters recommended per file
- Parallel texts should cover the same content

## Step 2: Load Texts

```bash
python manage.py load_literary_text \
  --source-slug tolstoy \
  --source-name "Leo Tolstoy" \
  --source-language ru \
  --text-slug anna_karenina_ch1 \
  --title "Anna Karenina, Chapter 1" \
  --language ru \
  --file fixtures/tolstoy/anna_karenina_ch1.ru.txt

# Repeat for each language
python manage.py load_literary_text \
  --source-slug tolstoy \
  --source-name "Leo Tolstoy" \
  --source-language ru \
  --text-slug anna_karenina_ch1 \
  --title "Anna Karenina, Kapitel 1" \
  --language de \
  --file fixtures/tolstoy/anna_karenina_ch1.de.txt
```

## Step 3: Index Texts

```bash
python manage.py index_literary_text \
  --source-slug tolstoy \
  --text-slug anna_karenina_ch1 \
  --language ru \
  --fragment-size 500

python manage.py index_literary_text \
  --source-slug tolstoy \
  --text-slug anna_karenina_ch1 \
  --language de \
  --fragment-size 500
```

This creates SceneAnchors and LiteraryFragments with LLM-extracted keywords and scene descriptions.

## Step 4: Generate Embeddings (Optional)

```bash
python manage.py generate_embeddings --source-slug tolstoy
```

## Step 5: Generate Scene Images

```bash
# Preview first
python manage.py generate_scene_images --source-slug tolstoy --dry-run

# Generate
python manage.py generate_scene_images --source-slug tolstoy --limit 20
```

## Step 6: Verify

```bash
python manage.py literary_context_stats --source-slug tolstoy
```

## Step 7: Create Convenience Command (Optional)

Create `management/commands/load_tolstoy_corpus.py` modeled after `load_chekhov_corpus.py`.

## Quality Checklist

- [ ] Texts are in plain UTF-8
- [ ] Parallel texts align by content
- [ ] Source has `is_active=True` in DB
- [ ] At least one language indexed with keywords
- [ ] Scene descriptions generated (check admin)
- [ ] Stats command shows expected counts
- [ ] Test word search returns matches
