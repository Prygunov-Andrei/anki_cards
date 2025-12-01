"""
Утилиты для работы с LLM (OpenAI) для генерации медиа и анализа слов
"""
import os
import json
import re
import uuid
import io
import logging
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image
from openai import OpenAI
from django.conf import settings
from .prompt_utils import get_user_prompt, format_prompt
from .default_prompts import get_image_prompt_for_style

logger = logging.getLogger(__name__)

# PartOfSpeechCache больше не используется - кэширование отключено


def get_openai_client() -> OpenAI:
    """
    Создает и возвращает клиент OpenAI
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
    
    return OpenAI(api_key=api_key)


def detect_part_of_speech(
    word: str,
    language: str,
    user=None
) -> Dict[str, Optional[str]]:
    """
    Определяет часть речи для слова через LLM
    
    Args:
        word: Слово для анализа
        language: Язык слова (pt или de)
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Словарь с ключами:
        - 'part_of_speech': часть речи (noun, verb, adjective, и т.д.)
        - 'article': артикль для немецкого (der, die, das) или None
    """
    # Всегда запрашиваем у LLM, без кэширования
    logger.info(f"Определение части речи для '{word}' ({language}) через LLM")
    
    # Получаем промпт пользователя или заводской
    prompt_template = get_user_prompt(user, 'part_of_speech') if user else None
    if not prompt_template:
        prompt_template = """Определи часть речи для слова '{word}' на языке {language}.
Для немецкого языка также определи артикль.
Верни JSON: {{'part_of_speech': '...', 'article': 'der|die|das' (только для немецкого)}}"""
    
    # Формируем промпт
    prompt = format_prompt(
        prompt_template,
        word=word,
        language=language
    )
    
    client = get_openai_client()
    
    try:
        # Вызываем GPT API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Используем более дешевую модель для простых задач
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник для определения частей речи. Всегда возвращай валидный JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Низкая температура для более детерминированных результатов
            response_format={"type": "json_object"}  # Принудительно JSON
        )
        
        # Парсим ответ
        content = response.choices[0].message.content
        result = json.loads(content)
        
        part_of_speech = result.get('part_of_speech', 'unknown')
        article = result.get('article') if language == 'de' else None
        
        return {
            'part_of_speech': part_of_speech,
            'article': article
        }
        
    except json.JSONDecodeError:
        # Если не удалось распарсить JSON, пытаемся извлечь из текста
        try:
            # Пытаемся найти JSON в ответе
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                result = json.loads(json_match.group())
                part_of_speech = result.get('part_of_speech', 'unknown')
                article = result.get('article') if language == 'de' else None
                
                return {
                    'part_of_speech': part_of_speech,
                    'article': article
                }
        except:
            pass
        
        return {
            'part_of_speech': 'unknown',
            'article': None
        }
    
    except Exception as e:
        logger.error(f"Ошибка при определении части речи: {e}")
        return {
            'part_of_speech': 'unknown',
            'article': None
        }


def generate_image_with_dalle(
    word: str,
    translation: str,
    language: str,
    user=None,
    native_language: str = 'русском',
    english_translation: str = None,
    image_style: str = 'balanced'
) -> Tuple[Path, str]:
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
    """
    client = get_openai_client()
    
    # Используем промпт для выбранного стиля
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
    """
    client = get_openai_client()
    
    # Определяем голос в зависимости от языка и разнообразия
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
