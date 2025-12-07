# ⚡ Быстрый деплой - Пошаговая инструкция

## 🎯 Простая инструкция для деплоя фронтенда на Django

### Шаг 1: Соберите фронтенд

```bash
# В корне фронтенд проекта
npm run build
```

Это создаст папку `dist/` с файлами.

---

### Шаг 2: Скопируйте файлы в Django

#### 2.1 Скопируйте HTML шаблон

```bash
# Замените /path/to/django на ваш путь!
cp dist/index.html /path/to/django/templates/index.html
```

#### 2.2 Скопируйте статические файлы

```bash
# Создайте папку static/assets если её нет
mkdir -p /path/to/django/static/assets

# Скопируйте все из dist/assets/
cp -r dist/assets/* /path/to/django/static/assets/
```

---

### Шаг 3: Настройте Django

#### 3.1 Обновите `settings.py`

Добавьте/проверьте эти настройки:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Шаблоны
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # ← ДОБАВИТЬ!
        'APP_DIRS': True,
        # ... остальное без изменений
    },
]

# Статические файлы
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # ← ДОБАВИТЬ!
]

# Медиа файлы
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

#### 3.2 Обновите `urls.py` (главный файл проекта)

```python
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Ваши API endpoints
    path('api/', include('your_app.urls')),  # Замените на ваше приложение
    
    # ⚠️ ВАЖНО: Это должно быть ПОСЛЕДНИМ!
    # React приложение (catch-all)
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]

# Медиа и статика в DEBUG режиме
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

---

### Шаг 4: Обновите пути в `index.html`

Откройте `/path/to/django/templates/index.html` в текстовом редакторе.

**Было:**
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <script type="module" crossorigin src="/assets/index-abc123.js"></script>
    <link rel="stylesheet" crossorigin href="/assets/index-xyz789.css">
  </head>
  ...
```

**Должно стать:**
```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
  <head>
    <script type="module" crossorigin src="{% static 'assets/index-abc123.js' %}"></script>
    <link rel="stylesheet" crossorigin href="{% static 'assets/index-xyz789.css' %}">
  </head>
  ...
```

**Изменения:**
1. Добавьте `{% load static %}` в самое начало файла
2. Замените `/assets/...` на `{% static 'assets/...' %}`

---

### Шаг 5: Соберите статические файлы

```bash
cd /path/to/django
python manage.py collectstatic --noinput
```

---

### Шаг 6: Запустите и проверьте

```bash
# Запуск Django
python manage.py runserver

# Откройте браузер
# http://localhost:8000/
```

**Проверьте:**
- ✅ Главная страница загружается
- ✅ Можно войти/зарегистрироваться
- ✅ API запросы работают
- ✅ Изображения и аудио отображаются
- ✅ Переходы между страницами работают

---

## 🔧 Если что-то не работает

### Проблема: Белый экран

**Откройте консоль браузера (F12)**

Если видите ошибки типа:
```
GET http://localhost:8000/assets/index-abc123.js 404 (Not Found)
```

**Решение:**
1. Проверьте, что файлы есть в `/path/to/django/static/assets/`
2. Проверьте, что в `index.html` используются `{% static '...' %}` теги
3. Запустите `python manage.py collectstatic` ещё раз

---

### Проблема: 404 на внутренних страницах

При переходе на `/decks` или `/profile` получаете 404.

**Решение:**
Убедитесь, что catch-all route (`re_path(r'^.*$', ...)`) **ПОСЛЕДНИЙ** в `urls.py`!

```python
urlpatterns = [
    path('api/', ...),  # API ПЕРВЫМ
    re_path(r'^.*$', ...),  # React ПОСЛЕДНИМ
]
```

---

### Проблема: Изображения не загружаются

**Решение:**
Проверьте настройки медиа в `settings.py` и `urls.py`:

```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# urls.py
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 📋 Чеклист

- [ ] Выполнен `npm run build`
- [ ] Скопирован `dist/index.html` → `django/templates/index.html`
- [ ] Скопированы `dist/assets/*` → `django/static/assets/`
- [ ] Добавлен `{% load static %}` в начало `index.html`
- [ ] Заменены пути `/assets/...` на `{% static 'assets/...' %}`
- [ ] Обновлен `settings.py` (TEMPLATES, STATIC, MEDIA)
- [ ] Обновлен `urls.py` (catch-all route в конце)
- [ ] Выполнен `python manage.py collectstatic`
- [ ] Запущен сервер и проверена работа

---

## 🎉 Готово!

После выполнения всех шагов ваше приложение должно работать на Django бэкенде.

Для автоматизации используйте скрипт `deploy.sh` (см. DEPLOYMENT_GUIDE.md).
