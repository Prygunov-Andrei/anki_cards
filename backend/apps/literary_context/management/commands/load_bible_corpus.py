"""
Convenience command to load Bible corpus.
Expects text files in fixtures/bible/ directory.

Usage:
    python manage.py load_bible_corpus
    python manage.py load_bible_corpus --index --skip-llm
"""
from pathlib import Path
from io import StringIO

from django.core.management.base import BaseCommand
from django.core.management import call_command

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / 'fixtures' / 'bible'


class Command(BaseCommand):
    help = 'Load Bible literary corpus from fixtures'

    def add_arguments(self, parser):
        parser.add_argument('--index', action='store_true', help='Also index texts after loading')
        parser.add_argument('--skip-llm', action='store_true', help='Skip LLM calls during indexing')
        parser.add_argument('--fragment-size', type=int, default=500, help='Fragment size for indexing')

    def handle(self, *args, **options):
        do_index = options['index']
        skip_llm = options['skip_llm']
        fragment_size = options['fragment_size']

        if not FIXTURES_DIR.exists():
            self.stderr.write(self.style.WARNING(
                f'Bible fixtures directory not found: {FIXTURES_DIR}\n'
                f'Create it and add text files named like: genesis_1-3.ru.txt, genesis_1-3.de.txt'
            ))
            return

        # Scan for files: pattern is {slug}.{lang}.txt
        files_by_slug = {}
        for filepath in sorted(FIXTURES_DIR.glob('*.txt')):
            parts = filepath.stem.rsplit('.', 1)
            if len(parts) != 2:
                self.stderr.write(self.style.WARNING(
                    f'Skipping {filepath.name}: expected format slug.lang.txt'
                ))
                continue
            slug, lang = parts
            files_by_slug.setdefault(slug, {})[lang] = filepath

        if not files_by_slug:
            self.stderr.write(self.style.WARNING('No Bible text files found'))
            return

        loaded = 0
        for slug, lang_files in files_by_slug.items():
            title = slug.replace('_', ' ').replace('-', ' ').title()

            for lang, filepath in lang_files.items():
                out = StringIO()
                call_command(
                    'load_literary_text',
                    source_slug='bible',
                    source_name='Bible',
                    source_language='en',
                    text_slug=slug,
                    title=title,
                    language=lang,
                    file=str(filepath),
                    stdout=out,
                )
                self.stdout.write(out.getvalue().strip())
                loaded += 1

                if do_index:
                    out = StringIO()
                    call_command(
                        'index_literary_text',
                        source_slug='bible',
                        text_slug=slug,
                        language=lang,
                        fragment_size=fragment_size,
                        skip_llm=skip_llm,
                        stdout=out,
                    )
                    self.stdout.write(out.getvalue().strip())

        self.stdout.write(self.style.SUCCESS(f'\nLoaded {loaded} Bible texts'))
