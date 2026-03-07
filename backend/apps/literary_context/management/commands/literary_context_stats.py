"""
Report statistics for literary context data.

Usage:
    python manage.py literary_context_stats
    python manage.py literary_context_stats --source-slug chekhov
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Q

from apps.literary_context.models import (
    LiterarySource, LiteraryText, SceneAnchor,
    LiteraryFragment, WordContextMedia,
)


class Command(BaseCommand):
    help = 'Display literary context statistics'

    def add_arguments(self, parser):
        parser.add_argument('--source-slug', help='Filter by source slug')

    def handle(self, *args, **options):
        source_slug = options.get('source_slug')

        sources = LiterarySource.objects.all()
        if source_slug:
            sources = sources.filter(slug=source_slug)

        if not sources.exists():
            self.stdout.write(self.style.WARNING('No literary sources found'))
            return

        for source in sources:
            self._print_source_stats(source)
            self.stdout.write('')

        if not source_slug:
            self._print_totals()

    def _print_source_stats(self, source):
        self.stdout.write(self.style.SUCCESS(f'=== {source.name} ({source.slug}) ==='))
        self.stdout.write(f'  Active: {source.is_active}')
        self.stdout.write(f'  Source language: {source.source_language}')
        self.stdout.write(f'  Available languages: {", ".join(source.available_languages or [])}')

        # Texts
        texts = LiteraryText.objects.filter(source=source)
        text_by_lang = texts.values('language').annotate(count=Count('id'))
        self.stdout.write(f'\n  Texts: {texts.count()}')
        for entry in text_by_lang:
            self.stdout.write(f'    {entry["language"]}: {entry["count"]}')

        # Scene Anchors
        anchors = SceneAnchor.objects.filter(source=source)
        anchors_with_images = anchors.filter(is_generated=True).count()
        self.stdout.write(f'\n  Scene Anchors: {anchors.count()}')
        self.stdout.write(f'    With images: {anchors_with_images}')
        self.stdout.write(f'    Without images: {anchors.count() - anchors_with_images}')

        # Fragments
        fragments = LiteraryFragment.objects.filter(anchor__source=source)
        fragments_with_embeddings = fragments.exclude(embedding__isnull=True).count()
        fragments_with_keywords = fragments.exclude(key_words=[]).count()
        frag_by_lang = fragments.values('text__language').annotate(count=Count('id'))
        self.stdout.write(f'\n  Fragments: {fragments.count()}')
        self.stdout.write(f'    With embeddings: {fragments_with_embeddings}')
        self.stdout.write(f'    With keywords: {fragments_with_keywords}')
        for entry in frag_by_lang:
            self.stdout.write(f'    {entry["text__language"]}: {entry["count"]}')

        # Word Context Media
        media = WordContextMedia.objects.filter(source=source)
        media_stats = media.aggregate(
            total=Count('id'),
            fallback=Count('id', filter=Q(is_fallback=True)),
            with_hint=Count('id', filter=~Q(hint_text='')),
            with_audio=Count('id', filter=~Q(audio_file='')),
            avg_score=Avg('match_score'),
        )
        method_counts = media.values('match_method').annotate(count=Count('id'))

        self.stdout.write(f'\n  Word Context Media: {media_stats["total"]}')
        self.stdout.write(f'    Fallback: {media_stats["fallback"]}')
        self.stdout.write(f'    With hints: {media_stats["with_hint"]}')
        self.stdout.write(f'    With audio: {media_stats["with_audio"]}')
        if media_stats['avg_score'] is not None:
            self.stdout.write(f'    Avg match score: {media_stats["avg_score"]:.2f}')
        self.stdout.write(f'    By match method:')
        for entry in method_counts:
            method = entry['match_method'] or 'none'
            self.stdout.write(f'      {method}: {entry["count"]}')

    def _print_totals(self):
        self.stdout.write(self.style.SUCCESS('=== TOTALS ==='))
        self.stdout.write(f'  Sources: {LiterarySource.objects.count()}')
        self.stdout.write(f'  Texts: {LiteraryText.objects.count()}')
        self.stdout.write(f'  Scene Anchors: {SceneAnchor.objects.count()}')
        self.stdout.write(f'  Fragments: {LiteraryFragment.objects.count()}')
        self.stdout.write(f'  Word Context Media: {WordContextMedia.objects.count()}')
