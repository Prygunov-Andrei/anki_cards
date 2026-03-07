"""
Generate embeddings for literary fragments that don't have them yet.

Usage:
    python manage.py generate_embeddings --source-slug chekhov --language ru --batch-size 50
"""
import sys
import logging

from django.core.management.base import BaseCommand

from apps.literary_context.models import (
    LiterarySource, LiteraryFragment, LiteraryContextSettings,
)
from apps.literary_context.embedding_utils import generate_embeddings_batch

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate embeddings for literary fragments missing them'

    def add_arguments(self, parser):
        parser.add_argument('--source-slug', required=True, help='Source slug')
        parser.add_argument('--language', default=None, help='Filter by language code')
        parser.add_argument('--batch-size', type=int, default=50, help='Texts per API call')
        parser.add_argument('--force', action='store_true', help='Regenerate even if embedding exists')

    def handle(self, *args, **options):
        source_slug = options['source_slug']
        language = options['language']
        batch_size = options['batch_size']
        force = options['force']

        try:
            source = LiterarySource.objects.get(slug=source_slug)
        except LiterarySource.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Source not found: {source_slug}'))
            return

        config = LiteraryContextSettings.get()

        qs = LiteraryFragment.objects.filter(anchor__source=source)
        if language:
            qs = qs.filter(text__language=language)
        if not force:
            qs = qs.filter(embedding__isnull=True)

        fragments = list(qs.select_related('text', 'anchor'))

        if not fragments:
            self.stdout.write('No fragments need embedding generation.')
            return

        self.stdout.write(f'Generating embeddings for {len(fragments)} fragments...')

        texts = [f.content for f in fragments]
        generated = 0

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_frags = fragments[i:i + batch_size]

            sys.stdout.write(f'\rBatch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}...')
            sys.stdout.flush()

            try:
                embeddings = generate_embeddings_batch(batch_texts, config, batch_size=batch_size)
                for frag, emb in zip(batch_frags, embeddings):
                    frag.embedding = emb
                    frag.save(update_fields=['embedding'])
                    generated += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'\nBatch failed: {e}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done: {generated}/{len(fragments)} embeddings generated'
        ))
