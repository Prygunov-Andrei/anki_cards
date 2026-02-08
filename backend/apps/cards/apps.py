from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cards'
    verbose_name = 'Карточки'

    def ready(self):
        # Импортируем сигналы при запуске приложения
        import apps.cards.signals  # noqa: F401