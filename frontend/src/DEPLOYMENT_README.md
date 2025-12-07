# 🚀 Деплой фронтенда на Django - Краткая инструкция

## 📚 Доступные гайды

### 1. **QUICK_DEPLOY.md** - Быстрый старт (5 минут)
Простая пошаговая инструкция для ручного деплоя.
Рекомендуется для первого деплоя.

### 2. **DEPLOYMENT_GUIDE.md** - Полная документация
Детальное руководство со всеми настройками, troubleshooting и production конфигурацией.

### 3. **deploy.sh** - Автоматический деплой
Bash скрипт для автоматизации всего процесса.

### 4. **update_django_paths.py** - Утилита для обновления путей
Python скрипт для корректной замены путей в index.html.

---

## ⚡ Самый быстрый способ

### Вариант 1: Автоматический (рекомендуется)

```bash
# 1. Откройте deploy.sh и укажите путь к Django
nano deploy.sh
# Измените: DJANGO_PATH="/path/to/your/django/project"

# 2. Сделайте скрипт исполняемым
chmod +x deploy.sh

# 3. Запустите деплой
./deploy.sh
```

### Вариант 2: Ручной (для понимания процесса)

```bash
# 1. Соберите фронтенд
npm run build

# 2. Скопируйте файлы
cp dist/index.html /path/to/django/templates/
cp -r dist/assets /path/to/django/static/

# 3. Обновите пути в index.html
python update_django_paths.py /path/to/django/templates/index.html

# 4. Collectstatic
cd /path/to/django
python manage.py collectstatic --noinput

# 5. Запустите сервер
python manage.py runserver
```

---

## 🎯 Что нужно сделать в Django (один раз)

### settings.py

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # ← Добавить!
        'APP_DIRS': True,
        'OPTIONS': {...},
    },
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # ← Добавить!
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### urls.py

```python
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('your_app.urls')),  # ← Ваши API
    
    # ⚠️ Это должно быть ПОСЛЕДНИМ!
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

---

## 📁 Структура Django после деплоя

```
your-django-project/
├── manage.py
├── your_app/
│   ├── settings.py          # Обновлён
│   ├── urls.py              # Обновлён
│   └── ...
├── templates/
│   └── index.html           # ← Скопирован из dist/
├── static/
│   └── assets/              # ← Скопирован из dist/
│       ├── index-abc123.js
│       ├── index-xyz789.css
│       └── ...
├── staticfiles/             # ← Создаётся collectstatic
└── media/                   # ← Загруженные медиа
```

---

## ✅ Чеклист проверки

После деплоя откройте `http://localhost:8000/` и проверьте:

- [ ] Главная страница загружается
- [ ] Нет ошибок в консоли браузера (F12)
- [ ] Можно войти/зарегистрироваться
- [ ] API запросы работают
- [ ] Генерация карточек работает
- [ ] Изображения и аудио отображаются
- [ ] Переходы между страницами работают (/decks, /profile)
- [ ] Можно создавать и редактировать колоды

---

## 🔧 Troubleshooting

### Белый экран

**Причина:** Не загружаются JS/CSS файлы

**Решение:**
1. Проверьте консоль браузера (F12)
2. Убедитесь, что в `index.html` используются `{% static '...' %}`
3. Запустите `python manage.py collectstatic`

### 404 на /decks, /profile

**Причина:** Catch-all route не последний в urls.py

**Решение:**
```python
urlpatterns = [
    path('api/', ...),        # API первым
    re_path(r'^.*$', ...),   # React последним
]
```

### CORS ошибки

**Причина:** Фронтенд и бэкенд на разных доменах

**Решение:**
После деплоя на Django - фронтенд и бэкенд на одном домене, CORS не нужен.

---

## 🎉 Готово!

После выполнения инструкций ваше приложение будет работать на Django.

**Для повторного деплоя (после изменений):**
```bash
./deploy.sh  # Автоматически всё обновит
```

---

## 📖 Дополнительные материалы

- **QUICK_DEPLOY.md** - Подробная пошаговая инструкция
- **DEPLOYMENT_GUIDE.md** - Полное руководство с настройками для продакшена
- **deploy.sh** - Автоматизация деплоя
- **update_django_paths.py** - Утилита для обновления путей

---

## 💡 Полезные команды

```bash
# Пересборка и деплой
npm run build && ./deploy.sh

# Только collectstatic
cd /path/to/django && python manage.py collectstatic --noinput

# Запуск Django в production режиме
cd /path/to/django && gunicorn your_project.wsgi:application --bind 0.0.0.0:8000

# Проверка размера билда
du -sh dist/
```

---

**Успешного деплоя! 🚀**
