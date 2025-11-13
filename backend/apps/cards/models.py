from django.db import models
from django.conf import settings
import uuid


class GeneratedDeck(models.Model):
    """Модель для хранения информации о сгенерированных колодах"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_decks',
        verbose_name='Пользователь'
    )
    deck_name = models.CharField(
        max_length=200,
        verbose_name='Название колоды'
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name='Путь к файлу'
    )
    cards_count = models.IntegerField(
        verbose_name='Количество карточек'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Сгенерированная колода'
        verbose_name_plural = 'Сгенерированные колоды'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.deck_name} ({self.user.username})"
