# Руководство по установке и настройке

## Требования

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+ (опционально, можно использовать SQLite для разработки)
- Git

## Быстрый старт

Для быстрого запуска используйте скрипт `start.sh`:

```bash
./start.sh
```

Скрипт автоматически:
- Создаст виртуальное окружение (если не существует)
- Установит все зависимости
- Применит миграции
- Создаст тестовых пользователей
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

## Структура проекта

```
anki-card-generator/
├── backend/                 # Django проект
│   ├── apps/
│   │   ├── users/          # Аутентификация и пользователи
│   │   ├── words/          # Модель слов
│   │   └── cards/          # Генерация карточек
│   ├── config/             # Настройки Django
│   ├── media/              # Медиафайлы
│   └── requirements.txt    # Python зависимости
│
├── frontend/                # React приложение
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── services/       # API клиент
│   │   ├── types/          # TypeScript типы
│   │   └── contexts/       # React Contexts
│   └── package.json        # Node.js зависимости
│
├── docs/                   # Документация
└── start.sh               # Скрипт быстрого запуска
```

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

# Собрать статические файлы
python manage.py collectstatic

# Запустить shell
python manage.py shell
```

### Frontend

```bash
# Запустить dev сервер
npm start

# Собрать для production
npm run build

# Запустить тесты
npm test

# Проверить линтер
npm run lint
```

## Стиль кода

### Python

- Следуйте PEP 8
- Используйте black для форматирования (опционально)
- Максимальная длина строки: 100 символов

### TypeScript/JavaScript

- Используйте ESLint
- Следуйте стандартам React
- Используйте функциональные компоненты с хуками

## Git workflow

1. Создайте ветку для новой функции:
```bash
git checkout -b feature/new-feature
```

2. Делайте коммиты часто с понятными сообщениями:
```bash
git commit -m "Add user registration endpoint"
```

3. Отправьте изменения:
```bash
git push origin feature/new-feature
```

4. Создайте Pull Request

## Отладка

### Backend

- Используйте `print()` или логирование
- Django Debug Toolbar (опционально)
- Проверяйте логи в консоли
- Используйте `python manage.py shell` для интерактивной отладки

### Frontend

- React DevTools
- Browser DevTools
- Console.log для отладки
- React компоненты с хуками для отладки состояния

## Проверка установки

1. Backend должен отвечать на `http://localhost:8000/admin/`
2. Frontend должен открываться на `http://localhost:3000`
3. Проверьте, что нет ошибок в консоли
4. Запустите тесты: `pytest` (backend) и `npm test` (frontend)

## Следующие шаги

После успешной установки:

1. Ознакомьтесь с [API документацией](./api.md)
2. Изучите [архитектуру приложения](./architecture.md)
3. Посмотрите [план разработки](./DEVELOPMENT_PLAN.md)
4. Проверьте [статус проекта](./status.md)
