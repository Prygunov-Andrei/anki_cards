# Руководство по тестированию

## Backend тесты (pytest)

### Установка зависимостей

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=apps --cov-report=html

# Конкретный файл
pytest apps/users/tests.py

# Конкретный тест
pytest apps/users/tests.py::test_user_registration
```

### Структура тестов

Тесты находятся в каждом приложении в файле `tests.py`:

```
apps/
├── users/
│   └── tests.py
├── words/
│   └── tests.py
└── cards/
    └── tests.py
```

### Пример теста

```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    assert user.username == 'testuser'
    assert user.check_password('testpass123')
```

## Frontend тесты (Jest)

### Установка зависимостей

```bash
cd frontend
npm install
```

### Запуск тестов

```bash
# Все тесты
npm test

# С покрытием
npm test -- --coverage

# В watch режиме
npm test -- --watch
```

### Структура тестов

Тесты находятся рядом с компонентами:

```
src/
├── components/
│   ├── WordInput.tsx
│   └── WordInput.test.tsx
```

## Интеграционные тесты

Интеграционные тесты проверяют взаимодействие между frontend и backend.

### Запуск

```bash
# Запустить backend
cd backend && python manage.py runserver

# В другом терминале запустить frontend
cd frontend && npm start

# Запустить интеграционные тесты
npm run test:integration
```

## Покрытие кода

Цель: минимум 70% покрытия кода тестами.

### Backend

```bash
pytest --cov=apps --cov-report=html
# Открыть htmlcov/index.html в браузере
```

### Frontend

```bash
npm test -- --coverage
# Отчет будет в coverage/lcov-report/index.html
```

