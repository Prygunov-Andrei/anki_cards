"""
Утилиты для работы с языками
"""
from typing import Dict

# Словарь полных названий языков для использования в LLM промптах
LANGUAGE_NAMES: Dict[str, str] = {
    'ru': 'Russian',
    'en': 'English',
    'pt': 'Portuguese',
    'de': 'German',
    'es': 'Spanish',
    'fr': 'French',
    'it': 'Italian',
}


def get_language_name(language_code: str) -> str:
    """
    Возвращает полное название языка по коду
    
    Args:
        language_code: Двухбуквенный ISO код языка (ru, en, pt, de, es, fr, it)
    
    Returns:
        Полное название языка на английском (Russian, English, и т.д.)
    
    Raises:
        KeyError: Если код языка не поддерживается
    """
    return LANGUAGE_NAMES[language_code]


def is_valid_language_code(language_code: str) -> bool:
    """
    Проверяет, является ли код языка валидным
    
    Args:
        language_code: Двухбуквенный ISO код языка
    
    Returns:
        True, если код поддерживается, False иначе
    """
    return language_code in LANGUAGE_NAMES

