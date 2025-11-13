# Руководство для разработчиков

## Настройка окружения разработки

### Требования

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+ (опционально, можно использовать SQLite для разработки)
- Git

### Backend

1. Создайте виртуальное окружение:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env`:
```bash
cp .env.example .env
# Отредактируйте .env с вашими настройками
```

4. Примените миграции:
```bash
python manage.py migrate
```

5. Создайте суперпользователя (опционально):
```bash
python manage.py createsuperuser
```

6. Запустите сервер:
```bash
python manage.py runserver
```

### Frontend

1. Установите зависимости:
```bash
cd frontend
npm install
```

2. Запустите dev сервер:
```bash
npm start
```

## Структура проекта

```
anki-card-generator/
├── backend/
│   ├── apps/
│   │   ├── users/       # Аутентификация и пользователи
│   │   ├── words/       # Модель слов
│   │   └── cards/       # Генерация карточек
│   ├── config/          # Настройки Django
│   └── media/           # Медиафайлы
│
├── frontend/
│   ├── src/
│   │   ├── components/  # React компоненты
│   │   ├── services/    # API клиент
│   │   └── types/       # TypeScript типы
│   └── public/
│
└── docs/                # Документация
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

### Frontend

- React DevTools
- Browser DevTools
- Console.log для отладки

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

# Собрать статические файлы
python manage.py collectstatic
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

