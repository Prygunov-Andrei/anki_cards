"""
Промпты для генерации контента (этимология, подсказки, предложения, синонимы)
"""
from typing import Optional
from django.contrib.auth import get_user_model

User = get_user_model()


# Дефолтные промпты для генерации контента
DEFAULT_ETYMOLOGY_PROMPT = """Объясни происхождение и этимологию слова '{word}' на языке {language}.
Перевод слова: {translation}

Требования:
- Объяснение должно быть на языке {native_language}
- Длина: 2-3 предложения
- Укажи происхождение слова (из какого языка, когда появилось)
- Укажи значение и связь с другими словами, если есть
- Будь точным и информативным

Пример для слова "Haus" (дом):
"Слово 'Haus' происходит от древнегерманского 'hūs' и связано с индоевропейским корнем '*keu-', означающим 'прикрывать, защищать'. Изначально обозначало жилище, которое защищает от непогоды. Родственно словам 'house' в английском и 'hus' в древнескандинавском." """


DEFAULT_HINT_PROMPT = """Создай подсказку для слова '{word}' на языке {language}.

Требования:
- Подсказка должна быть на языке {language}
- НЕ упоминай само слово '{word}'
- НЕ упоминай перевод '{translation}'
- Описание должно быть 1-2 предложения
- Подсказка должна описывать слово без его прямого названия
- Используй описательные характеристики (что это, как выглядит, для чего используется)

Перевод слова (только для контекста, НЕ включай в подсказку): {translation}

Пример для слова "Hund" (собака):
"Ein Tier mit vier Beinen, das oft als Haustier gehalten wird und als bester Freund des Menschen gilt." """


DEFAULT_SENTENCE_PROMPT = """Создай {count} пример(а/ов) предложения с использованием слова '{word}' на языке {language}.

Требования:
- Предложения должны быть на языке {language}
- Предложения должны быть естественными и вседневными
- Используй слово '{word}' в разных контекстах
- Длина предложений: 5-15 слов
- Используй современную разговорную речь
- Контекст: {context}

Перевод слова (только для контекста): {translation}

Формат ответа: Одно предложение на строку. Без нумерации. Без дополнительных комментариев.

Пример для слова "Haus" (дом, count=3):
Ich wohne in einem großen Haus mit einem Garten.
Das Haus hat drei Stockwerke und einen Balkon.
Wir haben gestern das Haus gekauft."""


DEFAULT_SYNONYM_PROMPT = """Найди синоним для слова '{word}' на языке {language}.

Требования:
- Синоним должен быть на том же языке ({language})
- Синоним должен иметь похожее, но не идентичное значение
- Синоним должен быть распространенным словом
- Предпочтительно использовать синонимы из той же части речи

Текущее слово: {word}
Перевод: {translation}

Формат ответа (ОБЯЗАТЕЛЬНО):
СИНОНИМ|ПЕРЕВОД_СИНОНИМА

Пример для слова "Haus" (дом):
Gebäude|здание"""


def get_etymology_prompt(user: Optional[User] = None) -> str:
    """
    Получает промпт для генерации этимологии
    
    Args:
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Промпт для генерации этимологии
    """
    if user:
        # Используем систему пользовательских промптов (аналогично изображениям)
        try:
            from apps.cards.prompt_utils import get_user_prompt
            prompt = get_user_prompt(user, 'etymology', use_default_if_not_exists=False)
            if prompt:
                return prompt
        except Exception:
            pass
    
    return DEFAULT_ETYMOLOGY_PROMPT


def get_hint_prompt(user: Optional[User] = None) -> str:
    """
    Получает промпт для генерации подсказки
    
    Args:
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Промпт для генерации подсказки
    """
    if user:
        try:
            from apps.cards.prompt_utils import get_user_prompt
            prompt = get_user_prompt(user, 'hint', use_default_if_not_exists=False)
            if prompt:
                return prompt
        except Exception:
            pass
    
    return DEFAULT_HINT_PROMPT


def get_sentence_prompt(user: Optional[User] = None) -> str:
    """
    Получает промпт для генерации предложений
    
    Args:
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Промпт для генерации предложений
    """
    if user:
        try:
            from apps.cards.prompt_utils import get_user_prompt
            prompt = get_user_prompt(user, 'sentence', use_default_if_not_exists=False)
            if prompt:
                return prompt
        except Exception:
            pass
    
    return DEFAULT_SENTENCE_PROMPT


def get_synonym_prompt(user: Optional[User] = None) -> str:
    """
    Получает промпт для генерации синонима
    
    Args:
        user: Пользователь (для получения пользовательского промпта)
    
    Returns:
        Промпт для генерации синонима
    """
    if user:
        try:
            from apps.cards.prompt_utils import get_user_prompt
            prompt = get_user_prompt(user, 'synonym', use_default_if_not_exists=False)
            if prompt:
                return prompt
        except Exception:
            pass
    
    return DEFAULT_SYNONYM_PROMPT


def format_prompt(template: str, **kwargs) -> str:
    """
    Форматирует промпт с подстановкой переменных
    
    Args:
        template: Шаблон промпта с плейсхолдерами
        **kwargs: Переменные для подстановки
    
    Returns:
        Отформатированный промпт
    """
    return template.format(**kwargs)
