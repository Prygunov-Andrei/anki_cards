#!/usr/bin/env python3
"""
Скрипт для исправления путей к изображениям в базе данных.
Исправляет полные URL от ngrok на относительные пути.
"""
import os
import sys
import django

# Настройка Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.words.models import Word
from django.conf import settings
from urllib.parse import urlparse

def fix_image_paths():
    """Исправляет пути к изображениям в базе данных."""
    print("🔍 Проверка путей к изображениям...")
    
    # Слова с полными URL от ngrok
    words_with_ngrok = Word.objects.filter(image_file__startswith='https://')
    print(f"📊 Найдено слов с ngrok URL: {words_with_ngrok.count()}")
    
    # Слова с относительными путями
    words_with_relative = Word.objects.filter(image_file__startswith='images/')
    print(f"📊 Найдено слов с относительными путями: {words_with_relative.count()}")
    
    # Слова без изображений
    words_without = Word.objects.filter(image_file__isnull=True)
    print(f"📊 Слов без изображений: {words_without.count()}")
    
    fixed_count = 0
    not_found_count = 0
    
    print("\n🔧 Исправление путей...")
    
    for word in words_with_ngrok:
        try:
            # Парсим URL
            url = urlparse(word.image_file.name)
            # Извлекаем путь: /media/images/xxx.jpg -> images/xxx.jpg
            relative_path = url.path.lstrip('/media/')
            if not relative_path.startswith('images/'):
                relative_path = f"images/{relative_path.split('/')[-1]}"
            
            # Проверяем существование файла
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            if os.path.exists(full_path):
                # Обновляем путь
                word.image_file.name = relative_path
                word.save(update_fields=['image_file'])
                fixed_count += 1
                if fixed_count <= 5:
                    print(f"  ✅ {word.original_word}: {word.image_file.name[:60]}")
            else:
                not_found_count += 1
                if not_found_count <= 5:
                    print(f"  ❌ Файл не найден: {relative_path}")
        except Exception as e:
            print(f"  ⚠️ Ошибка при обработке слова {word.id}: {e}")
    
    print(f"\n✅ Исправлено путей: {fixed_count}")
    print(f"❌ Файлов не найдено: {not_found_count}")
    
    # Проверяем относительные пути
    print("\n🔍 Проверка относительных путей...")
    missing_files = []
    for word in words_with_relative[:100]:  # Проверяем первые 100
        full_path = os.path.join(settings.MEDIA_ROOT, word.image_file.name)
        if not os.path.exists(full_path):
            missing_files.append(word)
            if len(missing_files) <= 5:
                print(f"  ❌ Файл не найден: {word.image_file.name}")
    
    if missing_files:
        print(f"\n⚠️ Найдено {len(missing_files)} слов с несуществующими файлами")
    else:
        print("✅ Все относительные пути корректны")

if __name__ == '__main__':
    fix_image_paths()

