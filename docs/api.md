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

## Коды ошибок

- `400` - Bad Request (неверные данные)
- `401` - Unauthorized (требуется аутентификация)
- `403` - Forbidden (нет доступа)
- `404` - Not Found (ресурс не найден)
- `500` - Internal Server Error (ошибка сервера)

