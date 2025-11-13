# Архитектура приложения

## Общая архитектура

Приложение построено по принципу клиент-серверной архитектуры:

```
┌─────────────┐         HTTP/REST API         ┌─────────────┐
│   Frontend  │ ◄──────────────────────────► │   Backend   │
│   (React)   │                               │   (Django)  │
└─────────────┘                               └─────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────┐
                                              │  PostgreSQL │
                                              └─────────────┘
```

## Backend архитектура

### Структура приложений

```
backend/
├── apps/
│   ├── users/          # Аутентификация и управление пользователями
│   │   ├── models.py   # Модель User (расширение стандартной)
│   │   ├── views.py    # API views для регистрации/входа
│   │   ├── serializers.py
│   │   └── urls.py
│   │
│   ├── words/          # Управление словами
│   │   ├── models.py   # Модель Word
│   │   ├── views.py    # API для работы со словами
│   │   ├── serializers.py
│   │   └── urls.py
│   │
│   └── cards/          # Генерация карточек Anki
│       ├── views.py    # API для генерации .apkg
│       ├── utils.py    # Утилиты для работы с genanki
│       └── urls.py
│
└── config/
    ├── settings.py     # Настройки Django
    └── urls.py         # Главный URL router
```

### Поток данных

1. **Регистрация/Вход:**
   - Frontend → POST `/api/auth/register/` или `/api/auth/login/`
   - Backend → Создание/проверка пользователя
   - Backend → Возврат токена
   - Frontend → Сохранение токена в localStorage

2. **Генерация карточек:**
   - Frontend → POST `/api/cards/generate/` (с токеном)
   - Backend → Валидация данных
   - Backend → Сохранение слов в БД
   - Backend → Генерация .apkg через genanki
   - Backend → Возврат ссылки на скачивание
   - Frontend → GET `/api/cards/download/<file_id>/`
   - Frontend → Скачивание файла

## Frontend архитектура

### Структура компонентов

```
frontend/src/
├── components/         # React компоненты
│   ├── WordInput.tsx
│   ├── LanguageSelector.tsx
│   ├── GenerateButton.tsx
│   └── ...
│
├── services/           # API клиент
│   └── api.ts
│
├── types/             # TypeScript типы
│   └── index.ts
│
├── contexts/           # React Contexts
│   └── AuthContext.tsx
│
└── App.tsx            # Главный компонент
```

### Поток данных в Frontend

1. **Аутентификация:**
   - Пользователь вводит данные
   - Компонент вызывает `apiService.login()` или `apiService.register()`
   - Токен сохраняется в localStorage
   - Состояние аутентификации обновляется через Context

2. **Генерация карточек:**
   - Пользователь вводит слова и переводы
   - Компонент собирает данные
   - Вызов `apiService.generateCards()`
   - Получение ссылки на скачивание
   - Автоматическое скачивание файла

## База данных

### Схема

```
User
├── id (PK)
├── username
├── email
├── password (hashed)
├── preferred_language
└── created_at

Word
├── id (PK)
├── user (FK → User)
├── original_word
├── translation
├── language
├── audio_file (nullable)
├── image_file (nullable)
├── created_at
└── updated_at

Index: (user, original_word, language) - unique
```

## Безопасность

- Аутентификация через токены (DRF Token Authentication)
- CORS настроен только для разрешенных доменов
- Валидация всех входных данных
- Изоляция данных пользователей (каждый видит только свои слова)

## Масштабируемость

- Модульная структура приложений
- RESTful API для легкого расширения
- Готовность к добавлению новых языков
- Возможность добавления автоматизации (переводы, TTS, изображения)

