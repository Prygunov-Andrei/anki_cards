"""
Утилиты для работы с LLM (GPT) для анализа слов
"""
import json
import os
import re
from typing import Dict, Optional
from openai import OpenAI
from .prompt_utils import get_user_prompt, format_prompt
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
    import logging
    logger = logging.getLogger(__name__)
    
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
        
        # Не сохраняем в кэш - всегда запрашиваем заново
        
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
                
                # Не сохраняем в кэш - всегда запрашиваем заново
                
                return {
                    'part_of_speech': part_of_speech,
                    'article': article
                }
        except:
            pass
        
        # Если ничего не получилось, возвращаем unknown
        return {
            'part_of_speech': 'unknown',
            'article': None
        }
    
    except Exception as e:
        # В случае ошибки возвращаем unknown
        return {
            'part_of_speech': 'unknown',
            'article': None
        }



