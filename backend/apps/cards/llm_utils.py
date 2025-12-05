"""
Утилиты для работы с LLM (OpenAI, Gemini) для генерации медиа и анализа слов
"""
import os
import json
import re
import uuid
import io
import logging
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from PIL import Image
from openai import OpenAI
from django.conf import settings
from .prompt_utils import get_user_prompt, format_prompt
from .default_prompts import get_image_prompt_for_style

logger = logging.getLogger(__name__)

# Импорт Gemini API (опционально)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai не установлен. Gemini API недоступен.")

# PartOfSpeechCache больше не используется - кэширование отключено


def get_openai_client() -> OpenAI:
    """
    Создает и возвращает клиент OpenAI
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
    
    return OpenAI(api_key=api_key)


def get_gemini_client():
    """
    Настраивает и возвращает клиент Gemini API
    """
    if not GEMINI_AVAILABLE:
        raise ValueError("google-generativeai не установлен. Установите: pip install google-generativeai")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    genai.configure(api_key=api_key)
    return genai


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


def generate_image_with_gemini(
    word: str,
    translation: str,
    language: str,
    user=None,
    native_language: str = 'русском',
    english_translation: str = None,
    image_style: str = 'balanced',
    model: str = None
) -> Tuple[Path, str]:
    """
    Генерирует изображение для слова через Google Gemini
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова (pt или de)
        user: Пользователь (для получения настройки модели из профиля)
        native_language: Родной язык пользователя
        english_translation: Английский перевод (опционально)
        image_style: Стиль генерации изображения (minimalistic, balanced, creative)
        model: Модель Gemini ('gemini-2.5-flash-image' или 'nano-banana-pro-preview')
               Если не указана, берется из user.gemini_model
    
    Returns:
        Кортеж (Path к сохраненному изображению, промпт)
    """
    if not GEMINI_AVAILABLE:
        raise ValueError("google-generativeai не установлен. Установите: pip install google-generativeai")
    
    genai_client = get_gemini_client()
    
    # Определяем модель
    if not model:
        if user and hasattr(user, 'gemini_model'):
            model = user.gemini_model
        else:
            model = 'gemini-2.5-flash-image'  # По умолчанию быстрая модель
    
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
    logger.info(f"[Gemini] Слово: '{word}', Перевод: '{translation}', Модель: {model}")
    logger.info(f"[Gemini] Финальный промпт: {prompt}")
    
    try:
        # Используем выбранную модель Gemini
        # gemini-2.5-flash-image: быстрая (~4.7 сек), 0.5 токена
        # nano-banana-pro-preview: новая (~12.6 сек), 1 токен
        genai_model = genai.GenerativeModel(model)
        
        # Генерируем изображение
        response = genai_model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.7 if image_style == 'creative' else 0.4,
            }
        )
        
        # Получаем изображение из ответа
        if not response.candidates or not response.candidates[0].content.parts:
            raise Exception("Gemini не вернул изображение")
        
        # Извлекаем изображение из ответа
        image_data = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Данные уже в байтах, не нужно декодировать base64
                image_data = part.inline_data.data
                logger.info(f"[Gemini] Изображение получено: {len(image_data)} байт, MIME: {part.inline_data.mime_type}")
                break
            elif hasattr(part, 'image') and part.image:
                # Если изображение передано как URL, скачиваем его
                if hasattr(part.image, 'url'):
                    image_response = requests.get(part.image.url)
                    image_response.raise_for_status()
                    image_data = image_response.content
                else:
                    image_data = part.image.data
        
        if not image_data:
            raise Exception("Не удалось извлечь изображение из ответа Gemini")
        
        # Валидация изображения
        image = Image.open(io.BytesIO(image_data))
        image.verify()  # Проверка целостности
        
        # Переоткрываем для сохранения (verify закрывает файл)
        image = Image.open(io.BytesIO(image_data))
        
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
        raise Exception(f"Ошибка при генерации изображения через Gemini: {str(e)}")


def generate_image(
    word: str,
    translation: str,
    language: str,
    user=None,
    native_language: str = 'русском',
    english_translation: str = None,
    image_style: str = 'balanced',
    provider: str = 'openai',
    gemini_model: str = None
) -> Tuple[Path, str]:
    """
    Универсальная функция для генерации изображения через выбранный провайдер
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова (pt или de)
        user: Пользователь (для определения провайдера и модели из настроек)
        native_language: Родной язык пользователя
        english_translation: Английский перевод (опционально)
        image_style: Стиль генерации изображения (minimalistic, balanced, creative)
        provider: Провайдер ('openai' или 'gemini'). Если не указан, берется из user.image_provider
        gemini_model: Модель Gemini ('gemini-2.5-flash-image' или 'nano-banana-pro-preview').
                      Если не указана, берется из user.gemini_model
    
    Returns:
        Кортеж (Path к сохраненному изображению, промпт)
    """
    # Определяем провайдер
    if user and hasattr(user, 'image_provider'):
        provider = provider or user.image_provider
    else:
        provider = provider or 'openai'
    
    # Вызываем соответствующую функцию
    if provider == 'gemini':
        return generate_image_with_gemini(
            word=word,
            translation=translation,
            language=language,
            user=user,
            native_language=native_language,
            english_translation=english_translation,
            image_style=image_style,
            model=gemini_model
        )
    else:  # По умолчанию OpenAI
        return generate_image_with_dalle(
            word=word,
            translation=translation,
            language=language,
            user=user,
            native_language=native_language,
            english_translation=english_translation,
            image_style=image_style
        )


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


def detect_word_language(word: str, user=None) -> str:
    """
    Определяет язык слова через LLM
    
    Args:
        word: Слово для определения языка
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Код языка: 'ru', 'pt', 'de', 'en' или 'unknown'
    """
    client = get_openai_client()
    
    # Получаем промпт
    prompt_template = get_user_prompt(user, 'language_detection')
    if not prompt_template:
        from .default_prompts import get_default_prompt
        prompt_template = get_default_prompt('language_detection')
    
    prompt = format_prompt(prompt_template, word=word)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник для определения языка слов. Отвечай только кодом языка."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        language_code = response.choices[0].message.content.strip().lower()
        
        # Валидация кода языка
        valid_codes = ['ru', 'pt', 'de', 'en']
        if language_code in valid_codes:
            return language_code
        
        logger.warning(f"Неожиданный код языка от LLM: {language_code} для слова '{word}'")
        return 'unknown'
        
    except Exception as e:
        logger.error(f"Ошибка при определении языка слова '{word}': {str(e)}")
        return 'unknown'


def analyze_mixed_languages(
    words_list: List[str],
    learning_language: str,
    native_language: str,
    user=None
) -> Dict[str, str]:
    """
    Анализирует список слов и определяет, какие на изучаемом языке,
    а какие на родном. Возвращает пары слово-перевод.
    
    Args:
        words_list: Список слов для анализа
        learning_language: Язык изучения (pt или de)
        native_language: Родной язык пользователя (ru, en, pt, de)
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Словарь {слово_на_изучаемом: перевод_на_родном}
    """
    if not words_list:
        return {}
    
    client = get_openai_client()
    
    # Получаем промпт
    prompt_template = get_user_prompt(user, 'word_analysis')
    if not prompt_template:
        from .default_prompts import get_default_prompt
        prompt_template = get_default_prompt('word_analysis')
    
    words_str = ', '.join(words_list)
    prompt = format_prompt(
        prompt_template,
        words_list=words_str,
        learning_language=learning_language,
        native_language=native_language
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник для анализа слов. Отвечай только валидным JSON без дополнительного текста."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        result_dict = json.loads(result_text)
        
        return result_dict
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON при анализе смешанных языков: {str(e)}")
        logger.error(f"Ответ LLM: {result_text}")
        return {}
    except Exception as e:
        logger.error(f"Ошибка при анализе смешанных языков: {str(e)}")
        return {}


def translate_words(
    words_list: List[str],
    learning_language: str,
    native_language: str,
    user=None
) -> Dict[str, str]:
    """
    Переводит список слов с изучаемого языка на родной
    
    Args:
        words_list: Список слов для перевода
        learning_language: Язык изучения (pt или de)
        native_language: Родной язык пользователя (ru, en, pt, de)
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Словарь {слово: перевод}
    """
    if not words_list:
        return {}
    
    client = get_openai_client()
    
    # Получаем промпт
    prompt_template = get_user_prompt(user, 'translation')
    if not prompt_template:
        from .default_prompts import get_default_prompt
        prompt_template = get_default_prompt('translation')
    
    words_str = ', '.join(words_list)
    prompt = format_prompt(
        prompt_template,
        words_list=words_str,
        learning_language=learning_language,
        native_language=native_language
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник для перевода слов. Отвечай только валидным JSON без дополнительного текста."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        result_dict = json.loads(result_text)
        
        return result_dict
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON при переводе слов: {str(e)}")
        logger.error(f"Ответ LLM: {result_text}")
        return {}
    except Exception as e:
        logger.error(f"Ошибка при переводе слов: {str(e)}")
        return {}


def process_german_word(word: str, user=None) -> str:
    """
    Обрабатывает немецкое слово: добавляет артикль для существительных,
    исправляет регистр
    
    Args:
        word: Немецкое слово для обработки
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Обработанное слово (например, "das Haus" для существительного)
    """
    if not word:
        return word
    
    client = get_openai_client()
    
    # Получаем промпт
    prompt_template = get_user_prompt(user, 'german_word_processing')
    if not prompt_template:
        from .default_prompts import get_default_prompt
        prompt_template = get_default_prompt('german_word_processing')
    
    prompt = format_prompt(prompt_template, word=word)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник для обработки немецких слов. Отвечай только обработанным словом без дополнительного текста."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        processed_word = response.choices[0].message.content.strip()
        return processed_word
        
    except Exception as e:
        logger.error(f"Ошибка при обработке немецкого слова '{word}': {str(e)}")
        return word


def generate_deck_name(
    words_list: List[str],
    learning_language: str,
    native_language: str,
    user=None
) -> str:
    """
    Генерирует название колоды на основе списка слов
    
    Args:
        words_list: Список слов
        learning_language: Язык изучения (pt или de)
        native_language: Родной язык пользователя (ru, en, pt, de)
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Название колоды
    """
    if not words_list:
        return "Новая колода"
    
    client = get_openai_client()
    
    # Получаем промпт
    prompt_template = get_user_prompt(user, 'deck_name')
    if not prompt_template:
        from .default_prompts import get_default_prompt
        prompt_template = get_default_prompt('deck_name')
    
    words_str = ', '.join(words_list)
    prompt = format_prompt(
        prompt_template,
        words_list=words_str,
        learning_language=learning_language,
        native_language=native_language
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник для генерации названий колод. Отвечай только названием без дополнительного текста."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=30
        )
        
        deck_name = response.choices[0].message.content.strip()
        # Очищаем от кавычек, если они есть
        deck_name = deck_name.strip('"\'')
        return deck_name if deck_name else "Новая колода"
        
    except Exception as e:
        logger.error(f"Ошибка при генерации названия колоды: {str(e)}")
        return "Новая колода"


def detect_category(
    words_list: List[str],
    language: str,
    native_language: str,
    user=None
) -> str:
    """
    Определяет категорию для списка слов
    
    Args:
        words_list: Список слов
        language: Язык слов (pt или de)
        native_language: Родной язык пользователя (ru, en, pt, de)
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Название категории
    """
    if not words_list:
        return "Разное"
    
    client = get_openai_client()
    
    # Получаем промпт
    prompt_template = get_user_prompt(user, 'category')
    if not prompt_template:
        from .default_prompts import get_default_prompt
        prompt_template = get_default_prompt('category')
    
    words_str = ', '.join(words_list)
    prompt = format_prompt(
        prompt_template,
        words_list=words_str,
        language=language,
        native_language=native_language
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник для определения категорий слов. Отвечай только названием категории без дополнительного текста."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=20
        )
        
        category = response.choices[0].message.content.strip()
        # Очищаем от кавычек, если они есть
        category = category.strip('"\'')
        return category if category else "Разное"
        
    except Exception as e:
        logger.error(f"Ошибка при определении категории: {str(e)}")
        return "Разное"


def select_image_style(category: str) -> str:
    """
    Подбирает стиль изображения на основе категории
    
    Args:
        category: Категория слов
    
    Returns:
        Стиль изображения: 'minimalistic', 'balanced', или 'creative'
    """
    # Маппинг категорий на стили
    category_lower = category.lower()
    
    # Категории, для которых лучше подходит минималистичный стиль
    minimalistic_categories = ['числа', 'цвета', 'алфавит', 'базовые', 'простые']
    
    # Категории, для которых лучше подходит творческий стиль
    creative_categories = [
        'животные', 'природа', 'еда', 'спорт', 'хобби', 'искусство',
        'музыка', 'путешествия', 'праздники', 'эмоции'
    ]
    
    if any(cat in category_lower for cat in minimalistic_categories):
        return 'minimalistic'
    elif any(cat in category_lower for cat in creative_categories):
        return 'creative'
    else:
        # По умолчанию сбалансированный стиль
        return 'balanced'
