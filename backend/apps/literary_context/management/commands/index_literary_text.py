"""
Index a literary text: split into fragments, extract keywords, generate scene descriptions.

Usage:
    python manage.py index_literary_text \
        --source-slug chekhov \
        --text-slug hameleon \
        --language ru \
        --fragment-size 500 \
        --dry-run
"""
import sys
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.literary_context.models import (
    LiterarySource, LiteraryText, SceneAnchor, LiteraryFragment,
    LiteraryContextSettings,
)
from apps.literary_context.corpus_processing import (
    split_text_into_fragments,
    extract_keywords,
    generate_scene_description,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Index a literary text: split into fragments, extract keywords, generate scene descriptions'

    def add_arguments(self, parser):
        parser.add_argument('--source-slug', required=True, help='Source slug')
        parser.add_argument('--text-slug', required=True, help='Text slug')
        parser.add_argument('--language', required=True, help='Language code')
        parser.add_argument('--fragment-size', type=int, default=None, help='Fragment size in chars (default: from settings)')
        parser.add_argument('--overlap', type=int, default=None, help='Fragment overlap in chars (default: from settings)')
        parser.add_argument('--dry-run', action='store_true', help='Preview fragments without saving')
        parser.add_argument('--skip-llm', action='store_true', help='Skip LLM calls (keywords/scene description)')

    def handle(self, *args, **options):
        source_slug = options['source_slug']
        text_slug = options['text_slug']
        language = options['language']
        fragment_size = options['fragment_size']
        overlap = options['overlap']
        dry_run = options['dry_run']
        skip_llm = options['skip_llm']

        # Load text
        try:
            source = LiterarySource.objects.get(slug=source_slug)
        except LiterarySource.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Source not found: {source_slug}'))
            return

        try:
            text = LiteraryText.objects.get(
                source=source, slug=text_slug, language=language
            )
        except LiteraryText.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f'Text not found: {text_slug} ({language}) in source {source_slug}'
            ))
            return

        config = LiteraryContextSettings.get()

        # Split into fragments
        fragments = split_text_into_fragments(
            text.full_text,
            fragment_size=fragment_size,
            overlap=overlap,
        )

        self.stdout.write(f'Split "{text.title}" into {len(fragments)} fragments')

        if dry_run:
            for i, frag in enumerate(fragments):
                self.stdout.write(f'\n--- Fragment {i} ({len(frag)} chars) ---')
                self.stdout.write(frag[:200] + ('...' if len(frag) > 200 else ''))
            self.stdout.write(self.style.WARNING('\nDry run: no changes saved'))
            return

        created_anchors = 0
        created_fragments = 0

        with transaction.atomic():
            for i, frag_text in enumerate(fragments):
                # Progress
                sys.stdout.write(f'\rProcessing fragment {i + 1}/{len(fragments)}...')
                sys.stdout.flush()

                # Get or create SceneAnchor
                anchor, anchor_created = SceneAnchor.objects.get_or_create(
                    source=source,
                    text_slug=text_slug,
                    fragment_index=i,
                    defaults={
                        'scene_description': '',
                        'characters': [],
                        'mood': 'neutral',
                    },
                )
                if anchor_created:
                    created_anchors += 1

                # Generate scene description for new anchors (only if not skip_llm)
                if anchor_created and not skip_llm:
                    try:
                        scene_data = generate_scene_description(
                            frag_text, language, config
                        )
                        anchor.scene_description = scene_data['description']
                        anchor.characters = scene_data['characters']
                        # Validate mood against choices
                        valid_moods = [c[0] for c in SceneAnchor._meta.get_field('mood').choices]
                        if scene_data['mood'] in valid_moods:
                            anchor.mood = scene_data['mood']
                        anchor.save()
                    except Exception as e:
                        logger.warning(f'Failed to generate scene description for fragment {i}: {e}')

                # Extract keywords (only if not skip_llm)
                key_words = []
                if not skip_llm:
                    try:
                        key_words = extract_keywords(frag_text, language, config)
                    except Exception as e:
                        logger.warning(f'Failed to extract keywords for fragment {i}: {e}')

                # Create or update fragment
                fragment, frag_created = LiteraryFragment.objects.update_or_create(
                    anchor=anchor,
                    text=text,
                    defaults={
                        'content': frag_text,
                        'key_words': key_words,
                    },
                )
                if frag_created:
                    created_fragments += 1

        self.stdout.write('')  # newline after progress
        self.stdout.write(self.style.SUCCESS(
            f'Done: {created_anchors} anchors created, '
            f'{created_fragments} fragments created, '
            f'{len(fragments) - created_fragments} fragments updated'
        ))
