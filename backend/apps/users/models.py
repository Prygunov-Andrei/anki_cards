from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Расширенная модель пользователя"""
    
    LANGUAGE_CHOICES = [
        ('ru', 'Russian'),
        ('en', 'English'),
        ('pt', 'Portuguese'),
        ('de', 'German'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('it', 'Italian'),
        ('tr', 'Turkish'),
    ]
    
    NATIVE_LANGUAGE_CHOICES = [
        ('ru', 'Russian'),
        ('en', 'English'),
        ('pt', 'Portuguese'),
        ('de', 'German'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('it', 'Italian'),
        ('tr', 'Turkish'),
    ]
    
    LEARNING_LANGUAGE_CHOICES = [
        ('ru', 'Russian'),
        ('en', 'English'),
        ('pt', 'Portuguese'),
        ('de', 'German'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('it', 'Italian'),
        ('tr', 'Turkish'),
    ]
    
    THEME_CHOICES = [
        ('light', 'Светлая'),
        ('dark', 'Темная'),
    ]
    
    MODE_CHOICES = [
        ('simple', 'Простой'),
        ('advanced', 'Расширенный'),
    ]
    
    IMAGE_PROVIDER_CHOICES = [
        ('openai', 'OpenAI DALL-E 3'),
        ('gemini', 'Google Gemini'),
    ]
    
    AUDIO_PROVIDER_CHOICES = [
        ('openai', 'OpenAI TTS'),
        ('gtts', 'Google TTS (gTTS)'),
    ]
    
    GEMINI_MODEL_CHOICES = [
        ('gemini-2.5-flash-image', 'Gemini Flash (быстрая, 0.5 токена)'),
        ('nano-banana-pro-preview', 'Nano Banana Pro (новая, 1 токен)'),
    ]
    
    preferred_language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='en',
        verbose_name='Предпочитаемый язык'
    )
    
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Имя'
    )
    
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Фамилия'
    )
    
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    
    native_language = models.CharField(
        max_length=2,
        choices=NATIVE_LANGUAGE_CHOICES,
        default='en',
        verbose_name='Родной язык'
    )
    
    learning_language = models.CharField(
        max_length=2,
        choices=LEARNING_LANGUAGE_CHOICES,
        default='de',
        verbose_name='Язык изучения'
    )
    
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light',
        verbose_name='Тема интерфейса'
    )
    
    mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES,
        default='advanced',
        verbose_name='Режим работы'
    )
    
    image_provider = models.CharField(
        max_length=20,
        choices=IMAGE_PROVIDER_CHOICES,
        default='openai',
        verbose_name='Провайдер генерации изображений'
    )
    
    gemini_model = models.CharField(
        max_length=50,
        choices=GEMINI_MODEL_CHOICES,
        default='gemini-2.5-flash-image',
        verbose_name='Модель Gemini для генерации изображений'
    )
    
    audio_provider = models.CharField(
        max_length=20,
        choices=AUDIO_PROVIDER_CHOICES,
        default='openai',
        verbose_name='Провайдер генерации аудио'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата регистрации'
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.username
