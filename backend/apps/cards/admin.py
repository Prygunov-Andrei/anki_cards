from django.contrib import admin
from .models import GeneratedDeck


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
