from django.contrib import admin
from .models import GeneratedDeck, UserPrompt, PartOfSpeechCache


@admin.register(GeneratedDeck)
class GeneratedDeckAdmin(admin.ModelAdmin):
    """Административная панель для модели GeneratedDeck"""
    list_display = ['deck_name', 'user', 'cards_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['deck_name', 'user__username']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'deck_name', 'cards_count')
        }),
        ('Файл', {
            'fields': ('file_path',)
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )


@admin.register(UserPrompt)
class UserPromptAdmin(admin.ModelAdmin):
    """Административная панель для модели UserPrompt"""
    list_display = ['user', 'prompt_type', 'is_custom', 'updated_at']
    list_filter = ['prompt_type', 'is_custom', 'updated_at']
    search_fields = ['user__username', 'prompt_type']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'prompt_type', 'is_custom')
        }),
        ('Промпт', {
            'fields': ('custom_prompt',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PartOfSpeechCache)
class PartOfSpeechCacheAdmin(admin.ModelAdmin):
    """Административная панель для модели PartOfSpeechCache"""
    list_display = ['word', 'language', 'part_of_speech', 'article', 'created_at']
    list_filter = ['language', 'part_of_speech', 'created_at']
    search_fields = ['word', 'part_of_speech']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('word', 'language', 'part_of_speech', 'article')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )
