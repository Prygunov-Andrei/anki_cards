from django.db import models
from django.conf import settings


class Word(models.Model):
    """Модель слова для изучения"""
    
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('pt', 'Португальский'),
        ('de', 'Немецкий'),
        ('es', 'Испанский'),
        ('fr', 'Французский'),
        ('it', 'Итальянский'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='words',
        verbose_name='Пользователь'
    )
    original_word = models.CharField(
        max_length=200,
        verbose_name='Исходное слово'
    )
    translation = models.CharField(
        max_length=200,
        verbose_name='Перевод'
    )
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        verbose_name='Язык'
    )
    audio_file = models.FileField(
        upload_to='audio/',
        null=True,
        blank=True,
        verbose_name='Аудиофайл'
    )
    image_file = models.ImageField(
        upload_to='images/',
        null=True,
        blank=True,
        verbose_name='Изображение'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Слово'
        verbose_name_plural = 'Слова'
        ordering = ['-created_at']
        # Уникальный индекс для предотвращения дубликатов
        unique_together = [['user', 'original_word', 'language']]
        indexes = [
            models.Index(fields=['user', 'language']),
            models.Index(fields=['user', 'original_word']),
        ]
    
    def __str__(self):
        return f"{self.original_word} ({self.language}) - {self.translation}"
