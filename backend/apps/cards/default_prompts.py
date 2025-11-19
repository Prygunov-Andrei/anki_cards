"""
Заводские промпты по умолчанию для различных типов операций
"""

DEFAULT_PROMPTS = {
    'image': """Простое, четкое изображение слова '{word}' ({translation} на {native_language}). 
Стиль: минималистичный, образовательный, без текста.
В яркой желтой подложке мелко написать английский перевод '{english_translation}'.
Никаких других надписей или символов.
Для абстрактных понятий используй символы, метафоры или визуализацию.""",
    
    'audio': """Произнеси слово '{word}' на языке {language} четко и понятно.""",
    
    'word_analysis': """Ты получаешь список слов на разных языках.
Определи, какие слова на языке изучения ({learning_language}), 
а какие на родном языке ({native_language}).
Верни JSON с парами: {{'слово_на_изучаемом': 'перевод_на_родном'}}""",
    
    'translation': """Переведи следующие слова с {learning_language} на {native_language}.
Верни JSON: {{'слово': 'перевод'}}""",
    
    'deck_name': """На основе списка слов на {learning_language} сгенерируй 
краткое и понятное название колоды на {native_language}.
Учти категории и тематику слов.""",
    
    'part_of_speech': """Определи часть речи для слова '{word}' на языке {language}.
Для немецкого языка также определи артикль.
Верни JSON: {{'part_of_speech': '...', 'article': 'der|die|das' (только для немецкого)}}""",
    
    'category': """Определи категорию для слова '{word}' на языке {language}.
Верни JSON: {{'category': 'название_категории'}}""",
}


def get_default_prompt(prompt_type: str) -> str:
    """
    Получает заводской промпт по типу
    
    Args:
        prompt_type: Тип промпта (image, audio, word_analysis, и т.д.)
    
    Returns:
        Заводской промпт или пустая строка, если тип не найден
    """
    return DEFAULT_PROMPTS.get(prompt_type, '')


def format_prompt(
    prompt_template: str,
    word: str = None,
    translation: str = None,
    language: str = None,
    native_language: str = None,
    learning_language: str = None,
    english_translation: str = None
) -> str:
    """
    Форматирует промпт, заменяя плейсхолдеры на реальные значения
    
    Args:
        prompt_template: Шаблон промпта с плейсхолдерами
        word: Слово
        translation: Перевод слова
        language: Язык слова
        native_language: Родной язык пользователя
        learning_language: Язык изучения
        english_translation: Английский перевод
    
    Returns:
        Отформатированный промпт
    """
    formatted = prompt_template
    
    # Заменяем плейсхолдеры
    replacements = {
        '{word}': word or '',
        '{translation}': translation or '',
        '{language}': language or '',
        '{native_language}': native_language or 'русском',
        '{learning_language}': learning_language or '',
        '{english_translation}': english_translation or translation or '',
    }
    
    for placeholder, value in replacements.items():
        formatted = formatted.replace(placeholder, value)
    
    return formatted

