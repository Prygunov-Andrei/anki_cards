# Руководство по тестированию

## Backend тестирование

### Запуск тестов

```bash
cd backend
source venv/bin/activate
pytest
```

### Тесты с покрытием

```bash
pytest --cov=apps --cov-report=html
```

Отчет будет доступен в `backend/htmlcov/index.html`

### Запуск конкретных тестов

```bash
# Тесты конкретного приложения
pytest apps/users/tests.py

# Тесты конкретного класса
pytest apps/users/tests.py::TestUserAPI

# Тесты конкретного метода
pytest apps/users/tests.py::TestUserAPI::test_register
```

## Frontend тестирование

### Запуск тестов

```bash
cd frontend
npm test
```

### Тесты в watch режиме

```bash
npm test -- --watch
```

## Интеграционное тестирование

### Тестирование API

Используйте Postman или curl для тестирования endpoints:

```bash
# Регистрация
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"test123"}'

# Генерация карточек
curl -X POST http://localhost:8000/api/cards/generate/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"words":["test"],"language":"en","translations":{"test":"тест"},"deck_name":"Test"}'
```

## Docker тестирование

См. [Docker тестирование](./deployment/DOCKER_TESTING.md)

