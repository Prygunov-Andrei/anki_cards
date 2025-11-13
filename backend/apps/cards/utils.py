"""
Утилиты для генерации карточек Anki
"""
import random
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from genanki import Deck, Note, Model, Package


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
            {"name": "Image"}
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{OriginalWord}}<br>{{Image}}",
                "afmt": "{{OriginalWord}}<br>{{Image}}<br>{{Audio}}<br>{{Translation}}"
            },
            {
                "name": "Card 2",
                "qfmt": "{{Translation}}<br>{{Image}}",
                "afmt": "{{Translation}}<br>{{Image}}<br>{{OriginalWord}}<br>{{Audio}}"
            }
        ]
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
    """
    # Создаем модель карточек
    model = create_card_model()
    
    # Создаем колоду
    deck = create_deck(deck_name)
    
    # Добавляем записи для каждого слова
    for word_data in words_data:
        original_word = word_data.get('original_word', '')
        translation = word_data.get('translation', '')
        
        # Формируем поля для карточки
        audio_field = ''
        if word_data.get('audio_file'):
            audio_filename = Path(word_data['audio_file']).name
            audio_field = f'[sound:{audio_filename}]'
        
        image_field = ''
        if word_data.get('image_file'):
            image_filename = Path(word_data['image_file']).name
            image_field = f'<img src="{image_filename}">'
        
        # Создаем запись (Note)
        note = Note(
            model=model,
            fields=[
                original_word,
                translation,
                audio_field,
                image_field
            ]
        )
        deck.add_note(note)
    
    # Собираем все медиафайлы из words_data
    all_media_files = []
    for word_data in words_data:
        if word_data.get('audio_file'):
            audio_path = Path(word_data['audio_file'])
            if audio_path.exists() and str(audio_path) not in all_media_files:
                all_media_files.append(str(audio_path))
        if word_data.get('image_file'):
            image_path = Path(word_data['image_file'])
            if image_path.exists() and str(image_path) not in all_media_files:
                all_media_files.append(str(image_path))
    
    # Добавляем медиафайлы из параметра media_files (если есть)
    if media_files:
        for media_file in media_files:
            media_path = Path(media_file)
            if media_path.exists() and str(media_path) not in all_media_files:
                all_media_files.append(str(media_path))
    
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

