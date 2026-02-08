from django.contrib import admin
from .models import Word, Category, WordRelation


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'parent', 'icon', 'order', 'created_at']
    list_filter = ['user', 'parent', 'created_at']
    search_fields = ['name', 'user__username']
    ordering = ['user', 'order', 'name']


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ['original_word', 'translation', 'language', 'learning_status', 'card_type', 'user', 'created_at']
    list_filter = ['language', 'learning_status', 'card_type', 'part_of_speech', 'created_at']
    search_fields = ['original_word', 'translation', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['categories']
    raw_id_fields = ['user']

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'original_word', 'translation', 'language', 'card_type', 'learning_status')
        }),
        ('Медиафайлы', {
            'fields': ('audio_file', 'image_file')
        }),
        ('AI контент', {
            'fields': ('etymology', 'hint_text', 'hint_audio_file', 'example_sentences', 'part_of_speech'),
            'classes': ('collapse',),
        }),
        ('Категории', {
            'fields': ('categories',),
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(WordRelation)
class WordRelationAdmin(admin.ModelAdmin):
    list_display = ['word_from', 'word_to', 'relation_type', 'created_at']
    list_filter = ['relation_type', 'created_at']
    search_fields = ['word_from__original_word', 'word_to__original_word']
    raw_id_fields = ['word_from', 'word_to']
