from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.constants import (
    LANGUAGE_CHOICES,
    THEME_CHOICES,
    MODE_CHOICES,
    IMAGE_PROVIDER_CHOICES,
    AUDIO_PROVIDER_CHOICES,
    IMAGE_STYLE_CHOICES,
    GEMINI_MODEL_CHOICES,
)


class User(AbstractUser):
    """Расширенная модель пользователя"""

    # Алиасы для обратной совместимости с сериализаторами, которые обращаются к User.LANGUAGE_CHOICES
    LANGUAGE_CHOICES = LANGUAGE_CHOICES
    NATIVE_LANGUAGE_CHOICES = LANGUAGE_CHOICES
    LEARNING_LANGUAGE_CHOICES = LANGUAGE_CHOICES
    THEME_CHOICES = THEME_CHOICES
    MODE_CHOICES = MODE_CHOICES
    IMAGE_PROVIDER_CHOICES = IMAGE_PROVIDER_CHOICES
    AUDIO_PROVIDER_CHOICES = AUDIO_PROVIDER_CHOICES
    IMAGE_STYLE_CHOICES = IMAGE_STYLE_CHOICES
    GEMINI_MODEL_CHOICES = GEMINI_MODEL_CHOICES
    
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

    image_style = models.CharField(
        max_length=20,
        choices=IMAGE_STYLE_CHOICES,
        default='balanced',
        verbose_name='Стиль генерации изображений'
    )

    # Per-user LLM settings (blank = use system defaults from LiteraryContextSettings)
    hint_generation_model = models.CharField(
        max_length=50, default='gpt-4o-mini', verbose_name='Модель для подсказок'
    )
    scene_description_model = models.CharField(
        max_length=50, default='gpt-4o-mini', verbose_name='Модель для описания сцен'
    )
    matching_model = models.CharField(
        max_length=50, default='gpt-4o', verbose_name='Модель для матчинга'
    )
    keyword_extraction_model = models.CharField(
        max_length=50, default='gpt-4o-mini', verbose_name='Модель для ключевых слов'
    )

    hint_temperature = models.FloatField(default=0.8, verbose_name='Температура подсказок')
    scene_description_temperature = models.FloatField(default=0.5, verbose_name='Температура описания сцен')
    matching_temperature = models.FloatField(default=0.2, verbose_name='Температура матчинга')
    keyword_temperature = models.FloatField(default=0.3, verbose_name='Температура ключевых слов')

    elevenlabs_voice_id = models.CharField(
        max_length=50, blank=True, default='', verbose_name='ElevenLabs Voice ID'
    )

    hint_prompt_template = models.TextField(blank=True, default='', verbose_name='Шаблон промпта подсказок')
    scene_description_prompt = models.TextField(blank=True, default='', verbose_name='Промпт описания сцен')
    keyword_extraction_prompt = models.TextField(blank=True, default='', verbose_name='Промпт ключевых слов')
    image_prompt_template = models.TextField(blank=True, default='', verbose_name='Шаблон промпта изображений')

    active_literary_source = models.ForeignKey(
        'literary_context.LiterarySource',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Активный литературный контекст',
        help_text='Если выбран, медиа слов будут из литературного источника'
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
