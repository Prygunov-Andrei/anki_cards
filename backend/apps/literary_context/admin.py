import logging

from django.contrib import admin, messages

from .models import (
    LiterarySource, LiteraryText, SceneAnchor, LiteraryFragment,
    WordContextMedia, LiteraryContextSettings,
)

logger = logging.getLogger(__name__)


class LiteraryTextInline(admin.TabularInline):
    model = LiteraryText
    extra = 0
    fields = ['slug', 'title', 'language']
    readonly_fields = ['slug']
    show_change_link = True


@admin.register(LiterarySource)
class LiterarySourceAdmin(admin.ModelAdmin):
    list_display = ['slug', 'name', 'source_language', 'is_active', 'created_at']
    list_filter = ['is_active', 'source_language']
    search_fields = ['slug', 'name']
    inlines = [LiteraryTextInline]


@admin.register(LiteraryText)
class LiteraryTextAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'slug', 'language', 'text_length', 'created_at']
    list_filter = ['source', 'language']
    search_fields = ['title', 'slug']

    def text_length(self, obj):
        return len(obj.full_text)
    text_length.short_description = 'Text Length'


class LiteraryFragmentInline(admin.TabularInline):
    model = LiteraryFragment
    extra = 0
    fields = ['text', 'content_preview', 'key_words']
    readonly_fields = ['content_preview']
    show_change_link = True

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(SceneAnchor)
class SceneAnchorAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'mood', 'is_generated',
        'characters_display', 'fragments_count',
    ]
    list_filter = ['source', 'mood', 'is_generated']
    search_fields = ['text_slug', 'scene_description']
    readonly_fields = ['created_at']
    inlines = [LiteraryFragmentInline]
    actions = ['generate_images']

    def characters_display(self, obj):
        return ', '.join(obj.characters) if obj.characters else '-'
    characters_display.short_description = 'Characters'

    def fragments_count(self, obj):
        return obj.fragments.count()
    fragments_count.short_description = 'Fragments'

    @admin.action(description='Generate images for selected anchors')
    def generate_images(self, request, queryset):
        from .image_generation import generate_scene_image
        config = LiteraryContextSettings.get()
        generated = 0
        errors = 0
        for anchor in queryset.filter(is_generated=False):
            try:
                generate_scene_image(anchor, config)
                generated += 1
            except Exception as e:
                logger.error(f'Image generation failed for {anchor}: {e}')
                errors += 1
        self.message_user(
            request,
            f'Generated {generated} images ({errors} errors)',
            messages.SUCCESS if not errors else messages.WARNING,
        )


@admin.register(LiteraryFragment)
class LiteraryFragmentAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'language', 'content_preview', 'keywords_count', 'has_embedding']
    list_filter = ['text__language', 'anchor__source']
    search_fields = ['content', 'key_words']
    actions = ['regenerate_keywords']

    def language(self, obj):
        return obj.text.language
    language.short_description = 'Language'

    def content_preview(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    content_preview.short_description = 'Content'

    def keywords_count(self, obj):
        return len(obj.key_words) if obj.key_words else 0
    keywords_count.short_description = 'Keywords'

    def has_embedding(self, obj):
        return obj.embedding is not None
    has_embedding.boolean = True
    has_embedding.short_description = 'Embedding'

    @admin.action(description='Regenerate keywords for selected fragments')
    def regenerate_keywords(self, request, queryset):
        from .corpus_processing import extract_keywords_batch
        config = LiteraryContextSettings.get()
        fragments = list(queryset.select_related('text'))
        contents = [f.content for f in fragments]
        # Use language from the first fragment's text; fragments in a batch
        # are typically the same language, but extract_keywords handles each individually
        language = fragments[0].text.language if fragments else 'en'
        try:
            keywords_list = extract_keywords_batch(contents, language, config)
            updated = 0
            for fragment, keywords in zip(fragments, keywords_list):
                fragment.key_words = keywords
                fragment.save(update_fields=['key_words'])
                updated += 1
            self.message_user(request, f'Regenerated keywords for {updated} fragments', messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f'Error regenerating keywords: {e}', messages.ERROR)


@admin.register(WordContextMedia)
class WordContextMediaAdmin(admin.ModelAdmin):
    list_display = [
        'word', 'source', 'match_method', 'match_score',
        'is_fallback', 'has_hint', 'has_audio', 'updated_at',
    ]
    list_filter = ['source', 'is_fallback', 'match_method']
    search_fields = ['word__original_word', 'hint_text']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['word', 'anchor', 'fragment']
    actions = ['regenerate_context', 'delete_fallbacks']

    def has_hint(self, obj):
        return bool(obj.hint_text)
    has_hint.boolean = True
    has_hint.short_description = 'Hint'

    def has_audio(self, obj):
        return bool(obj.audio_file)
    has_audio.boolean = True
    has_audio.short_description = 'Audio'

    @admin.action(description='Regenerate context for selected words')
    def regenerate_context(self, request, queryset):
        from .generation import generate_word_context
        config = LiteraryContextSettings.get()
        regenerated = 0
        errors = 0
        for media in queryset.select_related('word', 'source'):
            try:
                generate_word_context(media.word, media.source, config)
                regenerated += 1
            except Exception as e:
                logger.error(f'Regeneration failed for {media}: {e}')
                errors += 1
        self.message_user(
            request,
            f'Regenerated {regenerated} contexts ({errors} errors)',
            messages.SUCCESS if not errors else messages.WARNING,
        )

    @admin.action(description='Delete all fallback entries')
    def delete_fallbacks(self, request, queryset):
        count = queryset.filter(is_fallback=True).count()
        queryset.filter(is_fallback=True).delete()
        self.message_user(request, f'Deleted {count} fallback entries', messages.SUCCESS)


@admin.register(LiteraryContextSettings)
class LiteraryContextSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Matching', {
            'fields': ['semantic_match_min_score', 'llm_match_enabled'],
        }),
        ('Prompt Templates', {
            'fields': [
                'image_prompt_template',
                'hint_prompt_template',
                'sentence_extraction_prompt',
                'keyword_extraction_prompt',
                'scene_description_prompt',
            ],
            'classes': ['collapse'],
        }),
        ('LLM Models', {
            'fields': [
                'keyword_extraction_model',
                'scene_description_model',
                'hint_generation_model',
                'matching_model',
                'embedding_model',
                'embedding_dimensions',
            ],
        }),
        ('LLM Temperature', {
            'fields': [
                'hint_temperature',
                'keyword_temperature',
                'scene_description_temperature',
                'matching_temperature',
            ],
            'classes': ['collapse'],
        }),
        ('Token Costs (internal units)', {
            'fields': [
                'scene_image_cost',
                'hint_generation_cost',
                'audio_generation_cost',
                'llm_matching_cost',
            ],
        }),
        ('Fragment Splitting', {
            'fields': ['default_fragment_size', 'fragment_overlap'],
        }),
    ]

    def has_add_permission(self, request):
        return not LiteraryContextSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
