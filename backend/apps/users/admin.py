from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Административная панель для модели User"""
    list_display = ['username', 'email', 'native_language', 'learning_language', 'preferred_language', 'image_provider', 'gemini_model', 'audio_provider', 'created_at', 'is_staff']
    list_filter = ['native_language', 'learning_language', 'preferred_language', 'image_provider', 'gemini_model', 'audio_provider', 'is_staff', 'is_superuser', 'created_at']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('native_language', 'learning_language', 'preferred_language', 'image_provider', 'gemini_model', 'audio_provider')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('native_language', 'learning_language', 'preferred_language', 'image_provider', 'gemini_model', 'audio_provider')
        }),
    )
