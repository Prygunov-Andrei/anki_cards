# 🚀 Деплой приложения

## Обзор

Приложение состоит из:
- **Backend**: Django + PostgreSQL
- **Frontend**: React + Vite (собирается в статические файлы, отдается через Nginx)
- **Database**: PostgreSQL

Все компоненты контейнеризированы с помощью Docker.

---

## 📋 Предварительные требования

> **⚠️ ВАЖНО:** Перед деплоем обязательно создайте бэкап данных!  
> См. [Миграция данных](./DATA_MIGRATION.md) для подробностей.

### На сервере должны быть установлены:

1. **Docker** (версия 20.10+)
2. **Docker Compose** (версия 2.0+)
3. **Git**

### Проверка установки:

```bash
docker --version
docker-compose --version
git --version
```

---

## 🔧 Подготовка к деплою

### 1. Создание бэкапа данных (ВАЖНО!)

**⚠️ Перед деплоем обязательно создайте бэкап существующих данных!**

Если у вас есть важные данные (колоды, слова, пользователи), создайте бэкап:

```bash
./scripts/backup_data.sh
```

Скрипт создаст архив `backups/anki_backup_YYYYMMDD_HHMMSS.tar.gz` содержащий:
- Все данные из базы данных (JSON)
- Все медиафайлы (изображения, аудио, аватары)

**Бэкап будет сохранен в папке `backups/` (в .gitignore)**

### 2. Синхронизация фронтенда (если нужно)

Если были изменения фронтенда в Figma Make:

```bash
./scripts/sync_frontend.sh
```

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
cp .env.example .env
nano .env  # или используйте любой редактор
```

**Обязательные переменные:**

```env
# Database
POSTGRES_DB=anki_db
POSTGRES_USER=anki_user
POSTGRES_PASSWORD=strong_password_here

# Django
SECRET_KEY=your-very-secret-key-here-generate-with-openssl
DEBUG=False
# ВАЖНО: backend - для внутренних запросов Docker network
ALLOWED_HOSTS=backend,localhost,127.0.0.1,yourdomain.com,www.yourdomain.com

# OpenAI (ОБЯЗАТЕЛЬНО для генерации медиа)
OPENAI_API_KEY=sk-proj-...

# Google Gemini (опционально)
GEMINI_API_KEY=AIzaSy...
```

**Генерация SECRET_KEY:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Настройка backend/.env

Создайте `backend/.env`:

```bash
cd backend
cp .env.example .env  # если есть
nano .env
```

Минимум:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIzaSy...  # опционально
```

---

## 🐳 Локальное тестирование Docker

Перед деплоем на сервер протестируйте локально:

```bash
# Сборка образов
docker-compose build

# Запуск
docker-compose up -d

# Проверка логов
docker-compose logs -f

# Остановка
docker-compose down
```

Приложение будет доступно:
- Frontend: http://localhost
- Backend API: http://localhost/api/
- Admin: http://localhost/admin/

---

## 📤 Деплой на удаленный сервер

### Вариант 1: Через Git (рекомендуется)

1. **На сервере клонируйте репозиторий:**

```bash
git clone https://github.com/your-username/anki_cards.git
cd anki_cards
```

2. **Создайте `.env` файл:**

```bash
cp .env.example .env
nano .env  # заполните все переменные
```

3. **Создайте `backend/.env`:**

```bash
cd backend
cp .env.example .env  # если есть
nano .env
cd ..
```

4. **Соберите и запустите:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

5. **Проверьте статус:**

```bash
docker-compose ps
docker-compose logs -f
```

### Вариант 2: Через SCP (альтернатива)

1. **Локально соберите архив:**

```bash
tar -czf anki_cards.tar.gz \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.env' \
  --exclude='backend/.env' \
  .
```

2. **Скопируйте на сервер:**

```bash
scp anki_cards.tar.gz user@your-server:/path/to/destination/
```

3. **На сервере:**

```bash
cd /path/to/destination
tar -xzf anki_cards.tar.gz
cd anki_cards
# Создайте .env файлы
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 📦 Миграция данных на сервер

### Восстановление данных из бэкапа

После деплоя на новый сервер восстановите данные:

1. **Скопируйте архив бэкапа на сервер:**

```bash
# С локальной машины
scp backups/anki_backup_*.tar.gz user@your-server:/path/to/anki_cards/
```

2. **На сервере восстановите данные:**

```bash
cd /path/to/anki_cards
./scripts/restore_data.sh backups/anki_backup_YYYYMMDD_HHMMSS.tar.gz
```

Скрипт:
- Распакует архив
- Применит миграции БД
- Импортирует данные
- Скопирует медиафайлы
- Соберет статические файлы

3. **Проверьте восстановление:**

- Откройте админку: `http://your-server/admin/`
- Проверьте наличие колод, пользователей
- Проверьте медиафайлы

### Ручное восстановление (если скрипт не работает)

```bash
# Распаковка
tar -xzf anki_backup_*.tar.gz

# Импорт данных
docker-compose exec backend python manage.py loaddata /path/to/data.json

# Копирование медиафайлов
docker cp media/. $(docker-compose ps -q backend):/app/media/
```

---

## 🔄 Обновление приложения

### Обновление кода:

```bash
# На сервере
cd /path/to/anki_cards

# Получить последние изменения
git pull origin main

# Если были изменения фронтенда, синхронизируйте
./scripts/sync_frontend.sh

# Пересобрать и перезапустить
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Применить миграции (если были изменения в БД)
docker-compose exec backend python manage.py migrate
```

### Обновление только фронтенда:

```bash
# Синхронизация
./scripts/sync_frontend.sh

# Пересборка только фронтенда
docker-compose build frontend
docker-compose up -d frontend
```

---

## 🛠️ Управление контейнерами

### Просмотр логов:

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend
```

### Остановка:

```bash
docker-compose down
```

### Остановка с удалением volumes (⚠️ удалит данные БД):

```bash
docker-compose down -v
```

### Перезапуск:

```bash
docker-compose restart
```

### Выполнение команд в контейнере:

```bash
# Django shell
docker-compose exec backend python manage.py shell

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser

# Применение миграций
docker-compose exec backend python manage.py migrate

# Сборка статики
docker-compose exec backend python manage.py collectstatic --noinput
```

---

## 🔒 Настройка Nginx (опционально, для SSL)

Если нужен HTTPS, настройте Nginx как reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📊 Мониторинг

### Проверка здоровья:

```bash
# Backend health check
curl http://localhost:8000/health/

# Frontend
curl http://localhost/
```

### Статус контейнеров:

```bash
docker-compose ps
```

### Использование ресурсов:

```bash
docker stats
```

---

## 🐛 Решение проблем

### Проблема: Контейнеры не запускаются

```bash
# Проверьте логи
docker-compose logs

# Проверьте конфигурацию
docker-compose config
```

### Проблема: База данных не подключается

```bash
# Проверьте переменные окружения
docker-compose exec backend env | grep DATABASE

# Проверьте доступность БД
docker-compose exec backend python manage.py dbshell
```

### Проблема: Статические файлы не загружаются

```bash
# Пересоберите статику
docker-compose exec backend python manage.py collectstatic --noinput
```

### Проблема: Медиафайлы не отдаются

Проверьте:
1. Права доступа к `backend/media/`
2. Настройки `MEDIA_ROOT` и `MEDIA_URL` в `settings.py`
3. Конфигурацию Nginx в `frontend/nginx.conf`

---

## 📝 Чек-лист деплоя

### Перед деплоем:
- [ ] **Создан бэкап данных** (`./scripts/backup_data.sh`)
- [ ] Docker и Docker Compose установлены
- [ ] `.env` файл создан и заполнен
- [ ] `backend/.env` создан и заполнен
- [ ] `SECRET_KEY` сгенерирован
- [ ] `OPENAI_API_KEY` указан
- [ ] `ALLOWED_HOSTS` содержит домен сервера
- [ ] `DEBUG=False` в продакшене
- [ ] Локальное тестирование прошло успешно

### Деплой:
- [ ] Код загружен на сервер
- [ ] Контейнеры запущены и работают
- [ ] Health check проходит
- [ ] Миграции применены
- [ ] **Данные восстановлены из бэкапа** (`./scripts/restore_data.sh`)
- [ ] Медиафайлы скопированы
- [ ] Создан суперпользователь (если нужно)
- [ ] SSL настроен (если нужен)

### После деплоя:
- [ ] Проверена работа админки
- [ ] Проверены данные (колоды, пользователи)
- [ ] Проверены медиафайлы
- [ ] Проверена работа API
- [ ] Проверена работа фронтенда

---

## 🔐 Безопасность

1. **Никогда не коммитьте `.env` файлы в Git**
2. **Используйте сильные пароли для БД**
3. **В продакшене всегда `DEBUG=False`**
4. **Настройте файрвол на сервере**
5. **Используйте HTTPS (SSL)**
6. **Регулярно обновляйте зависимости**

---

**Последнее обновление:** 7 декабря 2025
