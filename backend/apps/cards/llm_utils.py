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
from .default_prompts import get_image_prompt_for_style, get_default_prompt, get_image_prompt_generation_for_style

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
        language: Язык слова (ru, en, pt, de, es, fr, it)
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


def generate_image_prompts_batch(
    words_translations: List[Dict[str, str]],
    user=None,
    image_style: str = 'balanced'
) -> Dict[str, str]:
    """
    Первый этап: генерирует промпты для изображений через GPT-4o-mini
    
    Args:
        words_translations: Список словарей [{'word': 'Haus', 'translation': 'дом'}, ...]
        user: Пользователь (для получения пользовательского промпта)
        image_style: Стиль генерации (minimalistic, balanced, creative)
    
    Returns:
        Словарь {word: prompt} с готовыми промптами для генерации изображений
    """
    if not words_translations:
        return {}
    
    client = get_openai_client()
    
    # Получаем промпт для первого этапа в зависимости от стиля
    prompt_key = f'image_prompt_generation_{image_style}'
    prompt_template = get_user_prompt(user, prompt_key)
    if not prompt_template:
        prompt_template = get_image_prompt_generation_for_style(image_style)
    
    # Формируем список слов для обработки
    words_list_text = "\n".join([
        f"- {item['translation']}" for item in words_translations
    ])
    
    # Создаем системный промпт на основе шаблона
    # Убираем плейсхолдер {translation} и заменяем на общую инструкцию
    system_prompt = prompt_template.replace("{translation}", "указанное слово, словосочетание или фразу")
    
    # КРИТИЧЕСКИ ВАЖНО: Добавляем явный запрет на текст в описании
    system_prompt += "\n\nКРИТИЧЕСКИ ВАЖНО: В описании НЕ должно быть упоминаний о тексте, буквах, цифрах, символах, надписях, знаках, книгах, экранах, плакатах, табличках, интерфейсах. Описывай ТОЛЬКО визуальные объекты, действия и сцены БЕЗ ЛЮБЫХ ФОРМ ТЕКСТА."
    
    # Добавляем инструкции для batch обработки в JSON формате
    system_prompt += "\n\nФормат ответа: ТОЛЬКО JSON без дополнительного текста.\n{\"перевод1\": \"визуальное описание сцены...\", \"перевод2\": \"визуальное описание сцены...\"}"
    
    # Определяем формат ответа в зависимости от стиля
    if image_style == 'minimalistic':
        format_instruction = "Каждое описание должно быть 1-2 коротких предложения, только перечисление визуальных элементов."
    elif image_style == 'creative':
        format_instruction = "Каждое описание должно быть 3-5 предложений, живой образный язык."
    else:  # balanced
        format_instruction = "Каждое описание должно быть 2-4 предложения, описательный стиль."
    
    user_prompt = f"""Создай визуальные описания сцен для следующих слов:

{words_list_text}

Верни ТОЛЬКО JSON в формате: {{"перевод": "описание сцены"}}
{format_instruction}
СТРОГО БЕЗ упоминаний текста, букв, цифр, символов, надписей, знаков, книг, экранов, плакатов.
Начни сразу с описания сцены."""
    
    result_text = None
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        result_dict = json.loads(result_text)
        
        # Преобразуем результат: ключи - переводы, значения - промпты
        # Нужно сопоставить переводы со словами
        prompts_map = {}
        for item in words_translations:
            translation = item['translation']
            word = item.get('word', '')
            
            # Ищем промпт по переводу
            if translation in result_dict:
                prompts_map[word] = result_dict[translation]
            else:
                # Если точного совпадения нет, берем первый доступный или используем fallback
                logger.warning(f"Промпт для '{translation}' не найден в ответе GPT")
                prompts_map[word] = f"Визуальная иллюстрация, передающая смысл: {translation}"
        
        logger.info(f"Сгенерировано промптов: {len(prompts_map)} из {len(words_translations)}")
        return prompts_map
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON при генерации промптов: {str(e)}")
        if result_text:
            logger.error(f"Ответ LLM: {result_text}")
        # Fallback: возвращаем простые промпты
        return {
            item.get('word', ''): f"Визуальная иллюстрация, передающая смысл: {item['translation']}"
            for item in words_translations
        }
    except Exception as e:
        logger.error(f"Ошибка при генерации промптов: {str(e)}")
        # Fallback: возвращаем простые промпты
        return {
            item.get('word', ''): f"Визуальная иллюстрация, передающая смысл: {item['translation']}"
            for item in words_translations
        }


def generate_image_with_dalle(
    word: str,
    translation: str,
    language: str,
    user=None,
    native_language: str = 'русском',
    english_translation: str = None,
    image_style: str = 'balanced',
    custom_prompt: str = None
) -> Tuple[Path, str]:
    """
    Генерирует изображение для слова через OpenAI DALL-E 3
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова (ru, en, pt, de, es, fr, it)
        user: Пользователь (не используется, оставлен для совместимости)
        native_language: Родной язык пользователя
        english_translation: Английский перевод (опционально)
        image_style: Стиль генерации изображения (minimalistic, balanced, creative)
    
    Returns:
        Кортеж (Path к сохраненному изображению, промпт)
    """
    client = get_openai_client()
    
    # Используем готовый промпт (если передан) или генерируем через шаблон
    if custom_prompt:
        # Используем промпт от GPT-4o-mini как есть, без добавления запретов
        # (запреты уже учтены GPT-4o-mini при генерации описания)
        prompt = custom_prompt
        logger.info(f"[DALL-E] Слово: '{word}', Перевод: '{translation}'")
        logger.info(f"[DALL-E] Используется готовый промпт (двухэтапная генерация)")
    else:
        # Старый способ: используем промпт для выбранного стиля
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
    model: str = None,
    custom_prompt: str = None
) -> Tuple[Path, str]:
    """
    Генерирует изображение для слова через Google Gemini
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова (ru, en, pt, de, es, fr, it)
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
    
    # Используем готовый промпт (если передан) или генерируем через шаблон
    if custom_prompt:
        # Используем промпт от GPT-4o-mini как есть, без добавления запретов
        # (запреты уже учтены GPT-4o-mini при генерации описания)
        prompt = custom_prompt
        logger.info(f"[Gemini] Слово: '{word}', Перевод: '{translation}', Модель: {model}")
        logger.info(f"[Gemini] Используется готовый промпт (двухэтапная генерация)")
    else:
        # Старый способ: используем промпт для выбранного стиля
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
    gemini_model: str = None,
    use_two_stage: bool = True,
    custom_prompt: str = None
) -> Tuple[Path, str]:
    """
    Универсальная функция для генерации изображения через выбранный провайдер
    Использует двухэтапный подход: сначала GPT-4o-mini создает промпт, затем генерируется изображение
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова (ru, en, pt, de, es, fr, it)
        user: Пользователь (для определения провайдера и модели из настроек)
        native_language: Родной язык пользователя
        english_translation: Английский перевод (опционально)
        image_style: Стиль генерации изображения (minimalistic, balanced, creative)
        provider: Провайдер ('openai' или 'gemini'). Если не указан, берется из user.image_provider
        gemini_model: Модель Gemini ('gemini-2.5-flash-image' или 'nano-banana-pro-preview').
                      Если не указана, берется из user.gemini_model
        use_two_stage: Использовать двухэтапную генерацию (True) или старый способ (False)
    
    Returns:
        Кортеж (Path к сохраненному изображению, промпт)
    """
    # Определяем провайдер
    if user and hasattr(user, 'image_provider'):
        provider = provider or user.image_provider
    else:
        provider = provider or 'openai'
    
    # Двухэтапная генерация: первый этап - создание промпта через GPT-4o-mini
    if use_two_stage and not custom_prompt:
        try:
            logger.info(f"[Two-Stage] Этап 1: Генерация промпта для '{word}' ({translation}), стиль: {image_style}")
            prompts = generate_image_prompts_batch(
                words_translations=[{'word': word, 'translation': translation}],
                user=user,
                image_style=image_style
            )
            if word in prompts:
                custom_prompt = prompts[word]
                logger.info(f"[Two-Stage] Промпт создан: {custom_prompt[:100]}...")
            else:
                logger.warning(f"[Two-Stage] Промпт для '{word}' не найден, используем fallback")
        except Exception as e:
            logger.error(f"[Two-Stage] Ошибка при генерации промпта: {str(e)}, используем fallback")
            # Продолжаем со старым способом
    
    # Второй этап: генерация изображения с готовым промптом
    if provider == 'gemini':
        return generate_image_with_gemini(
            word=word,
            translation=translation,
            language=language,
            user=user,
            native_language=native_language,
            english_translation=english_translation,
            image_style=image_style,
            model=gemini_model,
            custom_prompt=custom_prompt
        )
    else:  # По умолчанию OpenAI
        return generate_image_with_dalle(
            word=word,
            translation=translation,
            language=language,
            user=user,
            native_language=native_language,
            english_translation=english_translation,
            image_style=image_style,
            custom_prompt=custom_prompt
        )


def generate_images_batch(
    words_data: List[Dict[str, str]],
    user=None,
    native_language: str = 'русском',
    image_style: str = 'balanced',
    provider: str = 'openai',
    gemini_model: str = None,
    use_two_stage: bool = True
) -> Dict[str, Tuple[Path, str]]:
    """
    Batch генерация изображений для нескольких слов с двухэтапным подходом
    
    Args:
        words_data: Список словарей [{'word': 'Haus', 'translation': 'дом', 'language': 'de'}, ...]
        user: Пользователь
        native_language: Родной язык пользователя
        image_style: Стиль генерации
        provider: Провайдер ('openai' или 'gemini')
        gemini_model: Модель Gemini
        use_two_stage: Использовать двухэтапную генерацию
    
    Returns:
        Словарь {word: (Path, prompt)} с результатами генерации
    """
    results = {}
    
    # Первый этап: генерируем промпты для всех слов сразу
    prompts_map = {}
    if use_two_stage:
        try:
            logger.info(f"[Batch Two-Stage] Этап 1: Генерация промптов для {len(words_data)} слов, стиль: {image_style}")
            words_translations = [
                {'word': item['word'], 'translation': item['translation']}
                for item in words_data
            ]
            prompts_map = generate_image_prompts_batch(words_translations, user, image_style)
            logger.info(f"[Batch Two-Stage] Получено промптов: {len(prompts_map)}")
        except Exception as e:
            logger.error(f"[Batch Two-Stage] Ошибка при генерации промптов: {str(e)}, используем fallback")
    
    # Второй этап: генерируем изображения для каждого слова
    for item in words_data:
        word = item['word']
        translation = item['translation']
        language = item.get('language', 'de')
        
        custom_prompt = prompts_map.get(word) if use_two_stage and prompts_map else None
        
        try:
            result = generate_image(
                word=word,
                translation=translation,
                language=language,
                user=user,
                native_language=native_language,
                image_style=image_style,
                provider=provider,
                gemini_model=gemini_model,
                use_two_stage=False,  # Промпт уже готов
                custom_prompt=custom_prompt
            )
            results[word] = result
        except Exception as e:
            logger.error(f"[Batch] Ошибка при генерации изображения для '{word}': {str(e)}")
            results[word] = None
    
    return results


def generate_audio_with_gtts(
    word: str,
    language: str,
    user=None
) -> Path:
    """
    Генерирует аудио для слова через Google TTS (gTTS)
    
    Args:
        word: Исходное слово
        language: Язык слова (ru, en, pt, de, es, fr, it)
        user: Пользователь (не используется, оставлен для совместимости)
    
    Returns:
        Path к сохраненному аудиофайлу
    """
    try:
        from gtts import gTTS
    except ImportError:
        raise Exception("gTTS не установлен. Установите: pip install gtts")
    
    # Маппинг языков для gTTS
    # Для португальского используем 'pt' с tld='pt' для европейского варианта
    lang_map = {
        'ru': 'ru',
        'en': 'en',
        'pt': 'pt',  # Португальский (tld определяет диалект)
        'de': 'de',
        'es': 'es',
        'fr': 'fr',
        'it': 'it',
    }
    
    gtts_lang = lang_map.get(language, language)
    
    # Для португальского используем tld='pt' для европейского варианта
    # Для остальных языков используем tld='com'
    tld = 'pt' if language == 'pt' else 'com'
    
    try:
        # Создаем объект gTTS
        tts = gTTS(text=word, lang=gtts_lang, tld=tld, slow=False)
        
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.mp3"
        
        # Сохраняем аудио
        media_root = Path(settings.MEDIA_ROOT)
        audio_dir = media_root / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = audio_dir / filename
        
        # Сохраняем аудиофайл
        tts.save(str(file_path))
        
        logger.info(f"[gTTS] Сгенерировано аудио для '{word}' (язык: {gtts_lang}, tld: {tld})")
        
        return file_path
        
    except Exception as e:
        raise Exception(f"Ошибка при генерации аудио через gTTS: {str(e)}")


def generate_audio_with_tts(
    word: str,
    language: str,
    user=None,
    use_voice_variety: bool = True,
    provider: str = 'openai'
) -> Path:
    """
    Генерирует аудио для слова через выбранный провайдер (OpenAI TTS или gTTS)
    
    Args:
        word: Исходное слово
        language: Язык слова (ru, en, pt, de, es, fr, it)
        user: Пользователь (для получения настроек провайдера)
        use_voice_variety: Использовать разнообразие голосов (только для OpenAI)
        provider: Провайдер ('openai' или 'gtts'). Если не указан, берется из user.audio_provider
    
    Returns:
        Path к сохраненному аудиофайлу
    """
    # Определяем провайдер
    if user and hasattr(user, 'audio_provider'):
        provider = provider or user.audio_provider
    else:
        provider = provider or 'openai'
    
    # Для португальского по умолчанию используем gTTS
    if language == 'pt' and provider == 'openai':
        # Если пользователь не указал явно, используем gTTS для португальского
        if not hasattr(user, 'audio_provider') or user.audio_provider == 'openai':
            logger.info(f"[Audio] Для португальского языка используем gTTS (лучшее качество)")
            provider = 'gtts'
    
    # Вызываем соответствующую функцию
    if provider == 'gtts':
        return generate_audio_with_gtts(
            word=word,
            language=language,
            user=user
        )
    else:  # По умолчанию OpenAI
        return generate_audio_with_openai_tts(
            word=word,
            language=language,
            user=user,
            use_voice_variety=use_voice_variety
        )


def generate_audio_with_openai_tts(
    word: str,
    language: str,
    user=None,
    use_voice_variety: bool = True
) -> Path:
    """
    Генерирует аудио для слова через OpenAI TTS-1-HD
    
    Args:
        word: Исходное слово
        language: Язык слова (ru, en, pt, de, es, fr, it)
        user: Пользователь (для получения пользовательского промпта)
        use_voice_variety: Использовать разнообразие голосов
    
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
            'ru': 'alloy',  # Универсальный голос для русского
            'en': 'alloy',  # Универсальный голос для английского
            'pt': 'nova',   # Мягкий голос для португальского
            'de': 'onyx',   # Четкий голос для немецкого
            'es': 'nova',  # Мягкий голос для испанского
            'fr': 'shimmer', # Женский голос для французского
            'it': 'fable',  # Универсальный голос для итальянского
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
        learning_language: Язык изучения (ru, en, pt, de, es, fr, it)
        native_language: Родной язык пользователя (ru, en, pt, de, es, fr, it)
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
        learning_language: Язык изучения (ru, en, pt, de, es, fr, it)
        native_language: Родной язык пользователя (ru, en, pt, de, es, fr, it)
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
        raise ValueError(f"Ошибка парсинга ответа от OpenAI: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка при переводе слов: {error_msg}")
        
        # Проверяем тип ошибки
        if "429" in error_msg or "insufficient_quota" in error_msg.lower():
            raise ValueError("Превышен лимит квоты OpenAI API. Пожалуйста, проверьте баланс и настройки биллинга.")
        elif "401" in error_msg or "invalid_api_key" in error_msg.lower():
            raise ValueError("Неверный API ключ OpenAI. Пожалуйста, проверьте настройки.")
        elif "rate_limit" in error_msg.lower():
            raise ValueError("Превышен лимит запросов. Пожалуйста, подождите немного и попробуйте снова.")
        else:
            raise ValueError(f"Ошибка при переводе слов: {error_msg}")


def process_german_word(word: str, user=None) -> str:
    """
    Обрабатывает немецкое слово: добавляет артикль для существительных,
    исправляет регистр
    
    Args:
        word: Немецкое слово для обработки
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Обработанное слово (например, "das Haus" для существительного)
        
    Примечание:
        Если переданное слово является предложением или словосочетанием
        (содержит пробелы или несколько слов), функция возвращает его без изменений,
        так как обработка предназначена только для отдельных слов.
    """
    if not word:
        return word
    
    # Проверяем, является ли входная строка предложением/словосочетанием
    # Если содержит пробелы и более одного слова - не обрабатываем
    word_parts = word.strip().split()
    if len(word_parts) > 1:
        # Это предложение или словосочетание - возвращаем без изменений
        logger.info(f"Пропущена обработка словосочетания/предложения: '{word}' (содержит {len(word_parts)} слов)")
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
        learning_language: Язык изучения (ru, en, pt, de, es, fr, it)
        native_language: Родной язык пользователя (ru, en, pt, de, es, fr, it)
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
        language: Язык слов (ru, en, pt, de, es, fr, it)
        native_language: Родной язык пользователя (ru, en, pt, de, es, fr, it)
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
