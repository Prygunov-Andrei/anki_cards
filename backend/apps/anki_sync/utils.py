"""
Утилиты для работы с синхронизацией Anki
"""
import logging
import sqlite3
import zipfile
import json
from pathlib import Path
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def get_user_collection_path(user) -> Path:
    """
    Получает путь к SQLite базе данных коллекции Anki для пользователя
    """
    sync_base = Path(settings.MEDIA_ROOT) / 'anki_sync'
    sync_base.mkdir(parents=True, exist_ok=True)
    
    # Создаем директорию для пользователя
    user_dir = sync_base / str(user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Путь к базе данных коллекции
    collection_path = user_dir / 'collection.anki2'
    
    # Если база не существует, создаем пустую
    if not collection_path.exists():
        create_empty_collection(collection_path)
    
    return collection_path


def create_empty_collection(collection_path: Path):
    """
    Создает пустую SQLite базу данных коллекции Anki
    """
    # TODO: Реализовать создание пустой коллекции Anki
    # Это требует знания структуры базы данных Anki
    logger.info(f"Creating empty collection at {collection_path}")
    
    # Базовая структура SQLite базы Anki
    conn = sqlite3.connect(str(collection_path))
    cursor = conn.cursor()
    
    # Создаем основные таблицы (упрощенная версия)
    # В реальности структура базы Anki очень сложная
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS col (
            id INTEGER PRIMARY KEY,
            crt INTEGER,
            mod INTEGER,
            scm INTEGER,
            ver INTEGER,
            dty INTEGER,
            usn INTEGER,
            ls INTEGER,
            conf TEXT,
            models TEXT,
            decks TEXT,
            dconf TEXT,
            tags TEXT
        )
    ''')
    
    # Вставляем начальные данные
    cursor.execute('''
        INSERT INTO col (id, crt, mod, scm, ver, dty, usn, ls, conf, models, decks, dconf, tags)
        VALUES (1, 0, 0, 0, 11, 0, 0, 0, '{}', '{}', '{}', '{}', '{}')
    ''')
    
    conn.commit()
    conn.close()
    
    logger.info(f"Empty collection created at {collection_path}")


def import_apkg_to_anki_collection(user, apkg_path: Path) -> Dict:
    """
    Импортирует .apkg файл в базу данных коллекции Anki пользователя
    
    Args:
        user: Пользователь Django
        apkg_path: Путь к .apkg файлу
    
    Returns:
        Dict с результатами импорта
    """
    if not apkg_path.exists():
        raise FileNotFoundError(f"APKG file not found: {apkg_path}")
    
    collection_path = get_user_collection_path(user)
    
    # TODO: Реализовать импорт .apkg в коллекцию
    # Это требует:
    # 1. Распаковки .apkg файла (это ZIP архив)
    # 2. Извлечения SQLite базы данных из архива
    # 3. Слияния данных с существующей коллекцией
    # 4. Импорта медиафайлов
    
    logger.info(f"Importing {apkg_path} to collection {collection_path}")
    
    # Временная реализация - просто логируем
    # Для полной реализации нужно использовать библиотеку anki
    # или напрямую работать с SQLite базой
    
    try:
        # Открываем .apkg как ZIP архив
        with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
            # .apkg содержит:
            # - collection.anki2 (SQLite база)
            # - media (JSON файл с медиа)
            # - медиафайлы
            
            # Извлекаем информацию о медиа
            if 'media' in zip_ref.namelist():
                media_data = json.loads(zip_ref.read('media').decode('utf-8'))
                logger.info(f"Media files in APKG: {list(media_data.keys())}")
            
            # TODO: Реализовать импорт в коллекцию
            # Это сложная операция, требующая знания структуры базы Anki
        
        return {
            'success': True,
            'collection_path': str(collection_path),
            'apkg_path': str(apkg_path)
        }
    
    except Exception as e:
        logger.error(f"Error importing APKG: {str(e)}", exc_info=True)
        raise

