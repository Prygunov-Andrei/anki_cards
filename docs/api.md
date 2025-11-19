# API Документация

## Базовый URL

```
http://localhost:8000/api/
```

## Аутентификация

Большинство endpoints требуют аутентификации через токен. Токен передается в заголовке:

```
Authorization: Token <your-token>
```

## Endpoints

### Аутентификация

#### POST `/api/auth/register/`

Регистрация нового пользователя.

**Request Body:**
```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepassword",
  "preferred_language": "pt"
}
```

**Response:**
```json
{
  "user_id": 1,
  "token": "abc123...",
  "username": "user123",
  "email": "user@example.com",
  "preferred_language": "pt"
}
```

#### POST `/api/auth/login/`

Вход пользователя.

**Request Body:**
```json
{
  "username": "user123",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "token": "abc123...",
  "user_id": 1
}
```

### Профиль пользователя

#### GET `/api/user/profile/`

Получение профиля текущего пользователя (требует аутентификации).

**Response:**
```json
{
  "username": "user123",
  "email": "user@example.com",
  "preferred_language": "pt"
}
```

#### PATCH `/api/user/profile/`

Обновление профиля пользователя (требует аутентификации).

**Request Body:**
```json
{
  "preferred_language": "de"
}
```

**Response:**
```json
{
  "username": "user123",
  "email": "user@example.com",
  "preferred_language": "de"
}
```

### Работа со словами

#### GET `/api/words/list/`

Получение списка всех слов пользователя (требует аутентификации).

**Query Parameters:**
- `language` (optional): `pt` или `de` - фильтрация по языку
- `search` (optional): строка для поиска по словам и переводам

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "original_word": "casa",
      "translation": "дом",
      "language": "pt",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### Генерация карточек

#### POST `/api/cards/generate/`

Генерация .apkg файла с карточками (требует аутентификации).

**Request Body:**
```json
{
  "words": "casa, palavra, livro",
  "language": "pt",
  "translations": {
    "casa": "дом",
    "palavra": "слово",
    "livro": "книга"
  },
  "audio_files": {
    "casa": "/path/to/casa.mp3"
  },
  "image_files": {
    "casa": "/path/to/casa.jpg"
  },
  "deck_name": "Португальские слова - 2024"
}
```

**Response:**
```json
{
  "file_id": "uuid-string",
  "download_url": "/api/cards/download/uuid-string/",
  "deck_name": "Португальские слова - 2024",
  "cards_count": 6
}
```

#### GET `/api/cards/download/<file_id>/`

Скачивание сгенерированного .apkg файла.

**Response:** Бинарный файл .apkg

### Генерация медиафайлов через OpenAI

#### POST `/api/media/generate-image/`

Генерация изображения для слова через OpenAI DALL-E 3 (требует аутентификации).

**Request Body:**
```json
{
  "word": "casa",
  "translation": "дом",
  "language": "pt"
}
```

**Response:**
```json
{
  "image_url": "/media/images/uuid.jpg",
  "image_id": "uuid"
}
```

#### POST `/api/media/generate-audio/`

Генерация аудио для слова через OpenAI TTS-1-HD (требует аутентификации).

**Request Body:**
```json
{
  "word": "casa",
  "language": "pt"
}
```

**Response:**
```json
{
  "audio_url": "/media/audio/uuid.mp3",
  "audio_id": "uuid"
}
```

### Загрузка собственных медиафайлов

#### POST `/api/media/upload-image/`

Загрузка собственного изображения (требует аутентификации).

**Request:** `multipart/form-data` с полем `image` (файл)

**Response:**
```json
{
  "image_url": "/media/images/uuid.jpg",
  "image_id": "uuid"
}
```

#### POST `/api/media/upload-audio/`

Загрузка собственного аудио (требует аутентификации).

**Request:** `multipart/form-data` с полем `audio` (файл)

**Response:**
```json
{
  "audio_url": "/media/audio/uuid.mp3",
  "audio_id": "uuid"
}
```

### Управление промптами

#### GET `/api/user/prompts/`

Получение всех промптов пользователя (требует аутентификации).

**Response:**
```json
[
  {
    "id": 1,
    "prompt_type": "image",
    "prompt_type_display": "Генерация изображений",
    "custom_prompt": "Простое, четкое изображение слова '{word}'...",
    "is_custom": false,
    "created_at": "2024-12-17T12:00:00Z",
    "updated_at": "2024-12-17T12:00:00Z"
  }
]
```

#### GET `/api/user/prompts/{prompt_type}/`

Получение конкретного промпта пользователя (требует аутентификации).

**Path Parameters:**
- `prompt_type`: Тип промпта (`image`, `audio`, `word_analysis`, `translation`, `deck_name`, `part_of_speech`, `category`)

**Response:**
```json
{
  "id": 1,
  "prompt_type": "image",
  "prompt_type_display": "Генерация изображений",
  "custom_prompt": "Простое, четкое изображение слова '{word}'...",
  "is_custom": false,
  "created_at": "2024-12-17T12:00:00Z",
  "updated_at": "2024-12-17T12:00:00Z"
}
```

#### PATCH `/api/user/prompts/{prompt_type}/update/`

Обновление промпта пользователя (требует аутентификации).

**Path Parameters:**
- `prompt_type`: Тип промпта

**Request Body:**
```json
{
  "custom_prompt": "Новый промпт с плейсхолдерами {word} и {translation}"
}
```

**Response:**
```json
{
  "id": 1,
  "prompt_type": "image",
  "prompt_type_display": "Генерация изображений",
  "custom_prompt": "Новый промпт с плейсхолдерами {word} и {translation}",
  "is_custom": true,
  "created_at": "2024-12-17T12:00:00Z",
  "updated_at": "2024-12-17T12:30:00Z"
}
```

**Ошибки:**
- `400` - Промпт не содержит обязательные плейсхолдеры для данного типа

#### POST `/api/user/prompts/{prompt_type}/reset/`

Сброс промпта до заводских настроек (требует аутентификации).

**Path Parameters:**
- `prompt_type`: Тип промпта

**Response:**
```json
{
  "id": 1,
  "prompt_type": "image",
  "prompt_type_display": "Генерация изображений",
  "custom_prompt": "Заводской промпт...",
  "is_custom": false,
  "created_at": "2024-12-17T12:00:00Z",
  "updated_at": "2024-12-17T12:35:00Z"
}
```

**Доступные типы промптов:**
- `image` - Генерация изображений (DALL-E)
- `audio` - Генерация аудио (TTS)
- `word_analysis` - Анализ смешанных языков
- `translation` - Перевод слов
- `deck_name` - Генерация названия колоды
- `part_of_speech` - Определение части речи
- `category` - Определение категории

**Плейсхолдеры:**
- `{word}` - Исходное слово
- `{translation}` - Перевод слова
- `{language}` - Язык слова
- `{native_language}` - Родной язык пользователя
- `{learning_language}` - Язык изучения
- `{english_translation}` - Английский перевод

## Коды ошибок

- `400` - Bad Request (неверные данные)
- `401` - Unauthorized (требуется аутентификация)
- `403` - Forbidden (нет доступа)
- `404` - Not Found (ресурс не найден)
- `500` - Internal Server Error (ошибка сервера)

