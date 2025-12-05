from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Административная панель для модели User"""
    list_display = ['username', 'email', 'preferred_language', 'image_provider', 'gemini_model', 'created_at', 'is_staff']
    list_filter = ['preferred_language', 'image_provider', 'gemini_model', 'is_staff', 'is_superuser', 'created_at']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('preferred_language', 'image_provider', 'gemini_model')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('preferred_language', 'image_provider', 'gemini_model')
        }),
    )
