"""
Batch-translate all Chekhov stories from Russian to German.

Usage:
    python manage.py translate_chekhov_corpus
    python manage.py translate_chekhov_corpus --model gpt-4.1 --verify --stylistic-pass
    python manage.py translate_chekhov_corpus --skip-existing --resume
    python manage.py translate_chekhov_corpus --slugs hameleon,dushechka,student
    python manage.py translate_chekhov_corpus --max-chars 50000
"""
import json
from io import StringIO
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management import call_command

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / 'fixtures' / 'chekhov'
ORIGINALS_DIR = FIXTURES_DIR / 'originals'
TRANSLATIONS_DIR = FIXTURES_DIR / 'translations'
MANIFEST_PATH = FIXTURES_DIR / 'chekhov_manifest.json'
GLOSSARY_PATH = FIXTURES_DIR / 'name_glossary.json'

DEFAULT_MODEL = 'gpt-4.1'


class Command(BaseCommand):
    help = 'Batch-translate all Chekhov stories from Russian to German'

    def add_arguments(self, parser):
        parser.add_argument('--model', type=str, default=DEFAULT_MODEL)
        parser.add_argument('--chunk-size', type=int, default=3000)
        parser.add_argument('--verify', action='store_true')
        parser.add_argument('--stylistic-pass', action='store_true')
        parser.add_argument('--skip-existing', action='store_true',
                            help='Skip stories that already have translations')
        parser.add_argument('--resume', action='store_true',
                            help='Resume interrupted translations')
        parser.add_argument('--slugs', type=str, default=None,
                            help='Comma-separated list of slugs to translate')
        parser.add_argument('--max-chars', type=int, default=None,
                            help='Skip stories longer than this (chars)')
        parser.add_argument('--sort', type=str, default='shortest',
                            choices=['shortest', 'longest', 'alpha'],
                            help='Translation order')

    def handle(self, *args, **options):
        model = options['model']
        skip_existing = options['skip_existing']
        resume = options['resume']
        slugs_filter = options['slugs'].split(',') if options['slugs'] else None
        max_chars = options['max_chars']
        sort_order = options['sort']

        TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)

        # Load manifest
        if not MANIFEST_PATH.exists():
            self.stderr.write(self.style.ERROR(
                'Manifest not found. Run fetch_chekhov_originals first.'
            ))
            return

        manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))

        # Filter
        stories = []
        for entry in manifest:
            slug = entry['slug']
            chars = entry['chars']

            if slugs_filter and slug not in slugs_filter:
                continue

            if max_chars and chars > max_chars:
                continue

            source_file = ORIGINALS_DIR / f'{slug}.ru.txt'
            output_file = TRANSLATIONS_DIR / f'{slug}.de.txt'

            if skip_existing and output_file.exists():
                continue

            if not source_file.exists():
                continue

            stories.append({
                'slug': slug,
                'title': entry['title_ru'],
                'chars': chars,
                'source_file': str(source_file),
                'output_file': str(output_file),
            })

        # Sort
        if sort_order == 'shortest':
            stories.sort(key=lambda s: s['chars'])
        elif sort_order == 'longest':
            stories.sort(key=lambda s: -s['chars'])
        else:
            stories.sort(key=lambda s: s['slug'])

        if not stories:
            self.stdout.write('No stories to translate.')
            return

        total_chars = sum(s['chars'] for s in stories)
        self.stdout.write(
            f'Translating {len(stories)} stories ({total_chars:,} chars total), model={model}\n'
        )

        translated = 0
        errors = 0

        for i, story in enumerate(stories, 1):
            self.stdout.write(self.style.HTTP_INFO(
                f'\n[{i}/{len(stories)}] "{story["title"]}" '
                f'({story["chars"]:,} chars, slug={story["slug"]})'
            ))

            try:
                out = StringIO()
                call_command(
                    'translate_literary_text',
                    source_file=story['source_file'],
                    output_file=story['output_file'],
                    model=model,
                    chunk_size=options['chunk_size'],
                    verify=options['verify'],
                    stylistic_pass=options['stylistic_pass'],
                    resume=resume,
                    title=story['title'],
                    glossary_file=str(GLOSSARY_PATH) if GLOSSARY_PATH.exists() else None,
                    stdout=out,
                )
                self.stdout.write(out.getvalue())
                translated += 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  ERROR: {e}'))
                errors += 1

                # Check for quota/budget errors — stop the batch
                error_str = str(e).lower()
                if any(kw in error_str for kw in ['insufficient_quota', 'billing', 'quota']):
                    self.stderr.write(self.style.ERROR(
                        '\nAPI quota/billing error detected. Stopping batch.'
                    ))
                    break

        self.stdout.write(self.style.SUCCESS(
            f'\nBatch complete! Translated: {translated}, Errors: {errors}'
        ))
