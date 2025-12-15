# Установка и настройка

## Требования

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+ (опционально, можно использовать SQLite для разработки)
- Git

## Быстрый старт

Для быстрого запуска используйте скрипт из корня проекта:

```bash
./start.sh
```

Скрипт автоматически:
- Создаст виртуальное окружение (если не существует)
- Установит все зависимости
- Применит миграции
- Запустит backend и frontend

## Подробная установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/Prygunov-Andrei/anki_cards.git
cd anki_cards
```

### 2. Настройка Backend (Django)

#### Создание виртуального окружения

```bash
cd backend
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

#### Установка зависимостей

```bash
pip install -r requirements.txt
```

#### Настройка переменных окружения

Создайте файл `backend/.env`:

```env
# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/anki_db
# Или оставьте пустым для использования SQLite

# Django настройки
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Медиафайлы
MEDIA_ROOT=media
MEDIA_URL=/media/

# OpenAI API (для генерации медиа)
OPENAI_API_KEY=your-openai-api-key-here

# Google Gemini API (опционально)
GEMINI_API_KEY=your-gemini-api-key-here
```

#### Применение миграций

```bash
python manage.py migrate
```

#### Создание суперпользователя (опционально)

```bash
python manage.py createsuperuser
```

#### Запуск сервера

```bash
python manage.py runserver
```

Backend будет доступен на `http://localhost:8000`

### 3. Настройка Frontend (React)

#### Установка зависимостей

```bash
cd frontend
npm install
```

#### Запуск dev сервера

```bash
npm start
```

Frontend будет доступен на `http://localhost:3000`

## Разработка с ngrok

Для подключения облачного фронтенда (Figma Make) к локальному бэкенду используется **ngrok**:

```bash
# 1. Запустите бэкенд
./start.sh

# 2. Запустите ngrok туннель (в отдельном терминале)
ngrok http 8000

# 3. Используйте публичный URL в настройках фронтенда
```

Подробнее см. [Workflow разработки](../getting-started/workflow.md)

## Полезные команды

### Backend

```bash
# Создать миграции
python manage.py makemigrations

# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Запустить тесты
pytest

# Запустить тесты с покрытием
pytest --cov=apps --cov-report=html
```

### Frontend

```bash
# Запустить dev сервер
npm start

# Собрать для production
npm run build

# Запустить тесты
npm test
```

## Проверка установки

1. Backend должен отвечать на `http://localhost:8000/admin/`
2. Frontend должен открываться на `http://localhost:3000`
3. Проверьте, что нет ошибок в консоли
4. Запустите тесты: `pytest` (backend) и `npm test` (frontend)

## Следующие шаги

После успешной установки:

1. Ознакомьтесь с [API документацией](../api/README.md)
2. Изучите [архитектуру приложения](../architecture/README.md)
3. Посмотрите [план разработки](../development/DEVELOPMENT_PLAN.md)
4. Проверьте [workflow разработки](../getting-started/workflow.md)

