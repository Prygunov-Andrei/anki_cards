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
  "deck_name": "Португальские слова - 2024",
  "image_style": "balanced"
}
```

**Параметры:**
- `image_style` (optional): Режим генерации изображений. Возможные значения:
  - `minimalistic` - Минималистичный режим
  - `balanced` - Сбалансированный режим (по умолчанию)
  - `creative` - Творческий режим

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

### Режимы генерации изображений

Система поддерживает три режима генерации изображений, которые применяются для всей колоды:

1. **Минималистичный** (`minimalistic`): Простое, чистое, минималистичное изображение
2. **Сбалансированный** (`balanced`): Выразительная иллюстрация с умеренными деталями (по умолчанию)
3. **Творческий** (`creative`): Яркая, сочная иллюстрация с разнообразной палитрой

Режим выбирается через интерфейс и передается в параметре `image_style` при генерации колоды.

## Коды ошибок

- `400` - Bad Request (неверные данные)
- `401` - Unauthorized (требуется аутентификация)
- `403` - Forbidden (нет доступа)
- `404` - Not Found (ресурс не найден)
- `500` - Internal Server Error (ошибка сервера)

