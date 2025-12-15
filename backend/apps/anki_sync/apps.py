from django.apps import AppConfig


class AnkiSyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.anki_sync'
    verbose_name = 'Anki Sync Server'
