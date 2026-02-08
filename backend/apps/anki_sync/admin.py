from django.contrib import admin
from .models import AnkiSyncUser, AnkiSyncMedia


@admin.register(AnkiSyncUser)
class AnkiSyncUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'host_key', 'last_sync_time', 'created_at']
    list_filter = ['created_at', 'last_sync_time']
    search_fields = ['user__username', 'host_key']
    raw_id_fields = ['user']
    readonly_fields = ['created_at']


@admin.register(AnkiSyncMedia)
class AnkiSyncMediaAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'sync_user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['file_name', 'sync_user__user__username']
    raw_id_fields = ['sync_user']
    readonly_fields = ['created_at']
