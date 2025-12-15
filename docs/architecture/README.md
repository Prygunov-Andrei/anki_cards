# Архитектура приложения

## Общая архитектура

Приложение построено по принципу клиент-серверной архитектуры:

```
┌─────────────┐         HTTP/REST API         ┌─────────────┐
│   Frontend  │ ◄──────────────────────────► │   Backend   │
│   (React)   │                               │   (Django)  │
└─────────────┘                               └─────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────┐
                                              │  PostgreSQL │
                                              └─────────────┘
```

## Backend архитектура

### Структура приложений

```
backend/
├── apps/
│   ├── users/          # Аутентификация и управление пользователями
│   │   ├── models.py   # Модель User (расширение стандартной)
│   │   ├── views.py    # API views для регистрации/входа
│   │   ├── serializers.py
│   │   └── urls.py
│   │
│   ├── words/          # Управление словами
│   │   ├── models.py   # Модель Word
│   │   ├── views.py    # API для работы со словами
│   │   ├── serializers.py
│   │   └── urls.py
│   │
│   ├── cards/          # Генерация карточек Anki
│   │   ├── models.py   # GeneratedDeck, Deck, Token и др.
│   │   ├── views.py    # API для генерации .apkg
│   │   ├── utils.py    # Утилиты для работы с genanki
│   │   ├── llm_utils.py # Интеграция с OpenAI/Gemini
│   │   └── urls.py
│   │
│   └── anki_sync/      # Сервер синхронизации Anki
│       ├── models.py   # AnkiSyncUser, AnkiSyncMedia
│       ├── views.py    # Endpoints синхронизации
│       └── utils.py    # Работа с SQLite базами Anki
│
└── config/
    ├── settings.py     # Настройки Django
    └── urls.py         # Главный URL router
```

### Поток данных

#### 1. Регистрация/Вход

```
Frontend → POST /api/auth/register/
Backend → Создание пользователя
Backend → Генерация токена
Backend → Возврат токена
Frontend → Сохранение токена в localStorage
```

#### 2. Генерация медиафайлов

```
Frontend → POST /api/media/generate-image/ (с токеном)
Backend → Вызов OpenAI API (DALL-E 3) или Google Gemini
Backend → Сохранение медиафайла локально
Backend → Возврат URL к медиафайлу
Frontend → Предпросмотр медиафайла
```

#### 3. Генерация карточек

```
Frontend → POST /api/cards/generate/ (с токеном, словами, медиа)
Backend → Валидация данных
Backend → Сохранение слов в БД
Backend → Генерация .apkg через genanki
Backend → Импорт в базу синхронизации Anki (опционально)
Backend → Возврат ссылки на скачивание
Frontend → GET /api/cards/download/<file_id>/
Frontend → Скачивание файла
```

## База данных

### Схема

```
User
├── id (PK)
├── username
├── email
├── password (hashed)
├── preferred_language
├── native_language
├── learning_language
├── theme
├── mode
├── image_provider
├── audio_provider
└── created_at

Word
├── id (PK)
├── user (FK → User)
├── original_word
├── translation
├── language
├── audio_file (nullable)
├── image_file (nullable)
├── created_at
└── updated_at

Deck
├── id (PK)
├── user (FK → User)
├── name
├── target_lang
├── source_lang
├── cover (nullable)
├── words (M2M → Word)
├── created_at
└── updated_at

GeneratedDeck
├── id (PK, UUID)
├── user (FK → User)
├── deck_name
├── file_path
├── cards_count
└── created_at

Token
├── id (PK)
├── user (FK → User, OneToOne)
├── balance
├── created_at
└── updated_at

AnkiSyncUser
├── id (PK)
├── user (FK → User, OneToOne)
├── collection_path
├── host_key
├── last_sync_time
└── created_at
```

### Индексы

- `Word`: `(user, original_word, language)` - unique
- `Deck`: `(user, updated_at)`
- `GeneratedDeck`: `(user, created_at)`

## Формат файлов Anki (.apkg)

- **Один .apkg файл = одна колода карточек** (может содержать множество карточек)
- Файл .apkg представляет собой ZIP-архив, содержащий:
  - `collection.anki2` - SQLite база данных с карточками
  - `media` - JSON файл с метаданными медиафайлов
  - Медиафайлы (изображения, аудио)

### Структура .apkg

```
deck.apkg (ZIP)
├── collection.anki2 (SQLite)
├── media (JSON)
│   {
│     "image1.jpg": "abc123.jpg",
│     "audio1.mp3": "def456.mp3"
│   }
├── abc123.jpg
└── def456.mp3
```

## Модели для генерации медиа

### OpenAI

- **Изображения:** DALL-E 3 (`dall-e-3`)
  - Размер: 1024x1024
  - Формат: PNG/JPEG
- **Аудио:** TTS-1-HD (`tts-1-hd`)
  - Формат: MP3
  - Голос выбирается в зависимости от языка

### Google Gemini

- **Изображения:** Nano Banana Pro (`nano-banana-pro-preview`)
  - Размер: 1024x1024
  - Промпт формируется автоматически

### Google TTS (gTTS)

- **Аудио:** Google Text-to-Speech
  - Формат: MP3
  - Бесплатный альтернативный вариант

## Система токенов

Пользователи имеют баланс токенов для контроля использования ресурсов:

- **Генерация изображения (OpenAI):** 2 токена
- **Генерация изображения (Gemini):** 1 токен (0.5 токена для Flash)
- **Генерация аудио (OpenAI):** 1 токен
- **Генерация аудио (gTTS):** 0 токенов (бесплатно)

Токены начисляются при регистрации и могут быть добавлены администратором.

## Синхронизация Anki

Приложение поддерживает собственный сервер синхронизации Anki:

- Каждый пользователь имеет свою SQLite базу Anki на сервере
- При создании колоды она автоматически импортируется в базу
- Клиенты Anki могут синхронизироваться с сервером через `/sync/` endpoint

Подробнее: [Синхронизация Anki](../features/ANKI_SYNC.md)

## Безопасность

- Token-based аутентификация
- CORS настройки для фронтенда
- Валидация всех входных данных
- Хеширование паролей (Django)
- Защита от CSRF (Django)

## Масштабирование

### Текущая архитектура

- Монолитное Django приложение
- PostgreSQL для основных данных
- SQLite для синхронизации Anki (по пользователю)
- Локальное хранение медиафайлов

### Возможные улучшения

- Использование Redis для кэширования
- Очереди задач (Celery) для асинхронной генерации
- Облачное хранилище для медиафайлов (S3)
- Микросервисная архитектура для синхронизации Anki

