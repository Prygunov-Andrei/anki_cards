# Документация по серверу синхронизации Anki

## Текущее состояние

Создана базовая структура для сервера синхронизации Anki:

### Что реализовано:

1. **Django приложение `anki_sync`**
   - Модели для хранения данных синхронизации (`AnkiSyncUser`, `AnkiSyncMedia`)
   - Базовые views для обработки запросов синхронизации
   - Утилиты для работы с базами данных Anki

2. **Интеграция с созданием колод**
   - При создании колоды автоматически вызывается импорт в базу синхронизации
   - Функция `import_apkg_to_anki_collection()` вызывается после генерации .apkg файла

3. **Базовые endpoints**
   - `/sync/` - основной endpoint для синхронизации
   - `/api/sync/import/` - API для ручного импорта колод

### Что нужно доработать:

#### 1. Установка библиотеки `anki`

Для работы с базами данных Anki нужно установить библиотеку:

```bash
cd backend
source venv/bin/activate
pip install anki
```

**Важно:** Библиотека `anki` - это полный код Anki на Python, она довольно большая и может иметь зависимости.

#### 2. Реализация протокола синхронизации

Протокол синхронизации Anki не полностью документирован. Нужно изучить исходный код:

- **Исходный код Anki:** https://github.com/ankitects/anki
- **Сервер синхронизации (Rust):** https://github.com/ankitects/anki/tree/main/rslib/src/sync
- **Сервер синхронизации (Python):** Встроен в библиотеку `anki` как `anki.syncserver`

Основные методы синхронизации:
- `meta` - получение метаданных
- `start` - начало синхронизации
- `applyGraves` - применение удалений
- `applyChanges` - применение изменений
- `chunk` - получение чанка данных
- `applyChunk` - применение чанка данных
- `sanitize` - санитизация данных

#### 3. Реализация импорта .apkg в коллекцию

Текущая функция `import_apkg_to_anki_collection()` - заглушка. Нужно реализовать:

```python
# Используя библиотеку anki
from anki.collection import Collection
from anki.importing import AnkiPackageImporter

def import_apkg_to_anki_collection(user, apkg_path):
    collection_path = get_user_collection_path(user)
    col = Collection(collection_path)
    
    # Импортируем .apkg файл
    importer = AnkiPackageImporter(col, str(apkg_path))
    importer.run()
    
    col.close()
```

#### 4. Аутентификация

Anki использует HTTP Basic Authentication. Нужно реализовать:

```python
from django.contrib.auth import authenticate
import base64

def get_basic_auth_user(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Basic '):
        return None
    
    # Декодируем credentials
    encoded = auth_header.split(' ')[1]
    decoded = base64.b64decode(encoded).decode('utf-8')
    username, password = decoded.split(':', 1)
    
    # Проверяем пользователя
    user = authenticate(username=username, password=password)
    return user
```

#### 5. Хранение медиафайлов

Нужно реализовать хранение и синхронизацию медиафайлов:
- Хранение медиафайлов в директории пользователя
- Синхронизация медиа через `/sync/media/` endpoint
- Управление версиями медиафайлов

## Альтернативный подход

Вместо полной реализации протокола синхронизации можно:

1. **Использовать готовый сервер синхронизации**
   - Запустить отдельный сервер синхронизации (Python или Rust версия)
   - Интегрировать его с Django через API
   - Настроить общее хранилище данных

2. **Использовать AnkiConnect**
   - Установить плагин AnkiConnect на десктопное приложение
   - Использовать REST API для создания карточек
   - Но это не решает проблему синхронизации с мобильным приложением

3. **Упрощенная синхронизация**
   - При создании колоды - автоматически импортировать в базу
   - Предоставлять .apkg файлы для ручного импорта
   - Использовать стандартный AnkiWeb для синхронизации

## Настройка клиента Anki

После реализации сервера синхронизации нужно настроить клиенты:

### Anki Desktop (2.1.57+)
1. Открыть "Инструменты" → "Параметры" → "Синхронизация"
2. В поле "Самостоятельно размещаемый сервер синхронизации" ввести: `http://ваш-сервер:8000/sync/`
3. Перезапустить Anki

### AnkiMobile (iOS)
1. Настройки → Дополнительно → Пользовательский сервер синхронизации
2. Ввести URL сервера
3. Убедиться, что включен доступ к локальной сети

### AnkiDroid (Android)
1. Настройки → Дополнительно → Пользовательский сервер синхронизации
2. Ввести URL сервера

## Безопасность

⚠️ **Важно:** Текущая реализация использует незашифрованное HTTP соединение. Для продакшена нужно:

1. Настроить HTTPS (через nginx или другой reverse proxy)
2. Использовать токены аутентификации вместо Basic Auth
3. Ограничить доступ к серверу синхронизации
4. Регулярно обновлять сервер и клиенты

## Следующие шаги

1. Установить библиотеку `anki` и изучить её API
2. Реализовать полный протокол синхронизации
3. Протестировать с реальными клиентами Anki
4. Настроить безопасность для продакшена
5. Добавить мониторинг и логирование

## Полезные ссылки

- [Документация Anki](https://docs.ankiweb.net/)
- [Исходный код Anki](https://github.com/ankitects/anki)
- [Anki Sync Server (Rust)](https://github.com/yangchuansheng/anki-sync-server)
- [Anki Sync Server (Python)](https://github.com/tsudoko/anki-sync-server)

