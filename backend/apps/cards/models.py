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
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
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
        indexes = [
            models.Index(fields=['user', 'prompt_type']),
        ]
    
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


class PartOfSpeechCache(models.Model):
    """Модель для кэширования результатов определения части речи"""
    
    word = models.CharField(
        max_length=200,
        verbose_name='Слово'
    )
    language = models.CharField(
        max_length=2,
        verbose_name='Язык'
    )
    part_of_speech = models.CharField(
        max_length=50,
        verbose_name='Часть речи'
    )
    article = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name='Артикль (для немецкого)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Кэш части речи'
        verbose_name_plural = 'Кэш частей речи'
        unique_together = [['word', 'language']]
        indexes = [
            models.Index(fields=['word', 'language']),
        ]
    
    def __str__(self):
        article_str = f" ({self.article})" if self.article else ""
        return f"{self.word} ({self.language}): {self.part_of_speech}{article_str}"


class Deck(models.Model):
    """Модель колоды карточек"""
    
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('pt', 'Португальский'),
        ('de', 'Немецкий'),
        ('es', 'Испанский'),
        ('fr', 'Французский'),
        ('it', 'Итальянский'),
    ]
    
    NATIVE_LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('pt', 'Português'),
        ('de', 'Deutsch'),
        ('es', 'Español'),
        ('fr', 'Français'),
        ('it', 'Italiano'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='decks',
        verbose_name='Пользователь'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название колоды'
    )
    cover = models.ImageField(
        upload_to='deck_covers/',
        null=True,
        blank=True,
        verbose_name='Обложка колоды'
    )
    target_lang = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        verbose_name='Язык изучения'
    )
    source_lang = models.CharField(
        max_length=2,
        choices=NATIVE_LANGUAGE_CHOICES,
        default='ru',
        verbose_name='Родной язык'
    )
    words = models.ManyToManyField(
        'words.Word',
        related_name='decks',
        blank=True,
        verbose_name='Слова'
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
        verbose_name = 'Колода'
        verbose_name_plural = 'Колоды'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'updated_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    @property
    def words_count(self):
        """Количество слов в колоде"""
        return self.words.count()


class Token(models.Model):
    """Модель токенов пользователя (баланс)"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token',
        verbose_name='Пользователь'
    )
    balance = models.IntegerField(
        default=0,
        verbose_name='Баланс токенов'
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
        verbose_name = 'Токен'
        verbose_name_plural = 'Токены'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.balance} токенов"


class TokenTransaction(models.Model):
    """Модель транзакций токенов (история операций)"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('earned', 'Начислено'),
        ('spent', 'Потрачено'),
        ('refund', 'Возвращено'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token_transactions',
        verbose_name='Пользователь'
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='Тип транзакции'
    )
    amount = models.IntegerField(
        verbose_name='Сумма'
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата транзакции'
    )
    
    class Meta:
        verbose_name = 'Транзакция токенов'
        verbose_name_plural = 'Транзакции токенов'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        type_display = dict(self.TRANSACTION_TYPE_CHOICES).get(self.transaction_type, self.transaction_type)
        return f"{self.user.username}: {type_display} {self.amount} токенов"
