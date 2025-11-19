from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
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


class UserPrompt(models.Model):
    """Модель для хранения пользовательских промптов"""
    
    PROMPT_TYPE_CHOICES = [
        ('image', 'Генерация изображений'),
        ('audio', 'Генерация аудио'),
        ('word_analysis', 'Анализ смешанных языков'),
        ('translation', 'Перевод слов'),
        ('deck_name', 'Генерация названия колоды'),
        ('part_of_speech', 'Определение части речи'),
        ('category', 'Определение категории'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_prompts',
        verbose_name='Пользователь'
    )
    prompt_type = models.CharField(
        max_length=50,
        choices=PROMPT_TYPE_CHOICES,
        verbose_name='Тип промпта'
    )
    custom_prompt = models.TextField(
        verbose_name='Пользовательский промпт'
    )
    is_custom = models.BooleanField(
        default=False,
        verbose_name='Пользовательский промпт'
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
        verbose_name = 'Промпт пользователя'
        verbose_name_plural = 'Промпты пользователей'
        unique_together = [['user', 'prompt_type']]
        ordering = ['prompt_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_prompt_type_display()}"
    
    def clean(self):
        """Валидация промпта"""
        if self.custom_prompt:
            # Проверяем наличие обязательных плейсхолдеров в зависимости от типа
            required_placeholders = {
                'image': ['{word}', '{translation}'],
                'audio': ['{word}'],
                'word_analysis': ['{learning_language}', '{native_language}'],
                'translation': ['{learning_language}', '{native_language}'],
                'deck_name': ['{learning_language}', '{native_language}'],
                'part_of_speech': ['{word}', '{language}'],
                'category': ['{word}', '{language}'],
            }
            
            placeholders = required_placeholders.get(self.prompt_type, [])
            for placeholder in placeholders:
                if placeholder not in self.custom_prompt:
                    raise ValidationError(
                        f'Промпт должен содержать плейсхолдер {placeholder}'
                    )
