# Инструкция по настройке проекта

## Этап 1: Настройка проекта и инфраструктуры ✅

### Что уже сделано:

1. ✅ Создана структура проекта
2. ✅ Настроен Django backend с базовой конфигурацией
3. ✅ Настроен React frontend с TypeScript и TailwindCSS
4. ✅ Создана система документации
5. ✅ Настроена базовая структура тестов

### Следующие шаги:

#### 1. Установка зависимостей Backend

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Настройка переменных окружения

Создайте файл `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/anki_db
# Или оставьте пустым для использования SQLite

SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
MEDIA_ROOT=media
MEDIA_URL=/media/
```

#### 3. Применение миграций

```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

#### 4. Создание суперпользователя (опционально)

```bash
python manage.py createsuperuser
```

#### 5. Установка зависимостей Frontend

```bash
cd frontend
npm install
```

#### 6. Запуск приложения

**Backend (в одном терминале):**
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

**Frontend (в другом терминале):**
```bash
cd frontend
npm start
```

Приложение будет доступно по адресу `http://localhost:3000`

### Проверка установки

1. Backend должен отвечать на `http://localhost:8000/admin/`
2. Frontend должен открываться на `http://localhost:3000`
3. Проверьте, что нет ошибок в консоли

### Следующий этап

После успешной настройки переходите к **Этапу 2: Backend - Модели данных и аутентификация**

См. `DEVELOPMENT_PLAN.md` для детального плана.

