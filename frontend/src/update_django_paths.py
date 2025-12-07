#!/usr/bin/env python3
"""
Скрипт для автоматического обновления путей в index.html для Django
Использование: python update_django_paths.py /path/to/django/templates/index.html
"""

import sys
import re
from pathlib import Path


def update_index_html(file_path: str) -> None:
    """
    Обновляет пути в index.html для совместимости с Django static tags
    
    Args:
        file_path: Путь к файлу index.html
    """
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ Файл не найден: {file_path}")
        sys.exit(1)
    
    print(f"📄 Обрабатываю: {file_path}")
    
    # Читаем содержимое
    content = path.read_text(encoding='utf-8')
    original_content = content
    
    # 1. Добавляем {% load static %} в начало если его нет
    if '{% load static %}' not in content:
        content = '{% load static %}\n' + content
        print("✅ Добавлен {% load static %}")
    
    # 2. Заменяем пути к assets
    # Находим все src="/assets/..." и href="/assets/..."
    patterns = [
        # src="/assets/index-abc123.js" -> src="{% static 'assets/index-abc123.js' %}"
        (r'src="/assets/([^"]+)"', r'src="{% static \'assets/\1\' %}"'),
        
        # href="/assets/index-xyz789.css" -> href="{% static 'assets/index-xyz789.css' %}"
        (r'href="/assets/([^"]+)"', r'href="{% static \'assets/\1\' %}"'),
        
        # src="/vite.svg" -> src="{% static 'vite.svg' %}"
        (r'src="/vite\.svg"', r'src="{% static \'vite.svg\' %}"'),
        (r'href="/vite\.svg"', r'href="{% static \'vite.svg\' %}"'),
    ]
    
    replacements = 0
    for pattern, replacement in patterns:
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            content = new_content
            replacements += count
            print(f"✅ Заменено {count} вхождений: {pattern}")
    
    # 3. Проверяем изменения
    if content == original_content:
        print("ℹ️  Файл уже обновлён, изменений не требуется")
        return
    
    # 4. Создаём резервную копию
    backup_path = path.with_suffix('.html.backup')
    backup_path.write_text(original_content, encoding='utf-8')
    print(f"💾 Создана резервная копия: {backup_path}")
    
    # 5. Сохраняем обновлённый файл
    path.write_text(content, encoding='utf-8')
    print(f"✅ Файл обновлён! Всего замен: {replacements}")
    
    # 6. Показываем примеры изменений
    print("\n📋 Примеры изменений:")
    lines = content.split('\n')
    for i, line in enumerate(lines[:20], 1):  # Первые 20 строк
        if '{% static' in line:
            print(f"  Строка {i}: {line.strip()}")


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python update_django_paths.py /path/to/index.html")
        print("\nПример:")
        print("  python update_django_paths.py /home/user/django/templates/index.html")
        sys.exit(1)
    
    file_path = sys.argv[1]
    update_index_html(file_path)
    
    print("\n✅ Готово! Теперь можно запустить collectstatic:")
    print("   cd /path/to/django")
    print("   python manage.py collectstatic --noinput")


if __name__ == '__main__':
    main()
