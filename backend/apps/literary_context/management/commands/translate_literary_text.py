"""
Translate a single literary text from Russian to German using OpenAI.

3-stage pipeline:
  A) Translation with literary quality prompt
  B) Verification (another LLM call checks quality)
  C) Stylistic pass (whole-story review, optional)

Checkpoint/resume: each chunk saved to .partial.json immediately.

Usage:
    python manage.py translate_literary_text \\
        --source-file fixtures/chekhov/originals/hameleon.ru.txt \\
        --output-file fixtures/chekhov/translations/hameleon.de.txt \\
        --model gpt-4.1 --verify --stylistic-pass

    # Resume interrupted translation:
    python manage.py translate_literary_text \\
        --source-file fixtures/chekhov/originals/hameleon.ru.txt \\
        --output-file fixtures/chekhov/translations/hameleon.de.txt \\
        --resume
"""
import json
import re
import time
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.cards.llm_utils import get_openai_client

DEFAULT_MODEL = 'gpt-4.1'
DEFAULT_CHUNK_SIZE = 3000  # chars per chunk
MAX_RETRIES = 3
RETRY_DELAYS = [2, 8, 32]

# --- Prompts ---

TRANSLATE_SYSTEM = """Ты — профессиональный литературный переводчик с русского на немецкий с 30-летним опытом.
Ты переводишь рассказ «{title}» Антона Чехова.

ПРИНЦИПЫ ПЕРЕВОДА:
1. Современный живой Hochdeutsch — никакого канцелярита и архаизмов
2. Сохраняй ритм Чехова: короткие ёмкие предложения, без многословия
3. Диалоги должны звучать как живая немецкая речь, не как подстрочник
4. Русские реалии (самовар, дрожки, городовой) — транскрибируй, не объясняй
5. Ирония и подтекст Чехова — ВАЖНЕЕ буквальной точности
6. Читатель НЕ должен чувствовать, что это перевод
7. Сохраняй абзацную структуру оригинала

{name_glossary}"""

TRANSLATE_USER = """Предыдущий контекст (для связности):
{previous_context}

ТЕКСТ ДЛЯ ПЕРЕВОДА:
{chunk}

Верни ТОЛЬКО немецкий перевод. Ничего больше."""

VERIFY_SYSTEM = """Ты — редактор немецкого литературного издательства. Сравни перевод с оригиналом.

ПРОВЕРЬ:
1. Ничего не пропущено и не добавлено?
2. Стиль — живой немецкий, не «переводческий»?
3. Ирония и подтекст Чехова сохранены?
4. Нет грамматических ошибок?

ВАЖНО: Ответь ТОЛЬКО одним из двух вариантов:
- Если всё хорошо: верни РОВНО одно слово FREIGEGEBEN
- Если есть проблемы: верни ТОЛЬКО исправленный немецкий текст, БЕЗ комментариев, БЕЗ объяснений, БЕЗ нумерованных списков. Только чистый исправленный перевод."""

VERIFY_USER = """ОРИГИНАЛ:
{original}

ПЕРЕВОД:
{translation}"""

STYLISTIC_SYSTEM = """Прочитай этот немецкий перевод рассказа Чехова целиком.
Проверь единство стиля, естественность переходов между абзацами,
и общее впечатление. Это должно читаться как НЕМЕЦКАЯ литература,
а не как перевод. Исправь только то, что действительно нуждается в правке.
Если текст безупречен — верни его без изменений.

ПОЛНЫЙ ТЕКСТ:"""


def split_into_chunks(text: str, chunk_size: int) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para_size = len(para) + 1  # +1 for newline
        if current_size + para_size > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks


def call_llm(client, model: str, system: str, user: str, temperature: float = 0.7,
             max_tokens: int = 8000) -> str:
    """Call OpenAI with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_str = str(e).lower()
            if attempt < MAX_RETRIES - 1:
                if 'rate_limit' in error_str or '429' in error_str:
                    delay = RETRY_DELAYS[attempt]
                    time.sleep(delay)
                    continue
                if 'timeout' in error_str:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
            raise


class Command(BaseCommand):
    help = 'Translate a literary text from Russian to German using OpenAI'

    def add_arguments(self, parser):
        parser.add_argument('--source-file', type=str, required=True)
        parser.add_argument('--output-file', type=str, required=True)
        parser.add_argument('--model', type=str, default=DEFAULT_MODEL)
        parser.add_argument('--chunk-size', type=int, default=DEFAULT_CHUNK_SIZE)
        parser.add_argument('--verify', action='store_true',
                            help='Run verification pass on each chunk')
        parser.add_argument('--stylistic-pass', action='store_true',
                            help='Run final stylistic review on whole text')
        parser.add_argument('--resume', action='store_true',
                            help='Resume from checkpoint')
        parser.add_argument('--title', type=str, default='',
                            help='Story title for the prompt')
        parser.add_argument('--glossary-file', type=str, default=None,
                            help='Path to name glossary JSON')
        parser.add_argument('--temperature', type=float, default=0.7)

    def handle(self, *args, **options):
        source_path = Path(options['source_file'])
        output_path = Path(options['output_file'])
        model = options['model']
        chunk_size = options['chunk_size']
        do_verify = options['verify']
        do_stylistic = options['stylistic_pass']
        resume = options['resume']
        title = options['title'] or source_path.stem.replace('.ru', '')
        temperature = options['temperature']

        partial_path = output_path.with_suffix('.partial.json')

        # Load glossary
        glossary_text = ''
        if options['glossary_file']:
            glossary_path = Path(options['glossary_file'])
            if glossary_path.exists():
                glossary = json.loads(glossary_path.read_text(encoding='utf-8'))
                lines = [f'  {ru} → {de}' for ru, de in glossary.items()]
                glossary_text = 'ГЛОССАРИЙ ИМЁН (для консистентности):\n' + '\n'.join(lines)

        # Read source
        if not source_path.exists():
            self.stderr.write(self.style.ERROR(f'Source file not found: {source_path}'))
            return

        source_text = source_path.read_text(encoding='utf-8')
        chunks = split_into_chunks(source_text, chunk_size)
        total_chunks = len(chunks)

        self.stdout.write(
            f'"{title}" — {len(source_text):,} chars, {total_chunks} chunks, model={model}'
        )

        # Load checkpoint
        checkpoint = {'chunks': [], 'completed_chunks': 0, 'total_chunks': total_chunks}
        if resume and partial_path.exists():
            checkpoint = json.loads(partial_path.read_text(encoding='utf-8'))
            self.stdout.write(
                f'Resuming from chunk {checkpoint["completed_chunks"]}/{total_chunks}'
            )

        client = get_openai_client()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Translate chunks
        for i, chunk in enumerate(chunks):
            if i < checkpoint['completed_chunks']:
                continue

            # Previous context for continuity
            prev_context = ''
            if i > 0 and checkpoint['chunks']:
                prev_text = checkpoint['chunks'][-1]['translated']
                # Last ~500 chars
                prev_context = prev_text[-500:] if len(prev_text) > 500 else prev_text

            self.stdout.write(
                f'  [{i + 1}/{total_chunks}] Translating...',
                ending=''
            )

            # Stage A: Translate
            system_prompt = TRANSLATE_SYSTEM.format(
                title=title,
                name_glossary=glossary_text
            )
            user_prompt = TRANSLATE_USER.format(
                previous_context=prev_context or '(начало текста)',
                chunk=chunk
            )

            translation = call_llm(client, model, system_prompt, user_prompt,
                                   temperature=temperature)

            # Stage B: Verify
            verified = False
            if do_verify:
                self.stdout.write(' verifying...', ending='')
                verify_result = call_llm(
                    client, model,
                    VERIFY_SYSTEM,
                    VERIFY_USER.format(original=chunk, translation=translation),
                    temperature=0.2,
                )
                if verify_result.strip() == 'FREIGEGEBEN':
                    verified = True
                else:
                    # Verification returned corrected version
                    # Strip any Russian commentary that might precede the German text
                    cleaned = verify_result
                    # If there's a clear separator like "Исправленный вариант:"
                    for marker in ['Исправленный вариант:', 'Исправленная версия:',
                                   'Korrigierte Version:', 'Korrektur:']:
                        if marker in cleaned:
                            cleaned = cleaned.split(marker, 1)[1].strip()
                            break
                    # If first lines are Russian commentary (numbered list), skip them
                    lines = cleaned.split('\n')
                    start_idx = 0
                    for idx, line in enumerate(lines):
                        stripped = line.strip()
                        # Skip lines starting with numbers or Russian text analysis
                        if (re.match(r'^\d+\.', stripped) or
                            stripped.startswith('В переводе') or
                            stripped.startswith('Проблемы') or
                            stripped == ''):
                            start_idx = idx + 1
                        else:
                            break
                    if start_idx > 0:
                        cleaned = '\n'.join(lines[start_idx:]).strip()
                    translation = cleaned if cleaned else verify_result
                    verified = True

            # Save checkpoint immediately
            checkpoint['chunks'].append({
                'index': i,
                'original': chunk[:200] + '...',  # save only preview to keep file small
                'translated': translation,
                'verified': verified,
            })
            checkpoint['completed_chunks'] = i + 1
            checkpoint['model'] = model

            partial_path.write_text(
                json.dumps(checkpoint, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )

            chars = len(translation)
            status = ' (verified)' if verified else ''
            self.stdout.write(f' OK ({chars} chars){status}')

        # Assemble full translation
        full_translation = '\n'.join(
            c['translated'] for c in checkpoint['chunks']
        )

        # Stage C: Stylistic pass
        if do_stylistic:
            # Only do stylistic pass if text is not too long (< 30K chars)
            if len(full_translation) < 30000:
                self.stdout.write('Running stylistic pass...', ending='')
                stylistic_result = call_llm(
                    client, model,
                    STYLISTIC_SYSTEM,
                    full_translation,
                    temperature=0.3,
                    max_tokens=16000,
                )
                if stylistic_result and len(stylistic_result) > len(full_translation) * 0.5:
                    full_translation = stylistic_result
                    self.stdout.write(' OK')
                else:
                    self.stdout.write(' skipped (result too short)')
            else:
                self.stdout.write(
                    f'Skipping stylistic pass (text too long: {len(full_translation):,} chars)'
                )

        # Save final output
        output_path.write_text(full_translation, encoding='utf-8')

        # Clean up partial file
        if partial_path.exists():
            partial_path.unlink()

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Translated "{title}": {len(full_translation):,} chars -> {output_path}'
        ))
