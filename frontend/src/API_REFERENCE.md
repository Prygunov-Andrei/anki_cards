# 🔌 API Reference - ANKI Generator

## Base URL
```
https://spouse-safer-being-luke.trycloudflare.com
```

## Required Headers
```
Content-Type: application/json
ngrok-skip-browser-warning: true
Authorization: Bearer <token>  (для защищенных эндпоинтов)
```

---

## 🏥 Health Check

### `GET /api/health/`
Проверка работоспособности сервера

**Request:**
```bash
GET /api/health/
```

**Response: 200 OK**
```json
{
  "status": "ok",
  "message": "Backend is running"
}
```

---

## 🔐 Authentication

### `POST /api/auth/login/`
Вход в систему

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response: 200 OK**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  }
}
```

**Response: 401 Unauthorized**
```json
{
  "error": "Invalid credentials"
}
```

---

### `POST /api/auth/register/`
Регистрация нового пользователя

**Request:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword123"
}
```

**Response: 201 Created**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "username": "newuser",
    "email": "newuser@example.com"
  }
}
```

**Response: 400 Bad Request**
```json
{
  "error": "Username already exists"
}
```

---

### `POST /api/auth/logout/`
Выход из системы

**Headers:**
```
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "message": "Successfully logged out"
}
```

---

## 🎴 Decks

### `GET /api/decks/`
Получить список всех колод пользователя

**Headers:**
```
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "name": "Spanish Vocabulary",
    "sourceLanguage": "en",
    "targetLanguage": "es",
    "cardCount": 50,
    "createdAt": "2025-12-01T10:30:00Z",
    "status": "completed"
  },
  {
    "id": 2,
    "name": "French Basics",
    "sourceLanguage": "en",
    "targetLanguage": "fr",
    "cardCount": 30,
    "createdAt": "2025-12-01T11:00:00Z",
    "status": "completed"
  }
]
```

---

### `GET /api/decks/:id/`
Получить информацию о конкретной колоде

**Headers:**
```
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "Spanish Vocabulary",
  "sourceLanguage": "en",
  "targetLanguage": "es",
  "cardCount": 50,
  "createdAt": "2025-12-01T10:30:00Z",
  "status": "completed",
  "imageStyle": "realistic",
  "voiceGender": "female"
}
```

**Response: 404 Not Found**
```json
{
  "error": "Deck not found"
}
```

---

### `DELETE /api/decks/:id/`
Удалить колоду

**Headers:**
```
Authorization: Bearer <token>
```

**Response: 204 No Content**
(Пустое тело ответа)

**Response: 404 Not Found**
```json
{
  "error": "Deck not found"
}
```

---

### `GET /api/decks/:id/cards/`
Получить карточки колоды

**Headers:**
```
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "word": "hello",
    "translation": "hola",
    "imageUrl": "https://example.com/images/hello.jpg",
    "audioUrl": "https://example.com/audio/hello.mp3",
    "example": "Hello, how are you?",
    "exampleTranslation": "Hola, ¿cómo estás?"
  },
  {
    "id": 2,
    "word": "goodbye",
    "translation": "adiós",
    "imageUrl": "https://example.com/images/goodbye.jpg",
    "audioUrl": "https://example.com/audio/goodbye.mp3",
    "example": "Goodbye, see you later!",
    "exampleTranslation": "Adiós, ¡hasta luego!"
  }
]
```

---

### `GET /api/decks/:id/download/`
Скачать ZIP архив колоды

**Headers:**
```
Authorization: Bearer <token>
```

**Response: 200 OK**
```
Content-Type: application/zip
Content-Disposition: attachment; filename="spanish_vocabulary.zip"

<binary data>
```

---

## 🎨 Generation

### `POST /api/generate/`
Запустить генерацию новой колоды

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "words": ["hello", "goodbye", "thank you", "please", "yes", "no"],
  "sourceLanguage": "en",
  "targetLanguage": "es",
  "imageStyle": "realistic",
  "voiceGender": "female"
}
```

**Response: 202 Accepted**
```json
{
  "taskId": "task-123e4567-e89b-12d3-a456-426614174000",
  "message": "Generation started"
}
```

---

### `GET /api/decks/status/:taskId/`
Проверить статус генерации

**Headers:**
```
Authorization: Bearer <token>
```

**Response: 200 OK (В процессе)**
```json
{
  "status": "processing",
  "progress": 45,
  "message": "Generating images..."
}
```

**Response: 200 OK (Завершено)**
```json
{
  "status": "completed",
  "progress": 100,
  "deckId": 5,
  "message": "Generation completed successfully"
}
```

**Response: 200 OK (Ошибка)**
```json
{
  "status": "failed",
  "error": "Failed to generate images for some words",
  "message": "Generation failed"
}
```

---

## 📊 Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Запрос выполнен успешно |
| 201 | Created | Ресурс создан |
| 202 | Accepted | Запрос принят в обработку |
| 204 | No Content | Запрос выполнен, нет содержимого |
| 400 | Bad Request | Неверный формат запроса |
| 401 | Unauthorized | Требуется авторизация |
| 403 | Forbidden | Доступ запрещен |
| 404 | Not Found | Ресурс не найден |
| 500 | Internal Server Error | Ошибка сервера |

---

## 🔒 Authorization

Для защищенных эндпоинтов используйте JWT токен:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Токен получается при успешном логине/регистрации.

---

## 🧪 Testing с curl

### Health Check
```bash
curl https://f6c058cfd2ea.ngrok-free.app/api/health/ \
  -H "ngrok-skip-browser-warning: true"
```

### Login
```bash
curl -X POST https://f6c058cfd2ea.ngrok-free.app/api/auth/login/ \
  -H "Content-Type: application/json" \
  -H "ngrok-skip-browser-warning: true" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Get Decks
```bash
curl https://f6c058cfd2ea.ngrok-free.app/api/decks/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "ngrok-skip-browser-warning: true"
```

---

## 💡 Frontend Usage

```typescript
import apiClient from './lib/api';
import { API_ENDPOINTS } from './lib/config';

// Login
const response = await apiClient.post(API_ENDPOINTS.LOGIN, {
  username: 'admin',
  password: 'admin123'
});

// Get decks (with auth)
const decks = await apiClient.get(API_ENDPOINTS.DECKS);

// Generate deck
const task = await apiClient.post(API_ENDPOINTS.GENERATE, {
  words: ['hello', 'goodbye'],
  sourceLanguage: 'en',
  targetLanguage: 'es'
});
```

---

**Last Updated:** December 1, 2025  
**Version:** 1.0  
**Backend:** Django REST Framework  
**Frontend:** React + TypeScript + Axios