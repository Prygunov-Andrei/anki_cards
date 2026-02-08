from django.apps import AppConfig


class TrainingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.training'
    verbose_name = 'Тренировка'

    def ready(self):
        # Импортируем сигналы при запуске приложения
        import apps.training.signals  # noqa: F401
