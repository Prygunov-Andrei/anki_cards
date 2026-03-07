"""
Batch generate literary context for user words.

Usage:
    python manage.py generate_batch_context --source-slug chekhov --user-id 1
    python manage.py generate_batch_context --source-slug bible --language de --limit 50
    python manage.py generate_batch_context --source-slug chekhov --skip-hint
"""
import sys

from django.core.management.base import BaseCommand, CommandError

from apps.literary_context.models import LiterarySource, WordContextMedia
from apps.literary_context.generation import generate_word_context, LiteraryContextSettings
from apps.words.models import Word


class Command(BaseCommand):
    help = 'Batch generate literary context media for user words'

    def add_arguments(self, parser):
        parser.add_argument('--source-slug', required=True, help='Literary source slug')
        parser.add_argument('--user-id', type=int, help='Filter words by user ID')
        parser.add_argument('--language', help='Filter words by language (e.g. de, ru)')
        parser.add_argument('--limit', type=int, help='Max number of words to process')
        parser.add_argument('--skip-existing', action='store_true', default=True,
                            help='Skip words that already have context (default: True)')
        parser.add_argument('--force', action='store_true',
                            help='Regenerate even if context exists')
        parser.add_argument('--skip-hint', action='store_true',
                            help='Skip LLM hint generation')

    def handle(self, *args, **options):
        source_slug = options['source_slug']
        user_id = options['user_id']
        language = options['language']
        limit = options['limit']
        skip_existing = not options['force']
        skip_hint = options['skip_hint']

        try:
            source = LiterarySource.objects.get(slug=source_slug)
        except LiterarySource.DoesNotExist:
            raise CommandError(f'Literary source "{source_slug}" not found')

        words = Word.objects.all()
        if user_id:
            words = words.filter(user_id=user_id)
        if language:
            words = words.filter(language=language)

        words = words.order_by('id')

        if skip_existing:
            existing_word_ids = WordContextMedia.objects.filter(
                source=source
            ).values_list('word_id', flat=True)
            words = words.exclude(id__in=existing_word_ids)

        if limit:
            words = words[:limit]

        word_list = list(words)
        total = len(word_list)

        if total == 0:
            self.stdout.write(self.style.WARNING('No words to process'))
            return

        self.stdout.write(f'Processing {total} words for source "{source.name}"...')

        config = LiteraryContextSettings.get()
        stats = {'generated': 0, 'fallback': 0, 'errors': 0}

        for i, word in enumerate(word_list, 1):
            try:
                ctx = generate_word_context(word, source, config, skip_hint=skip_hint)
                stats['generated'] += 1
                if ctx.is_fallback:
                    stats['fallback'] += 1
                status = 'fallback' if ctx.is_fallback else ctx.match_method
                self.stdout.write(f'  [{i}/{total}] {word.original_word} -> {status}')
            except Exception as e:
                stats['errors'] += 1
                self.stderr.write(f'  [{i}/{total}] {word.original_word} -> ERROR: {e}')

            if i % 10 == 0:
                sys.stdout.flush()

        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {stats["generated"]} generated '
            f'({stats["fallback"]} fallback, {stats["errors"]} errors)'
        ))
