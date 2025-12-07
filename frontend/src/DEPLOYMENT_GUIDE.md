# 🚀 Гайд по деплою фронтенда на Django бэкенд

## 📋 Оглавление
1. [Подготовка фронтенда](#1-подготовка-фронтенда)
2. [Билд проекта](#2-билд-проекта)
3. [Настройка Django](#3-настройка-django)
4. [Копирование файлов](#4-копирование-файлов)
5. [Проверка деплоя](#5-проверка-деплоя)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Подготовка фронтенда

### 1.1 Проверьте конфигурацию

Убедитесь, что файл `/lib/config.ts` использует переменную окружения:

```typescript
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://get-anki.fan.ngrok.app';
```

### 1.2 Создайте `.env.production`

Файл уже создан в корне проекта:

```bash
VITE_API_BASE_URL=/api
```

Это означает, что в продакшене API запросы пойдут на тот же домен: `/api/...`

---

## 2. Билд проекта

### 2.1 Установите зависимости (если нужно)

```bash
npm install
```

### 2.2 Соберите production билд

```bash
npm run build
```

Эта команда создаст папку `dist/` с оптимизированными файлами:

```
dist/
├── index.html          # Главная HTML страница
├── assets/             # JS, CSS, шрифты
│   ├── index-[hash].js
│   ├── index-[hash].css
│   └── ...
└── ...
```

**Размер:** обычно 500KB - 2MB (сжатый)

---

## 3. Настройка Django

### 3.1 Структура Django проекта

Создайте следующую структуру в вашем Django проекте:

```
your-django-project/
├── manage.py
├── your_app/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── static/              # Для статических файлов (JS/CSS)
├── staticfiles/         # Для собранных статических файлов (после collectstatic)
└── templates/           # Для HTML шаблонов
    └── index.html       # React приложение
```

### 3.2 Обновите `settings.py`

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Статические файлы (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Шаблоны
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # ← ВАЖНО!
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# CORS настройки (если фронтенд и бэкенд на одном домене, не нужно)
# Если используете отдельные домены, оставьте CORS middleware

# Медиа файлы (загруженные пользователями)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 3.3 Обновите `urls.py` (главный)

```python
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('your_api_app.urls')),  # Ваши API endpoints
    
    # React приложение (catch-all route)
    # ВАЖНО: Это должно быть в самом конце!
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='frontend'),
]

# Статические и медиа файлы в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

**⚠️ ВАЖНО:** Catch-all route (`re_path(r'^.*$', ...)`) должен быть **ПОСЛЕДНИМ**!  
Это позволит Django обработать все API запросы перед тем, как вернуть React приложение.

---

## 4. Копирование файлов

### 4.1 Скопируйте файлы из `dist/`

После успешного билда (`npm run build`):

#### A. Скопируйте `index.html` → Django templates

```bash
# Из корня фронтенд проекта
cp dist/index.html /path/to/django/templates/index.html
```

#### B. Скопируйте `assets/` → Django static

```bash
# Создайте папку для фронтенда в static
mkdir -p /path/to/django/static/assets

# Скопируйте все файлы из dist/assets/
cp -r dist/assets/* /path/to/django/static/assets/
```

### 4.2 Обновите пути в `index.html`

Откройте `/path/to/django/templates/index.html` и обновите пути к статическим файлам:

**Было:**
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Anki Generator</title>
    <script type="module" crossorigin src="/assets/index-abc123.js"></script>
    <link rel="stylesheet" crossorigin href="/assets/index-xyz789.css">
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
```

**Стало (с Django template tags):**
```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="{% static 'vite.svg' %}" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Anki Generator</title>
    <script type="module" crossorigin src="{% static 'assets/index-abc123.js' %}"></script>
    <link rel="stylesheet" crossorigin href="{% static 'assets/index-xyz789.css' %}">
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
```

**Или автоматически через скрипт:**

```bash
# Замените /assets/ на {% static 'assets/' %} и т.д.
sed -i 's|/assets/|{% static "assets/|g' /path/to/django/templates/index.html
sed -i 's|\.js"|.js" %}|g' /path/to/django/templates/index.html
sed -i 's|\.css"|.css" %}|g' /path/to/django/templates/index.html
```

### 4.3 Соберите статические файлы

```bash
cd /path/to/django
python manage.py collectstatic --noinput
```

Это скопирует все файлы из `static/` в `staticfiles/` для продакшена.

---

## 5. Проверка деплоя

### 5.1 Запустите Django сервер

```bash
python manage.py runserver
```

### 5.2 Откройте браузер

Перейдите на `http://localhost:8000/`

**Проверьте:**
- ✅ React приложение загружается
- ✅ API запросы работают (`/api/...`)
- ✅ Медиа файлы отображаются
- ✅ Роутинг работает (переходы между страницами)

### 5.3 Проверьте консоль браузера

Не должно быть ошибок типа:
- ❌ `404 Not Found` для JS/CSS файлов
- ❌ `CORS errors`
- ❌ `Failed to fetch` для API

---

## 6. Troubleshooting

### Проблема 1: 404 на статические файлы

**Симптомы:**
```
GET http://localhost:8000/assets/index-abc123.js 404 (Not Found)
```

**Решение:**
1. Проверьте, что файлы скопированы в `static/assets/`
2. Запустите `python manage.py collectstatic`
3. Проверьте `STATICFILES_DIRS` в `settings.py`
4. Проверьте пути в `index.html` (должны быть `{% static '...' %}`)

---

### Проблема 2: Роутинг не работает (404 на /decks, /profile и т.д.)

**Симптомы:**
При переходе на `/decks` получаете 404 от Django

**Решение:**
Убедитесь, что catch-all route **ПОСЛЕДНИЙ** в `urls.py`:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('your_api.urls')),  # API ПЕРВЫМ!
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),  # Catch-all ПОСЛЕДНИМ!
]
```

---

### Проблема 3: CORS ошибки

**Симптомы:**
```
Access to fetch at 'http://localhost:8000/api/...' has been blocked by CORS policy
```

**Решение:**
Если фронтенд и бэкенд на **одном домене** (после деплоя), CORS не нужен!

Удалите или отключите `django-cors-headers` в продакшене:

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['corsheaders']
    MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')
    CORS_ALLOW_ALL_ORIGINS = True
```

---

### Проблема 4: Медиа файлы не загружаются

**Симптомы:**
Изображения и аудио возвращают 404

**Решение:**
1. Проверьте `MEDIA_URL` и `MEDIA_ROOT` в `settings.py`
2. Добавьте в `urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

3. В продакшене используйте Nginx/Apache для раздачи медиа

---

### Проблема 5: Приложение работает, но API запросы идут на старый URL

**Симптомы:**
Запросы идут на `https://get-anki.fan.ngrok.app/api/...` вместо `/api/...`

**Решение:**
1. Проверьте файл `.env.production`:
   ```bash
   VITE_API_BASE_URL=/api
   ```
2. Пересоберите билд:
   ```bash
   npm run build
   ```
3. Заново скопируйте файлы в Django

---

## 7. Автоматизация деплоя

### Создайте скрипт `deploy.sh`

Сохраните в корне фронтенд проекта:

```bash
#!/bin/bash

# Путь к Django проекту (ИЗМЕНИТЕ!)
DJANGO_PATH="/path/to/your/django/project"

echo "🚀 Starting deployment..."

# 1. Билд фронтенда
echo "📦 Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# 2. Копирование index.html
echo "📄 Copying index.html..."
cp dist/index.html "$DJANGO_PATH/templates/index.html"

# 3. Копирование assets
echo "📁 Copying assets..."
rm -rf "$DJANGO_PATH/static/assets"
cp -r dist/assets "$DJANGO_PATH/static/"

# 4. Обновление путей в index.html (опционально)
echo "🔧 Updating static paths..."
# Используйте sed или Python скрипт для замены путей

# 5. Collectstatic
echo "📚 Running collectstatic..."
cd "$DJANGO_PATH"
python manage.py collectstatic --noinput

echo "✅ Deployment complete!"
echo "🌐 Visit: http://localhost:8000/"
```

Сделайте скрипт исполняемым:

```bash
chmod +x deploy.sh
```

Запуск:

```bash
./deploy.sh
```

---

## 8. Production настройки

### 8.1 Nginx конфигурация (рекомендуется для продакшена)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Статические файлы
    location /static/ {
        alias /path/to/django/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Медиа файлы
    location /media/ {
        alias /path/to/django/media/;
        expires 7d;
    }

    # API запросы к Django
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Admin панель
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # React приложение (все остальное)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 8.2 Gunicorn для продакшена

```bash
# Установка
pip install gunicorn

# Запуск
gunicorn your_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
```

---

## 9. Быстрый чеклист

- [ ] Обновлен `/lib/config.ts` для использования переменной окружения
- [ ] Создан `.env.production` с `VITE_API_BASE_URL=/api`
- [ ] Выполнен `npm run build`
- [ ] Скопирован `dist/index.html` → `django/templates/index.html`
- [ ] Скопированы `dist/assets/*` → `django/static/assets/`
- [ ] Обновлены пути в `index.html` (добавлены `{% static %}`)
- [ ] Настроен `settings.py` (STATIC_URL, TEMPLATES, MEDIA)
- [ ] Настроен `urls.py` (catch-all route в конце)
- [ ] Выполнен `python manage.py collectstatic`
- [ ] Проверена работа на `http://localhost:8000/`
- [ ] Проверены API запросы, роутинг, медиа

---

## 10. Контакты и поддержка

Если что-то не работает:

1. Проверьте консоль браузера (F12)
2. Проверьте логи Django
3. Проверьте Network tab в DevTools
4. Убедитесь, что все пути корректны

**Успешного деплоя! 🚀**
