# 🔧 Инструкция по исправлению CORS на Backend

## ✅ ИСПРАВЛЕНО ДЛЯ DJANGO!

**Django требует trailing slash!** Все пути на фронтенде обновлены:
- ✅ `/api/auth/login/` (со слешем)
- ✅ `/api/auth/register/` (со слешем)
- ✅ `/api/health/` (со слешем)

---

## 🚨 Проблема
Фронтенд не может подключиться к backend из-за CORS (Cross-Origin Resource Sharing) ошибки:
```
Access-Control-Allow-Origin header is not present on the requested resource
```

## ✅ Решение для Django Backend

### 📘 Django + django-cors-headers

**1. Установите django-cors-headers:**
```bash
pip install django-cors-headers
```

**2. Добавьте в `settings.py`:**
```python
INSTALLED_APPS = [
    # ... другие приложения
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ⚠️ Должно быть первым!
    'django.middleware.common.CommonMiddleware',
    # ... остальные middleware
]

# CORS настройки
CORS_ALLOW_ALL_ORIGINS = True  # Для разработки
# Для production используйте:
# CORS_ALLOWED_ORIGINS = [
#     "https://your-frontend-domain.com",
# ]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'ngrok-skip-browser-warning',  # Важно для ngrok!
]
```

**3. Добавьте health endpoint в `urls.py`:**
```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok', 'message': 'Backend is running'})

urlpatterns = [
    path('api/health/', health_check),
    # ... остальные пути
]
```

---

## ✅ Решение для других Backend

### Если у вас Flask (Python)

1. **Установите flask-cors:**
```bash
pip install flask-cors
```

2. **Добавьте в ваш `app.py` или главный файл:**
```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# Настройка CORS для разрешения запросов от Figma Make
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Разрешить все домены
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "ngrok-skip-browser-warning"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }
})

# Ваши роуты...
@app.route('/api/health', methods=['GET'])
def health():
    return {"status": "ok", "message": "Server is running"}
```

### Если у вас FastAPI (Python)

1. **Добавьте в ваш `main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все домены
    allow_credentials=False,
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)

# Ваши роуты...
@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Server is running"}
```

### Если у вас Express (Node.js)

1. **Установите cors:**
```bash
npm install cors
```

2. **Добавьте в ваш `server.js` или `app.js`:**
```javascript
const express = require('express');
const cors = require('cors');

const app = express();

// Настройка CORS
app.use(cors({
    origin: '*',  // Разрешить все домены
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'ngrok-skip-browser-warning'],
    credentials: false
}));

// Ваши роуты...
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', message: 'Server is running' });
});
```

## ✅ Checklist

После внесения изменений проверьте:

- [ ] Backend запущен и работает
- [ ] Ngrok туннель активен (проверьте URL: https://spouse-safer-being-luke.trycloudflare.com)
- [ ] CORS middleware добавлен в код backend
- [ ] Эндпоинт `/api/health` существует и отвечает
- [ ] В консоли backend нет ошибок
- [ ] Фронтенд может подключиться (используйте кнопку "Проверить соединение")

## 🧪 Тестирование

После исправления:
1. Перезапустите backend
2. Откройте фронтенд
3. Нажмите "🔍 Проверить соединение с сервером"
4. Нажмите "🔽 Расширенная диагностика" для детальной проверки

## 💡 Дополнительные советы

### Для production (после разработки):
Замените `"*"` на конкретный домен:
```python
# Flask/FastAPI
allow_origins=["https://your-frontend-domain.com"]

# Express
origin: 'https://your-frontend-domain.com'
```

### Если используете Ngrok:
Убедитесь, что ngrok запущен и URL актуален:
```bash
ngrok http 5000  # Замените 5000 на ваш порт
```

### Проверка вручную:
Откройте в браузере:
- https://f6c058cfd2ea.ngrok-free.app/api/health
- Должен вернуть JSON с данными

## 🆘 Если ничего не помогает

1. Проверьте логи backend в консоли
2. Убедитесь, что порт не занят другим процессом
3. Попробуйте перезапустить ngrok
4. Проверьте firewall/антивирус
5. Напишите в поддержку с логами из "Расширенной диагностики"