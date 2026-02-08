from django.apps import AppConfig


class WordsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.words'
    
    def ready(self):
        """Импортируем сигналы при запуске приложения"""
        import apps.words.signals  # noqa