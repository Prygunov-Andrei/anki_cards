# Anki Card Generator (Backend)

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/Prygunov-Andrei/anki_cards)

Backend для веб-приложения автоматической генерации карточек Anki.

## Описание

Backend обеспечивает API для:
- Управления пользователями и аутентификации
- Генерации карточек Anki (.apkg)
- Интеграции с OpenAI (DALL-E 3, TTS-1-HD) и Google Gemini (Nano Banana) для генерации медиа
- Управления библиотекой слов

**Фронтенд:** Находится в стадии полной переработки (см. [План разработки](./docs/DEVELOPMENT_PLAN.md)).

## Документация

- **[План разработки Backend](./docs/DEVELOPMENT_PLAN.md)** — план Backend разработки (завершен)
- **[Техническое задание Frontend](./docs/FRONTEND_TASKS.md)** — полное ТЗ для Frontend разработчика (18 этапов)
- **[Деплой](./docs/DEPLOYMENT.md)** — информация о деплое (будет дополнено)

## Быстрый старт (Backend)

### Требования
- Python 3.10+
- PostgreSQL 12+ (или SQLite)

### Настройка переменных окружения (.env)

1. Скопируйте пример файла:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Обязательные переменные в `.env`:
   ```env
   # Секретный ключ Django
   SECRET_KEY=your_secret_key
   
   # OpenAI API Key (ОБЯЗАТЕЛЬНО для генерации медиа!)
   # Получить ключ: https://platform.openai.com/api-keys
   OPENAI_API_KEY=sk-proj-...
   
   # Google Gemini API Key (опционально, для альтернативной генерации изображений)
   # Получить ключ: https://ai.google.dev/
   GEMINI_API_KEY=AIzaSy...
   ```

3. Опциональные переменные:
   ```env
   # База данных (по умолчанию SQLite)
   # DATABASE_URL=postgresql://user:password@localhost:5432/anki_db
   
   # Отладка
   DEBUG=True
   
   # Хосты
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

### Запуск

```bash
./start.sh
```

Скрипт создаст виртуальное окружение, установит зависимости, применит миграции и запустит сервер на http://localhost:8000.

### Разработка с фронтендом (ngrok)

Для подключения облачного фронтенда (Figma Make) к локальному бэкенду используется **ngrok**:

```bash
# 1. Запустите бэкенд
./start.sh
# Django запустится на http://localhost:8000

# 2. Запустите ngrok туннель (в отдельном терминале)
ngrok http 8000
# ngrok выдаст публичный URL, например: https://f6c058cfd2ea.ngrok-free.app

# 3. Используйте публичный URL в настройках фронтенда:
# BASE_URL: 'https://f6c058cfd2ea.ngrok-free.app/api/'
```

> **Примечание:** ngrok URL меняется при каждом перезапуске. Текущий URL можно узнать:
> - В консоли ngrok
> - Через `curl http://localhost:4040/api/tunnels`

Подробнее см. [Техническое задание Frontend](./docs/FRONTEND_TASKS.md#подключение-к-backend-ngrok).

## Структура проекта

```
anki-card-generator/
├── backend/              # Django проект
├── docs/                 # Документация
│   ├── DEVELOPMENT_PLAN.md   # План Backend разработки
│   ├── FRONTEND_TASKS.md     # ТЗ для Frontend
│   └── DEPLOYMENT.md         # Информация о деплое
├── nginx/                # Конфигурация Nginx
│   ├── nginx.conf            # Production конфиг
│   └── nginx.dev.conf        # Development конфиг
├── start.sh              # Скрипт запуска бэкенда
└── README.md             # Этот файл
```

---

## Архитектура

### Общая архитектура

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

### Backend архитектура

#### Структура приложений

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
│   └── cards/          # Генерация карточек Anki
│       ├── views.py    # API для генерации .apkg
│       ├── utils.py    # Утилиты для работы с genanki
│       └── urls.py
│
└── config/
    ├── settings.py     # Настройки Django
    └── urls.py         # Главный URL router
```

#### Поток данных

1. **Регистрация/Вход:**
   - Frontend → POST `/api/auth/register/` или `/api/auth/login/`
   - Backend → Создание/проверка пользователя
   - Backend → Возврат токена
   - Frontend → Сохранение токена в localStorage

2. **Генерация медиафайлов (опционально):**
   - Frontend → POST `/api/media/generate-image/` или `/api/media/generate-audio/` (с токеном)
   - Backend → Вызов OpenAI API (DALL-E 3 для изображений, TTS-1-HD для аудио) или Google Gemini API (Nano Banana для изображений)
   - Провайдер выбирается из настроек пользователя или может быть указан в запросе
   - Backend → Сохранение медиафайла локально
   - Backend → Возврат URL к медиафайлу
   - Frontend → Предпросмотр медиафайла

3. **Генерация карточек:**
   - Frontend → POST `/api/cards/generate/` (с токеном, словами, переводами, медиафайлами)
   - Backend → Валидация данных
   - Backend → Сохранение слов в БД
   - Backend → Генерация .apkg через genanki (включая медиафайлы)
   - Backend → Возврат ссылки на скачивание
   - Frontend → GET `/api/cards/download/<file_id>/`
   - Frontend → Скачивание файла

### База данных

#### Схема

```
User
├── id (PK)
├── username
├── email
├── password (hashed)
├── preferred_language
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

Index: (user, original_word, language) - unique
```

### Формат файлов Anki (.apkg)

- **Один .apkg файл = одна колода карточек** (может содержать множество карточек)
- Файл .apkg представляет собой ZIP-архив, содержащий базу данных SQLite и медиафайлы.
- **Колода обязательно должна иметь название** при создании.
- Для создания .apkg файлов используется библиотека `genanki` (Python).

### Модели для генерации медиа

- **OpenAI:**
  - **Изображения:** DALL-E 3 (`dall-e-3`)
  - **Аудио:** TTS-1-HD (`tts-1-hd`)
- **Google Gemini:**
  - **Изображения:** Nano Banana Pro (`nano-banana-pro-preview`)
  - Размер: 1024x1024
  - Промпт формируется автоматически на основе слова и перевода
- **Аудио:** TTS-1-HD (`tts-1-hd`)
  - Формат: MP3
  - Голос выбирается в зависимости от языка (pt → португальский, de → немецкий)

---

## API Документация

### Базовый URL

```
http://localhost:8000/api/
```

### Аутентификация

Большинство endpoints требуют аутентификации через токен. Токен передается в заголовке:

```
Authorization: Token <your-token>
```

### Endpoints

#### Аутентификация

- **POST `/api/auth/register/`** - Регистрация нового пользователя.
- **POST `/api/auth/login/`** - Вход пользователя.

#### Профиль пользователя

- **GET `/api/user/profile/`** - Получение профиля текущего пользователя.
- **PATCH `/api/user/profile/`** - Обновление профиля пользователя.

#### Работа со словами

- **GET `/api/words/list/`** - Получение списка всех слов пользователя.

#### Генерация карточек

- **POST `/api/cards/generate/`** - Генерация .apkg файла с карточками.
  - Параметр `image_style`: `minimalistic` (минималистичный), `balanced` (сбалансированный, по умолчанию), `creative` (творческий).
- **GET `/api/cards/download/<file_id>/`** - Скачивание сгенерированного .apkg файла.

#### Генерация медиафайлов

- **POST `/api/media/generate-image/`** - Генерация изображения для слова.
  - Поддерживает два провайдера: OpenAI DALL-E 3 (по умолчанию) и Google Gemini Nano Banana
  - Параметр `provider`: `'openai'` или `'gemini'` (опционально, если не указан - используется из профиля пользователя)
  - Параметр `image_style`: `'minimalistic'`, `'balanced'`, `'creative'`
- **POST `/api/media/generate-audio/`** - Генерация аудио для слова через OpenAI TTS-1-HD.

#### Загрузка собственных медиафайлов

- **POST `/api/media/upload-image/`** - Загрузка собственного изображения.
- **POST `/api/media/upload-audio/`** - Загрузка собственного аудио.

### Коды ошибок

- `400` - Bad Request (неверные данные)
- `401` - Unauthorized (требуется аутентификация)
- `403` - Forbidden (нет доступа)
- `404` - Not Found (ресурс не найден)
- `500` - Internal Server Error (ошибка сервера)
