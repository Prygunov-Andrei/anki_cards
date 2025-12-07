# 📝 Шпаргалка по деплою - Для копирования команд

## 🚀 Быстрый деплой (скопируйте и выполните)

### 1️⃣ Настройте скрипт деплоя

```bash
# Откройте deploy.sh в редакторе
nano deploy.sh

# Найдите строку (строка 17):
DJANGO_PATH="/path/to/your/django/project"

# Замените на реальный путь, например:
DJANGO_PATH="/home/user/my-django-anki"

# Сохраните: Ctrl+O, Enter, Ctrl+X
```

### 2️⃣ Запустите автоматический деплой

```bash
# Сделайте скрипт исполняемым (один раз)
chmod +x deploy.sh

# Запустите деплой
./deploy.sh
```

**Готово!** Скрипт автоматически:
- ✅ Соберёт билд
- ✅ Скопирует файлы
- ✅ Обновит пути
- ✅ Запустит collectstatic

### 3️⃣ Запустите Django

```bash
# Перейдите в папку Django (замените путь!)
cd /home/user/my-django-anki

# Запустите сервер
python manage.py runserver

# Откройте в браузере:
# http://localhost:8000/
```

---

## 🔧 Настройка Django (один раз)

### Файл: `settings.py`

Найдите и обновите эти секции:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Секция TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # ← Добавьте эту строку!
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

# Секция STATIC (добавьте/обновите)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # ← Добавьте эту строку!
]

# Секция MEDIA (добавьте если нет)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### Файл: главный `urls.py` (обычно в папке проекта)

```python
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ← Ваши API endpoints (замените на реальные!)
    path('api/', include('your_app.urls')),
    
    # ⚠️ ВАЖНО: Эта строка должна быть ПОСЛЕДНЕЙ!
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]

# Для режима DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

---

## 📋 Ручной деплой (без скрипта)

Если хотите сделать всё вручную:

```bash
# 1. Соберите билд
npm run build

# 2. Скопируйте index.html (замените путь!)
cp dist/index.html /home/user/my-django-anki/templates/index.html

# 3. Создайте папку для assets
mkdir -p /home/user/my-django-anki/static/assets

# 4. Скопируйте assets
cp -r dist/assets/* /home/user/my-django-anki/static/assets/

# 5. Обновите пути в index.html
python update_django_paths.py /home/user/my-django-anki/templates/index.html

# 6. Collectstatic
cd /home/user/my-django-anki
python manage.py collectstatic --noinput

# 7. Запустите сервер
python manage.py runserver
```

---

## 🔄 Повторный деплой (после изменений)

Когда вы изменили код фронтенда и хотите обновить:

```bash
# Просто запустите скрипт снова!
./deploy.sh
```

Или вручную:

```bash
npm run build && \
cp dist/index.html /path/to/django/templates/ && \
cp -r dist/assets/* /path/to/django/static/assets/ && \
python update_django_paths.py /path/to/django/templates/index.html && \
cd /path/to/django && \
python manage.py collectstatic --noinput
```

---

## 🐛 Если что-то не работает

### Белый экран

```bash
# 1. Откройте консоль браузера (F12)
# 2. Ищите ошибки 404 для JS/CSS файлов

# Решение:
cd /path/to/django
python manage.py collectstatic --noinput
python manage.py runserver
```

### 404 на страницах (/decks, /profile)

Проверьте `urls.py`:
- Catch-all route (`re_path(r'^.*$', ...)`) должен быть **ПОСЛЕДНИМ**!

### Изображения не грузятся

```bash
# Проверьте MEDIA_URL и MEDIA_ROOT в settings.py
# Убедитесь, что в urls.py добавлены static/media routes
```

---

## 📦 Production деплой

Для реального сервера:

```bash
# 1. Установите Gunicorn
pip install gunicorn

# 2. Запустите
gunicorn your_project.wsgi:application --bind 0.0.0.0:8000 --workers 4

# 3. Настройте Nginx для раздачи статики (см. DEPLOYMENT_GUIDE.md)
```

---

## 💡 Полезные команды

```bash
# Проверить размер билда
du -sh dist/

# Очистить старые static файлы
rm -rf /path/to/django/staticfiles/*

# Пересоздать миграции
cd /path/to/django
python manage.py makemigrations
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Проверить настройки Django
python manage.py check
```

---

## 📂 Структура файлов

После деплоя ваш Django проект должен выглядеть так:

```
my-django-anki/
├── manage.py
├── config/                    # Или название вашего проекта
│   ├── settings.py           # ← Обновлён
│   ├── urls.py               # ← Обновлён
│   └── wsgi.py
├── api/                       # Ваше API приложение
│   ├── views.py
│   ├── urls.py
│   └── ...
├── templates/                 # ← Создайте если нет
│   └── index.html            # ← Скопирован из фронтенда
├── static/                    # ← Создайте если нет
│   └── assets/               # ← Скопирован из фронтенда
│       ├── index-abc.js
│       ├── index-xyz.css
│       └── ...
├── staticfiles/              # ← Создаётся collectstatic
│   └── assets/
├── media/                     # Загруженные медиа
│   ├── images/
│   └── audio/
└── db.sqlite3
```

---

## ✅ Финальная проверка

После деплоя откройте `http://localhost:8000/` и проверьте:

```
✅ Главная страница загружается
✅ Нет ошибок в консоли (F12)
✅ Можно войти/зарегистрироваться
✅ API запросы работают (/api/...)
✅ Изображения и аудио отображаются
✅ Переходы работают (/decks, /profile, и т.д.)
✅ Можно создать колоду
✅ Можно сгенерировать карточки
✅ Файл .apkg скачивается
```

---

**Копируйте команды из этого файла и выполняйте! 🚀**
