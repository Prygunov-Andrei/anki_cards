from django.contrib import admin
from .models import Word


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    """Административная панель для модели Word"""
    list_display = ['original_word', 'translation', 'language', 'user', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['original_word', 'translation', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'original_word', 'translation', 'language')
        }),
        ('Медиафайлы', {
            'fields': ('audio_file', 'image_file')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )
