"""
Заводские промпты по умолчанию для различных типов операций
"""

# Три режима генерации изображений
IMAGE_PROMPTS = {
    'minimalistic': """Простое, чистое, минималистичное изображение, иллюстрирующее: {translation}. Только один основной объект, без лишних деталей, на светлом фоне. СТРОГО, ОЧЕНЬ ВАЖНО БЕЗ текста, букв, цифр и любых символов.""",
    'balanced': """Выразительная иллюстрация, ясно передающая смысл слова: {translation}. Стиль — нейтральный, умеренно детализированный, с естественными цветами.

Фон может быть светлым или ненавязчивым. СТРОГО, ОЧЕНЬ ВАЖНО БЕЗ текста, букв, цифр и любых символов.""",
    'creative': """Создай яркую, сочную иллюстрацию, которая помогает запомнить значение слова: {translation}. Стиль свободный — может быть минимализм, рисованный арт, живопись, 3D или реалистичность. Разнообразная цветовая палитра, красивый свет, приятные детали. СТРОГО, ОЧЕНЬ ВАЖНО БЕЗ текста, букв, цифр и любых символов.""",
}

DEFAULT_PROMPTS = {
    'image': IMAGE_PROMPTS['balanced'],  # По умолчанию используем сбалансированный режим
    
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
    
    'category': """Определи категорию для слова '{word}' на языке {language}.
Верни JSON: {{'category': 'название_категории'}}""",
    
    'language_detection': """Определи язык слова '{word}'. 
Верни ТОЛЬКО код языка: 'ru' (русский), 'pt' (португальский), 'de' (немецкий), 'en' (английский).
Если не уверен, верни наиболее вероятный код.""",
    
    'word_analysis': """Дан список слов: {words_list}
Определи, какие слова на изучаемом языке ({learning_language}), а какие на родном языке ({native_language}).
Верни ТОЛЬКО JSON без дополнительного текста в формате: {{"слово_на_изучаемом": "перевод_на_родном"}}
Если слово уже на родном языке, не включай его в результат.""",
    
    'translation': """Переведи следующие слова с {learning_language} на {native_language}: {words_list}
Верни ТОЛЬКО JSON без дополнительного текста в формате: {{"слово": "перевод"}}""",
    
    'german_word_processing': """Обработай немецкое слово '{word}':
1. Если это существительное - добавь правильный артикль (der/die/das) и напиши с заглавной буквы
2. Если это глагол или другое - оставь без артикля, но исправь регистр если нужно
3. Если это предложение или словосочетание (содержит несколько слов) - верни его БЕЗ ИЗМЕНЕНИЙ
Верни ТОЛЬКО обработанное слово без дополнительного текста.""",
    
    'deck_name': """На основе списка слов на {learning_language} сгенерируй 
краткое и понятное название колоды на {native_language}.
Учти категории и тематику слов. Название должно быть коротким (2-4 слова).
Верни ТОЛЬКО название без дополнительного текста.""",
    
    'category': """Определи категорию для списка слов на языке {language}: {words_list}
Верни ТОЛЬКО название категории на {native_language} без дополнительного текста.
Примеры категорий: Еда, Спорт, Природа, Технологии, Одежда, Дом, Транспорт, Животные, Цвета, Числа и т.д.""",
}


def get_default_prompt(prompt_type: str, image_style: str = 'balanced') -> str:
    """
    Получает заводской промпт по типу
    
    Args:
        prompt_type: Тип промпта (image, audio, word_analysis, и т.д.)
        image_style: Стиль генерации изображения (minimalistic, balanced, creative)
                     Используется только для prompt_type='image'
    
    Returns:
        Заводской промпт или пустая строка, если тип не найден
    """
    if prompt_type == 'image':
        return IMAGE_PROMPTS.get(image_style, IMAGE_PROMPTS['balanced'])
    return DEFAULT_PROMPTS.get(prompt_type, '')


def get_image_prompt_for_style(image_style: str = 'balanced') -> str:
    """
    Получает промпт для генерации изображения по стилю
    
    Args:
        image_style: Стиль генерации (minimalistic, balanced, creative)
    
    Returns:
        Промпт для выбранного стиля или сбалансированный по умолчанию
    """
    return IMAGE_PROMPTS.get(image_style, IMAGE_PROMPTS['balanced'])


def format_prompt(
    prompt_template: str,
    word: str = None,
    translation: str = None,
    language: str = None,
    native_language: str = None,
    learning_language: str = None,
    english_translation: str = None,
    words_list: str = None
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
        words_list: Список слов (строка)
    
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
        '{words_list}': words_list or '',
    }
    
    for placeholder, value in replacements.items():
        formatted = formatted.replace(placeholder, value)
    
    return formatted

