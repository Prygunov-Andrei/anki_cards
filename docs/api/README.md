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

Токен получается при регистрации или входе.

## Endpoints

### Аутентификация

#### POST `/api/auth/register/`
Регистрация нового пользователя.

**Тело запроса:**
```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepassword",
  "preferred_language": "ru"
}
```

**Ответ:**
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com"
  }
}
```

#### POST `/api/auth/login/`
Вход пользователя.

**Тело запроса:**
```json
{
  "username": "user123",
  "password": "securepassword"
}
```

**Ответ:**
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "username": "user123"
  }
}
```

### Профиль пользователя

#### GET `/api/user/profile/`
Получение профиля текущего пользователя.

**Требует аутентификации:** Да

**Ответ:**
```json
{
  "id": 1,
  "username": "user123",
  "email": "user@example.com",
  "preferred_language": "ru",
  "native_language": "ru",
  "learning_language": "de",
  "theme": "light",
  "mode": "advanced"
}
```

#### PATCH `/api/user/profile/`
Обновление профиля пользователя.

**Требует аутентификации:** Да

**Тело запроса:**
```json
{
  "preferred_language": "en",
  "native_language": "ru",
  "learning_language": "de",
  "theme": "dark"
}
```

### Работа со словами

#### GET `/api/words/list/`
Получение списка всех слов пользователя.

**Требует аутентификации:** Да

**Ответ:**
```json
{
  "words": [
    {
      "id": 1,
      "original_word": "Haus",
      "translation": "Дом",
      "language": "de",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### Генерация карточек

#### POST `/api/cards/generate/`
Генерация .apkg файла с карточками.

**Требует аутентификации:** Да

**Тело запроса:**
```json
{
  "words": ["Haus", "Auto", "Buch"],
  "language": "de",
  "translations": {
    "Haus": "Дом",
    "Auto": "Машина",
    "Buch": "Книга"
  },
  "deck_name": "Немецкие слова",
  "image_style": "balanced",
  "audio_files": {},
  "image_files": {},
  "save_to_decks": true
}
```

**Параметры:**
- `image_style`: `minimalistic` | `balanced` | `creative` (по умолчанию: `balanced`)
- `save_to_decks`: `true` | `false` - сохранить ли колоду в "Мои колоды"

**Ответ:**
```json
{
  "file_id": "uuid-here",
  "download_url": "/api/cards/download/uuid-here/",
  "deck_name": "Немецкие слова",
  "cards_count": 6,
  "deck_id": 1,
  "deck_url": "/decks/1"
}
```

#### GET `/api/cards/download/<file_id>/`
Скачивание сгенерированного .apkg файла.

**Требует аутентификации:** Да

**Ответ:** Файл .apkg

### Генерация медиафайлов

#### POST `/api/media/generate-image/`
Генерация изображения для слова.

**Требует аутентификации:** Да

**Тело запроса:**
```json
{
  "word": "Haus",
  "translation": "Дом",
  "language": "de",
  "image_style": "balanced",
  "provider": "openai"
}
```

**Параметры:**
- `provider`: `openai` | `gemini` (опционально, используется из профиля)
- `image_style`: `minimalistic` | `balanced` | `creative`

**Ответ:**
```json
{
  "image_url": "/media/images/abc123.jpg",
  "image_id": "uuid-here",
  "file_path": "/path/to/image.jpg"
}
```

#### POST `/api/media/generate-audio/`
Генерация аудио для слова.

**Требует аутентификации:** Да

**Тело запроса:**
```json
{
  "word": "Haus",
  "language": "de",
  "provider": "openai"
}
```

**Ответ:**
```json
{
  "audio_url": "/media/audio/abc123.mp3",
  "audio_id": "uuid-here",
  "file_path": "/path/to/audio.mp3"
}
```

### Загрузка медиафайлов

#### POST `/api/media/upload-image/`
Загрузка собственного изображения.

**Требует аутентификации:** Да

**Формат:** `multipart/form-data`

**Поля:**
- `image`: файл изображения

**Ответ:**
```json
{
  "image_url": "/media/images/abc123.jpg",
  "image_id": "uuid-here",
  "file_path": "/path/to/image.jpg"
}
```

#### POST `/api/media/upload-audio/`
Загрузка собственного аудио.

**Требует аутентификации:** Да

**Формат:** `multipart/form-data`

**Поля:**
- `audio`: файл аудио

**Ответ:**
```json
{
  "audio_url": "/media/audio/abc123.mp3",
  "audio_id": "uuid-here",
  "file_path": "/path/to/audio.mp3"
}
```

### Управление колодами

#### GET `/api/cards/decks/`
Получение списка колод пользователя.

**Требует аутентификации:** Да

#### POST `/api/cards/decks/`
Создание новой колоды.

**Требует аутентификации:** Да

#### GET `/api/cards/decks/<deck_id>/`
Получение детальной информации о колоде.

**Требует аутентификации:** Да

#### PATCH `/api/cards/decks/<deck_id>/`
Обновление колоды.

**Требует аутентификации:** Да

#### DELETE `/api/cards/decks/<deck_id>/`
Удаление колоды.

**Требует аутентификации:** Да

#### POST `/api/cards/decks/<deck_id>/generate-apkg/`
Генерация .apkg файла из колоды.

**Требует аутентификации:** Да

### Синхронизация Anki

#### POST `/sync/`
Основной endpoint для синхронизации Anki.

**Аутентификация:** HTTP Basic Auth

**Используется клиентами Anki для синхронизации.**

## Коды ошибок

- `400` - Bad Request (неверные данные)
- `401` - Unauthorized (требуется аутентификация)
- `402` - Payment Required (недостаточно токенов)
- `403` - Forbidden (нет доступа)
- `404` - Not Found (ресурс не найден)
- `500` - Internal Server Error (ошибка сервера)

## Примеры использования

### Python (requests)

```python
import requests

# Регистрация
response = requests.post('http://localhost:8000/api/auth/register/', json={
    'username': 'user123',
    'email': 'user@example.com',
    'password': 'password123'
})
token = response.json()['token']

# Генерация карточек
headers = {'Authorization': f'Token {token}'}
response = requests.post('http://localhost:8000/api/cards/generate/', 
    json={
        'words': ['Haus', 'Auto'],
        'language': 'de',
        'translations': {'Haus': 'Дом', 'Auto': 'Машина'},
        'deck_name': 'Немецкие слова'
    },
    headers=headers
)
```

### JavaScript (fetch)

```javascript
// Регистрация
const response = await fetch('http://localhost:8000/api/auth/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user123',
    email: 'user@example.com',
    password: 'password123'
  })
});
const { token } = await response.json();

// Генерация карточек
const cardsResponse = await fetch('http://localhost:8000/api/cards/generate/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${token}`
  },
  body: JSON.stringify({
    words: ['Haus', 'Auto'],
    language: 'de',
    translations: { Haus: 'Дом', Auto: 'Машина' },
    deck_name: 'Немецкие слова'
  })
});
```

