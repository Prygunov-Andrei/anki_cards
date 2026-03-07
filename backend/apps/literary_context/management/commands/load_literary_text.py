"""
Load a literary text file into the database.

Usage:
    python manage.py load_literary_text \
        --source-slug chekhov \
        --source-name "Chekhov Stories" \
        --source-language ru \
        --text-slug hameleon \
        --title "Hameleon" \
        --language ru \
        --file ./data/chekhov/hameleon.ru.txt
"""
from django.core.management.base import BaseCommand
from apps.literary_context.models import LiterarySource, LiteraryText


class Command(BaseCommand):
    help = 'Load a literary text file into the database'

    def add_arguments(self, parser):
        parser.add_argument('--source-slug', required=True, help='Source slug (e.g. "chekhov")')
        parser.add_argument('--source-name', default='', help='Source display name (used only when creating)')
        parser.add_argument('--source-language', default='ru', help='Source original language code')
        parser.add_argument('--text-slug', required=True, help='Text slug (e.g. "hameleon")')
        parser.add_argument('--title', required=True, help='Text title')
        parser.add_argument('--language', required=True, help='Language code of this text file')
        parser.add_argument('--file', required=True, help='Path to .txt file')

    def handle(self, *args, **options):
        source_slug = options['source_slug']
        source_name = options['source_name'] or source_slug.title()
        source_language = options['source_language']
        text_slug = options['text_slug']
        title = options['title']
        language = options['language']
        file_path = options['file']

        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                full_text = f.read().strip()
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        if not full_text:
            self.stderr.write(self.style.ERROR(f'File is empty: {file_path}'))
            return

        # Get or create source
        source, source_created = LiterarySource.objects.get_or_create(
            slug=source_slug,
            defaults={
                'name': source_name,
                'source_language': source_language,
                'available_languages': [source_language],
            },
        )
        if source_created:
            self.stdout.write(self.style.SUCCESS(f'Created source: {source.name}'))
        else:
            self.stdout.write(f'Using existing source: {source.name}')

        # Update available_languages if needed
        if language not in source.available_languages:
            source.available_languages = list(set(source.available_languages + [language]))
            source.save(update_fields=['available_languages'])
            self.stdout.write(f'Added language "{language}" to source available_languages')

        # Create or update text
        text, text_created = LiteraryText.objects.update_or_create(
            source=source,
            slug=text_slug,
            language=language,
            defaults={
                'title': title,
                'full_text': full_text,
            },
        )

        action = 'Created' if text_created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'{action} text: {title} ({language}), {len(full_text)} chars'
        ))
