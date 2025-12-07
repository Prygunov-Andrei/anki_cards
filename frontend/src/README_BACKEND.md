# 🚀 ANKI Generator - Backend Integration Guide

## 🔌 Backend Integration

### Backend: Django REST Framework
### Frontend: React + TypeScript + Axios
### Туннель: Ngrok (`https://spouse-safer-being-luke.trycloudflare.com`)

---

## ⚡ Важно для Django!

### Django требует trailing slash (`/`) в конце всех URL!

| Метод | Правильный путь | Что возвращает |
|-------|----------------|----------------|
| `GET` | `/api/health/` | `{"status": "ok", "message": "..."}` |
| `POST` | `/api/auth/login/` | `{"token": "...", "user": {...}}` |
| `POST` | `/api/auth/register/` | `{"token": "...", "user": {...}}` |
| `POST` | `/api/auth/logout/` | `{"message": "Logged out"}` |
| `GET` | `/api/decks/` | `[{...}, {...}]` |
| `GET` | `/api/decks/:id/` | `{"id": ..., "name": "..."}` |
| `POST` | `/api/generate/` | `{"taskId": "..."}` |

---

## 🔧 Настройка Backend (Django)

### 1. Установите CORS

```bash
pip install django-cors-headers
```

### 2. settings.py

```python
INSTALLED_APPS = [
    'corsheaders',  # Добавьте
    # ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ⚠️ Первым!
    'django.middleware.common.CommonMiddleware',
    # ...
]

# CORS настройки для разработки
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'ngrok-skip-browser-warning',  # Важно для ngrok!
]
```

### 3. urls.py - Эндпоинты

```python
from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('api/health/', views.health_check),
    
    # Auth
    path('api/auth/login/', views.login),
    path('api/auth/register/', views.register),
    path('api/auth/logout/', views.logout),
    
    # Decks
    path('api/decks/', views.decks_list),
    path('api/decks/<int:id>/', views.deck_detail),
    path('api/decks/<int:id>/download/', views.deck_download),
    path('api/decks/<int:id>/cards/', views.deck_cards),
    
    # Generate
    path('api/generate/', views.generate_deck),
    path('api/decks/status/<str:task_id>/', views.generation_status),
]
```

### 4. views.py - Примеры

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Health check
def health_check(request):
    return JsonResponse({'status': 'ok', 'message': 'Backend is running'})

# Login
@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        # Ваша логика проверки
        if username == 'admin' and password == 'admin123':
            return JsonResponse({
                'token': 'your-jwt-token-here',
                'user': {
                    'id': 1,
                    'username': username,
                    'email': 'admin@example.com'
                }
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Register
@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # Ваша логика регистрации
        return JsonResponse({
            'token': 'your-jwt-token-here',
            'user': {
                'id': 1,
                'username': data.get('username'),
                'email': data.get('email')
            }
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
```

---

## 🧪 Тестирование

### Вариант 1: Через фронтенд

1. Откройте страницу входа
2. Нажмите **"🔽 Расширенная диагностика"**
3. Нажмите **"▶️ Запустить тесты"**
4. Все тесты должны быть ✅ зелеными

### Вариант 2: Через curl

```bash
# Health check
curl https://spouse-safer-being-luke.trycloudflare.com/api/health/ \
  -H "ngrok-skip-browser-warning: true"

# Login
curl -X POST https://spouse-safer-being-luke.trycloudflare.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -H "ngrok-skip-browser-warning: true" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Вариант 3: Через браузер

Откройте: `https://spouse-safer-being-luke.trycloudflare.com/api/health/`

Должно вернуть JSON.

---

## 📁 Структура Frontend

```
/lib/config.ts          ← Все API пути здесь (легко изменить)
/lib/api.ts            ← Axios клиент с настройками
/services/
  authService.ts       ← Логин, регистрация, logout
  deckService.ts       ← Работа с колодами
/contexts/
  AuthContext.tsx      ← Контекст авторизации
/pages/
  LoginPage.tsx        ← Страница входа с диагностикой
  RegisterPage.tsx     ← Страница регистрации
  DecksPage.tsx        ← Список колод
```

---

## 🔑 Тестовые данные

**Username:** `admin`  
**Password:** `admin123`

---

## ⚠️ Частые ошибки

### ❌ 404 Not Found
**Причина:** URL без trailing slash  
**Решение:** Добавьте `/` в конец: `/api/auth/login/`

### ❌ CORS Error
**Причина:** CORS не настроен на backend  
**Решение:** Добавьте `django-cors-headers` (см. выше)

### ❌ 401 Unauthorized
**Причина:** Неверные credentials или токен  
**Решение:** Проверьте username/password или JWT токен

### ❌ Network Error
**Причина:** Backend не запущен или ngrok не активен  
**Решение:** Проверьте что Django и ngrok работают

---

## 📚 Документация

- **BACKEND_FIX.md** - Настройка CORS для разных backend
- **DJANGO_TRAILING_SLASH.md** - Почему Django требует trailing slash
- **QUICK_FIX_404.md** - Быстрое исправление 404
- **CHANGELOG.md** - История всех изменений

---

## 🎯 Checklist для Backend разработчика

- [ ] Django запущен
- [ ] Ngrok туннель активен
- [ ] `django-cors-headers` установлен и настроен
- [ ] Все URL в `urls.py` со слешем (`/`)
- [ ] Эндпоинт `/api/health/` существует
- [ ] Эндпоинт `/api/auth/login/` возвращает `{token, user}`
- [ ] Тестовый пользователь `admin:admin123` создан
- [ ] CORS разрешает все домены (для разработки)
- [ ] Заголовок `ngrok-skip-browser-warning` разрешен

---

## 💡 Если что-то не работает

1. Проверьте логи Django в консоли
2. Запустите диагностику на фронтенде
3. Проверьте что ngrok URL актуален
4. Убедитесь что все URL со слешем
5. Посмотрите в консоль браузера (F12)

---

## 🎉 Всё настроено!

Фронтенд готов к работе с Django backend через ngrok!

**Дата:** 1 декабря 2025  
**Версия:** 1.0  
**Статус:** ✅ Production Ready