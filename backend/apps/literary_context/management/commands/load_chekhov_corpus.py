"""
Load the full Chekhov corpus from fixtures into the database.

Reads the manifest and loads Russian originals + German translations.

Usage:
    python manage.py load_chekhov_corpus
    python manage.py load_chekhov_corpus --index --skip-llm
"""
import json
from pathlib import Path
from io import StringIO

from django.core.management.base import BaseCommand
from django.core.management import call_command

from apps.literary_context.models import LiterarySource, LiteraryText

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / 'fixtures' / 'chekhov'
ORIGINALS_DIR = FIXTURES_DIR / 'originals'
TRANSLATIONS_DIR = FIXTURES_DIR / 'translations'
MANIFEST_PATH = FIXTURES_DIR / 'chekhov_manifest.json'


class Command(BaseCommand):
    help = 'Load Chekhov literary corpus from fixtures'

    def add_arguments(self, parser):
        parser.add_argument('--index', action='store_true', help='Also index texts after loading')
        parser.add_argument('--skip-llm', action='store_true', help='Skip LLM calls during indexing')
        parser.add_argument('--fragment-size', type=int, default=500, help='Fragment size for indexing')
        parser.add_argument('--slugs', type=str, default=None,
                            help='Comma-separated list of slugs to load')

    def handle(self, *args, **options):
        do_index = options['index']
        skip_llm = options['skip_llm']
        fragment_size = options['fragment_size']
        slugs_filter = options['slugs'].split(',') if options['slugs'] else None

        if not MANIFEST_PATH.exists():
            self.stderr.write(self.style.ERROR(
                'Manifest not found. Run fetch_chekhov_originals first.'
            ))
            return

        manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))

        # Get or create the source
        source, created = LiterarySource.objects.get_or_create(
            slug='chekhov',
            defaults={
                'name': 'Chekhov Stories',
                'source_language': 'ru',
                'available_languages': ['ru'],
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created source: Chekhov Stories'))

        loaded = 0
        skipped = 0

        for i, entry in enumerate(manifest, 1):
            slug = entry['slug']
            title = entry['title_ru']
            chars = entry['chars']

            if slugs_filter and slug not in slugs_filter:
                continue

            # Load Russian original
            ru_file = ORIGINALS_DIR / f'{slug}.ru.txt'
            de_file = TRANSLATIONS_DIR / f'{slug}.de.txt'

            if not ru_file.exists():
                self.stdout.write(f'  [{i}] SKIP {slug} (no Russian file)')
                skipped += 1
                continue

            ru_text = ru_file.read_text(encoding='utf-8').strip()
            word_count = len(ru_text.split())

            # Load/update Russian text
            text_obj, text_created = LiteraryText.objects.update_or_create(
                source=source,
                slug=slug,
                language='ru',
                defaults={
                    'title': title,
                    'full_text': ru_text,
                    'word_count': word_count,
                    'sort_order': i,
                },
            )
            action = 'Created' if text_created else 'Updated'
            self.stdout.write(f'  [{i}] {action} ru: {title} ({chars:,} chars)')
            loaded += 1

            # Load German translation if available
            if de_file.exists():
                de_text = de_file.read_text(encoding='utf-8').strip()
                de_word_count = len(de_text.split())

                LiteraryText.objects.update_or_create(
                    source=source,
                    slug=slug,
                    language='de',
                    defaults={
                        'title': title,
                        'full_text': de_text,
                        'word_count': de_word_count,
                        'sort_order': i,
                    },
                )
                self.stdout.write(f'        + de: {len(de_text):,} chars')
                loaded += 1

                # Ensure 'de' is in available_languages
                if 'de' not in source.available_languages:
                    source.available_languages = list(
                        set(source.available_languages + ['de'])
                    )
                    source.save(update_fields=['available_languages'])

            # Index if requested
            if do_index:
                for lang in ['ru', 'de']:
                    lang_file = ru_file if lang == 'ru' else de_file
                    if not lang_file.exists():
                        continue
                    try:
                        out = StringIO()
                        call_command(
                            'index_literary_text',
                            source_slug='chekhov',
                            text_slug=slug,
                            language=lang,
                            fragment_size=fragment_size,
                            skip_llm=skip_llm,
                            stdout=out,
                        )
                        self.stdout.write(out.getvalue().strip())
                    except Exception as e:
                        self.stderr.write(f'  Index error ({slug}/{lang}): {e}')

        self.stdout.write(self.style.SUCCESS(
            f'\nLoaded {loaded} texts, skipped {skipped}'
        ))
