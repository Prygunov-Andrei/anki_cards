"""
Утилиты для работы с OpenAI API для генерации медиафайлов
"""
import os
import uuid
import io
import requests
from pathlib import Path
from typing import Optional
from openai import OpenAI
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image
from .prompt_utils import get_user_prompt
from .default_prompts import get_default_prompt, format_prompt


def get_openai_client() -> OpenAI:
    """
    Создает и возвращает клиент OpenAI
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
    
    return OpenAI(api_key=api_key)


def generate_image_with_dalle(
    word: str,
    translation: str,
    language: str,
    user=None,
    native_language: str = 'русском',
    english_translation: str = None,
    image_style: str = 'balanced'
) -> tuple[Path, str]:
    """
    Генерирует изображение для слова через OpenAI DALL-E 3
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова (pt или de)
        user: Пользователь (не используется, оставлен для совместимости)
        native_language: Родной язык пользователя
        english_translation: Английский перевод (опционально)
        image_style: Стиль генерации изображения (minimalistic, balanced, creative)
    
    Returns:
        Кортеж (Path к сохраненному изображению, промпт)
    
    Raises:
        ValueError: Если API ключ не установлен
        Exception: При ошибках API OpenAI
    """
    client = get_openai_client()
    
    # Используем промпт для выбранного стиля
    from .default_prompts import get_image_prompt_for_style
    prompt_template = get_image_prompt_for_style(image_style)
    
    # Формируем промпт для генерации изображения
    prompt = format_prompt(
        prompt_template,
        word=word,
        translation=translation,
        language=language,
        native_language=native_language,
        english_translation=english_translation or translation
    )
    
    # Логируем промпт для отладки
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[DALL-E] Слово: '{word}', Перевод: '{translation}'")
    logger.info(f"[DALL-E] Финальный промпт: {prompt}")
    
    try:
        # Вызываем DALL-E 3 API
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Получаем URL изображения
        image_url = response.data[0].url
        
        # Скачиваем изображение
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        # Валидация изображения
        image = Image.open(io.BytesIO(image_response.content))
        image.verify()  # Проверка целостности
        
        # Переоткрываем для сохранения (verify закрывает файл)
        image = Image.open(io.BytesIO(image_response.content))
        
        # Конвертируем в RGB если нужно
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.jpg"
        
        # Сохраняем изображение
        media_root = Path(settings.MEDIA_ROOT)
        images_dir = media_root / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = images_dir / filename
        
        # Сохраняем изображение
        image.save(file_path, "JPEG", quality=95)
        
        return file_path, prompt
        
    except Exception as e:
        raise Exception(f"Ошибка при генерации изображения через DALL-E 3: {str(e)}")


def generate_audio_with_tts(
    word: str,
    language: str,
    user=None,
    use_voice_variety: bool = True
) -> Path:
    """
    Генерирует аудио для слова через OpenAI TTS-1-HD
    
    Args:
        word: Исходное слово
        language: Язык слова (pt или de)
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Path к сохраненному аудиофайлу
    
    Raises:
        ValueError: Если API ключ не установлен
        Exception: При ошибках API OpenAI
    """
    client = get_openai_client()
    
    # Получаем промпт пользователя или заводской
    # Для аудио промпт используется только для инструкций, сам текст - это слово
    prompt_template = get_user_prompt(user, 'audio') if user else None
    
    # Определяем голос в зависимости от языка и разнообразия
    # OpenAI TTS поддерживает голоса: alloy, echo, fable, onyx, nova, shimmer
    import random
    
    if use_voice_variety:
        # Разнообразие голосов: женские (nova, shimmer), мужские (onyx, echo), универсальные (alloy, fable)
        all_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        voice = random.choice(all_voices)
    else:
        # Стандартное поведение: голос зависит от языка
        voice_map = {
            'pt': 'nova',  # Более мягкий голос для португальского
            'de': 'onyx',  # Более четкий голос для немецкого
        }
        voice = voice_map.get(language, 'alloy')
    
    try:
        # Вызываем TTS API
        # Для TTS промпт не используется напрямую, но может быть использован в будущем
        # для настройки стиля произношения
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=word,
        )
        
        # Получаем аудио данные
        audio_data = response.content
        
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.mp3"
        
        # Сохраняем аудио
        media_root = Path(settings.MEDIA_ROOT)
        audio_dir = media_root / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = audio_dir / filename
        
        # Сохраняем аудиофайл
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        
        return file_path
        
    except Exception as e:
        raise Exception(f"Ошибка при генерации аудио через TTS-1-HD: {str(e)}")

