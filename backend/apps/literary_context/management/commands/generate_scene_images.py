"""
Generate scene images for SceneAnchors that don't have them.

Usage:
    python manage.py generate_scene_images --source-slug chekhov --limit 10 --dry-run
"""
import sys
import logging

from django.core.management.base import BaseCommand

from apps.literary_context.models import LiterarySource, SceneAnchor, LiteraryContextSettings
from apps.literary_context.image_generation import generate_scene_image

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate scene images for SceneAnchors missing images'

    def add_arguments(self, parser):
        parser.add_argument('--source-slug', required=True, help='Source slug')
        parser.add_argument('--text-slug', default=None, help='Filter by text slug')
        parser.add_argument('--limit', type=int, default=None, help='Max images to generate')
        parser.add_argument('--dry-run', action='store_true', help='Preview without generating')
        parser.add_argument('--force', action='store_true', help='Regenerate even if image exists')

    def handle(self, *args, **options):
        source_slug = options['source_slug']
        text_slug = options['text_slug']
        limit = options['limit']
        dry_run = options['dry_run']
        force = options['force']

        try:
            source = LiterarySource.objects.get(slug=source_slug)
        except LiterarySource.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Source not found: {source_slug}'))
            return

        config = LiteraryContextSettings.get()

        qs = SceneAnchor.objects.filter(source=source)
        if text_slug:
            qs = qs.filter(text_slug=text_slug)
        if not force:
            qs = qs.filter(image_file='')

        anchors = list(qs.order_by('text_slug', 'fragment_index'))
        if limit:
            anchors = anchors[:limit]

        if not anchors:
            self.stdout.write('No anchors need image generation.')
            return

        self.stdout.write(f'Found {len(anchors)} anchors to generate images for.')

        if dry_run:
            for anchor in anchors:
                prompt = config.image_prompt_template.format(
                    scene_description=anchor.scene_description
                )
                self.stdout.write(f'\n--- {anchor} ---')
                self.stdout.write(f'Prompt: {prompt[:200]}...')
            self.stdout.write(self.style.WARNING('\nDry run: no images generated'))
            return

        generated = 0
        errors = 0

        for i, anchor in enumerate(anchors):
            sys.stdout.write(f'\rGenerating {i + 1}/{len(anchors)}...')
            sys.stdout.flush()

            try:
                generate_scene_image(anchor, config)
                generated += 1
            except Exception as e:
                errors += 1
                logger.error(f'Failed to generate image for {anchor}: {e}')
                self.stderr.write(self.style.ERROR(f'\nFailed: {anchor}: {e}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done: {generated} images generated, {errors} errors'
        ))
