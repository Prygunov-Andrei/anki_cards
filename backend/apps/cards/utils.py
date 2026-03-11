"""
Утилиты для генерации карточек Anki
"""
import random
import uuid
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
from genanki import Deck, Note, Model, Package

logger = logging.getLogger(__name__)


def create_card_model() -> Model:
    """
    Создает модель карточек для двусторонних карточек
    """
    model_id = random.randrange(1 << 30, 1 << 31)
    
    model = Model(
        model_id=model_id,
        name="Двусторонние карточки",
        fields=[
            {"name": "OriginalWord"},
            {"name": "Translation"},
            {"name": "Audio"},
            {"name": "Image"},
            {"name": "Hint"},
            {"name": "ExampleSentence"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{OriginalWord}}<br>{{Image}}",
                "afmt": (
                    "{{OriginalWord}}<br>{{Image}}<br>{{Audio}}<br>{{Translation}}"
                    "{{#Hint}}<br><hr><div style='font-style:italic;color:#666;font-size:0.9em;'>{{Hint}}</div>{{/Hint}}"
                    "{{#ExampleSentence}}<br><div style='font-size:0.85em;color:#555;'>{{ExampleSentence}}</div>{{/ExampleSentence}}"
                ),
            },
            {
                "name": "Card 2",
                "qfmt": "{{Translation}}<br>{{Image}}",
                "afmt": (
                    "{{Translation}}<br>{{Image}}<br>{{OriginalWord}}<br>{{Audio}}"
                    "{{#Hint}}<br><hr><div style='font-style:italic;color:#666;font-size:0.9em;'>{{Hint}}</div>{{/Hint}}"
                    "{{#ExampleSentence}}<br><div style='font-size:0.85em;color:#555;'>{{ExampleSentence}}</div>{{/ExampleSentence}}"
                ),
            },
        ],
    )
    
    return model


def create_deck(deck_name: str) -> Deck:
    """
    Создает колоду карточек с указанным названием
    """
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = Deck(deck_id=deck_id, name=deck_name)
    return deck


def generate_apkg(
    words_data: List[Dict],
    deck_name: str,
    media_files: Optional[List[str]] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Генерирует .apkg файл с карточками Anki
    
    Args:
        words_data: Список словарей с данными слов:
            - original_word: исходное слово
            - translation: перевод
            - audio_file: путь к аудиофайлу (опционально)
            - image_file: путь к изображению (опционально)
        deck_name: Название колоды
        media_files: Список путей к медиафайлам
        output_path: Путь для сохранения .apkg файла
    
    Returns:
        Path к созданному .apkg файлу
    
    Note:
        Слова автоматически перемешиваются в случайном порядке перед добавлением в колоду.
    """
    # Создаем модель карточек
    model = create_card_model()
    
    # Создаем колоду
    deck = create_deck(deck_name)
    
    # Перемешиваем слова в случайном порядке перед добавлением в колоду
    shuffled_words = words_data.copy()  # Создаем копию, чтобы не изменять исходный список
    random.shuffle(shuffled_words)
    logger.info(f"🔀 Слова перемешаны в случайном порядке для колоды '{deck_name}'")
    
    # Отделяем пустые карточки и ставим их в конец
    empty_cards = []
    non_empty_cards = []
    for word_data in shuffled_words:
        card_type = word_data.get('card_type', 'normal')
        if card_type == 'empty':
            empty_cards.append(word_data)
        else:
            non_empty_cards.append(word_data)
    
    # Формируем финальный список: сначала непустые карточки, затем пустые
    final_words_order = non_empty_cards + empty_cards
    logger.info(f"📋 Порядок карточек: {len(non_empty_cards)} обычных + {len(empty_cards)} пустых (в конце)")
    
    # Добавляем записи для каждого слова
    for word_data in final_words_order:
        original_word = word_data.get('original_word', '')
        translation = word_data.get('translation', '')
        
        # Определяем display_word в зависимости от типа карточки
        # Для пустых карточек показываем пустую строку, для остальных - original_word
        card_type = word_data.get('card_type', 'normal')
        if card_type == 'empty':
            display_word = ''  # Пустые карточки показывают пустую строку
        else:
            display_word = original_word
        
        # Формируем поля для карточки
        audio_field = ''
        if word_data.get('audio_file'):
            audio_filename = Path(word_data['audio_file']).name
            audio_field = f'[sound:{audio_filename}]'
        
        image_field = ''
        if word_data.get('image_file'):
            image_filename = Path(word_data['image_file']).name
            image_field = f'<img src="{image_filename}">'
        
        hint_field = word_data.get('hint', '')
        sentence_field = word_data.get('example_sentence', '')

        # Создаем запись (Note)
        note = Note(
            model=model,
            fields=[
                display_word,  # Используем display_word вместо original_word
                translation,
                audio_field,
                image_field,
                hint_field,
                sentence_field,
            ]
        )
        deck.add_note(note)
    
    # Собираем все медиафайлы из финального списка слов (с пустыми карточками в конце)
    all_media_files = []
    seen_files = set()  # Для отслеживания уже добавленных файлов
    
    # Получаем MEDIA_ROOT для преобразования относительных путей
    from django.conf import settings
    media_root = Path(settings.MEDIA_ROOT)
    
    for word_data in final_words_order:
        # Обработка аудио
        if word_data.get('audio_file'):
            audio_path = Path(word_data['audio_file'])
            # Преобразуем в абсолютный путь, если нужно
            if not audio_path.is_absolute():
                audio_path = media_root / audio_path
            else:
                audio_path = audio_path.resolve()
            
            audio_str = str(audio_path)
            if audio_path.exists():
                if audio_str not in seen_files:
                    all_media_files.append(audio_str)
                    seen_files.add(audio_str)
                    logger.info(f"✅ Добавлен аудиофайл: {audio_str}")
                else:
                    logger.debug(f"⚠️ Аудиофайл уже добавлен: {audio_str}")
            else:
                logger.warning(f"❌ Аудиофайл не найден: {audio_str}")
        
        # Обработка изображений
        if word_data.get('image_file'):
            image_path = Path(word_data['image_file'])
            # Преобразуем в абсолютный путь, если нужно
            if not image_path.is_absolute():
                image_path = media_root / image_path
            else:
                image_path = image_path.resolve()
            
            image_str = str(image_path)
            if image_path.exists():
                if image_str not in seen_files:
                    all_media_files.append(image_str)
                    seen_files.add(image_str)
                    logger.info(f"✅ Добавлен файл изображения: {image_str}")
                else:
                    logger.debug(f"⚠️ Файл изображения уже добавлен: {image_str}")
            else:
                logger.warning(f"❌ Файл изображения не найден: {image_str}")
    
    # Добавляем медиафайлы из параметра media_files (если есть)
    if media_files:
        for media_file in media_files:
            media_path = Path(media_file)
            # Преобразуем в абсолютный путь, если нужно
            if not media_path.is_absolute():
                media_path = media_root / media_path
            else:
                media_path = media_path.resolve()
            
            media_str = str(media_path)
            if media_path.exists():
                if media_str not in seen_files:
                    all_media_files.append(media_str)
                    seen_files.add(media_str)
                    logger.info(f"✅ Добавлен медиафайл из параметра: {media_str}")
                else:
                    logger.debug(f"⚠️ Медиафайл уже добавлен: {media_str}")
            else:
                logger.warning(f"❌ Медиафайл не найден: {media_str}")
    
    logger.info(f"📦 Всего медиафайлов для добавления в .apkg: {len(all_media_files)}")
    if all_media_files:
        logger.info(f"📋 Список медиафайлов: {all_media_files}")
    else:
        logger.warning("⚠️ Медиафайлы не найдены! .apkg будет создан без медиа.")
    
    # Создаем пакет с медиафайлами
    package = Package(deck, media_files=all_media_files if all_media_files else None)
    
    # Генерируем уникальное имя файла, если не указано
    if output_path is None:
        file_id = str(uuid.uuid4())
        output_path = Path(f"temp_files/{file_id}.apkg")
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Генерируем .apkg файл
    package.write_to_file(str(output_path))
    
    return output_path


def parse_words_input(text: str) -> List[str]:
    """
    Умный парсинг ввода слов: разбивает строку по точкам с запятой/переносам,
    определяет словосочетания (по заглавной букве), чистит мусор.
    
    Args:
        text: Строка с вводом слов (через точку с запятой, с переносами строк)
    
    Returns:
        Список слов/словосочетаний (очищенных от лишних символов)
    
    Примеры:
        "casa; tempo; vida" -> ["casa", "tempo", "vida"]
        "casa; Carro novo; vida" -> ["casa", "Carro novo", "vida"]
        "casa\ntempo\nvida" -> ["casa", "tempo", "vida"]
    """
    if not text or not text.strip():
        return []
    
    # Заменяем переносы строк на точку с запятой для единообразной обработки
    text = text.replace('\n', ';').replace('\r', ';')
    
    # Разбиваем по точкам с запятой
    parts = text.split(';')
    
    words = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Убираем точки в конце (но не внутри слова)
        part = re.sub(r'\.$', '', part).strip()
        
        if not part:
            continue
        
        # Добавляем слово как есть (не объединяем автоматически)
        # Если слова разделены точкой с запятой, они уже правильно разделены
        words.append(part)
    
    # Очищаем от лишних пробелов и пустых строк
    words = [w.strip() for w in words if w.strip()]
    
    # Убираем дубликаты, сохраняя порядок
    seen = set()
    unique_words = []
    for word in words:
        if word.lower() not in seen:
            seen.add(word.lower())
            unique_words.append(word)
    
    return unique_words

