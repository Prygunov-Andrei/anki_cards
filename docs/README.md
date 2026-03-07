# Документация проекта Anki Card Generator

## Структура документации

### 🚀 Для быстрого старта

- **[Установка и настройка](./getting-started/setup.md)** — полное руководство по установке, настройке и разработке
- **[Workflow разработки](./getting-started/workflow.md)** — ежедневный workflow разработки с Frontend (Figma Make) и Backend

### 📚 Техническая документация

- **[API Документация](./api/README.md)** — описание всех API endpoints с примерами запросов и ответов
- **[Архитектура](./architecture/README.md)** — архитектура приложения, структура проекта, формат .apkg файлов, модели OpenAI/Gemini
- **[Руководство по тестированию](./testing.md)** — как запускать тесты для backend и frontend

### 🛠 Разработка

- **[План разработки Backend](./development/DEVELOPMENT_PLAN.md)** — детальный поэтапный план разработки Backend (завершен)
- **[Техническое задание Frontend](./development/FRONTEND_TASKS.md)** — полное ТЗ для Frontend разработчика (18 этапов)
- **[Workflow разработки](./getting-started/workflow.md)** — как работать с Frontend (Figma Make) + Backend (локально)

### 🚀 Деплой

- **[Деплой приложения](./deployment/DEPLOYMENT.md)** — полная инструкция по деплою с Docker
- **[Миграция данных](./deployment/DATA_MIGRATION.md)** — создание бэкапа и восстановление данных
- **[HTTPS настройка](./deployment/HTTPS_SETUP.md)** — настройка SSL сертификатов
- **[Docker тестирование](./deployment/DOCKER_TESTING.md)** — тестирование Docker контейнеров

### ⚙️ Функции

- **[Синхронизация Anki](./features/ANKI_SYNC.md)** — документация по серверу синхронизации Anki
- **[Варианты синхронизации](./features/ANKI_SYNC_OPTIONS.md)** — варианты реализации синхронизации
- **[Генерация .apkg](./features/APKG_GENERATION_GUIDE.md)** — руководство по генерации файлов Anki
- **[Распознавание слов с фото](./features/PHOTO_WORD_EXTRACTION.md)** — извлечение слов из фотографий текста
- **[Система токенов](./TOKEN_SYSTEM.md)** — описание системы внутренней валюты

### 📊 Планирование и статус

- **[Статус проекта](./status.md)** — текущий прогресс разработки по этапам

## Быстрый запуск

Для быстрого запуска используйте скрипт из корня проекта:

```bash
./start.sh
```

Подробная инструкция по установке: см. [setup.md](./getting-started/setup.md)

## Навигация по документации

### Новичок в проекте?

1. Начните с [README.md](../README.md) в корне проекта
2. Прочитайте [установку и настройку](./getting-started/setup.md)
3. Изучите [архитектуру](./architecture/README.md) для понимания структуры
4. Посмотрите [workflow разработки](./getting-started/workflow.md)

### Разработчик?

1. [Установка и настройка](./getting-started/setup.md) — настройка окружения разработки
2. [Workflow разработки](./getting-started/workflow.md) — ежедневный workflow
3. [API Документация](./api/README.md) — все доступные endpoints
4. [Архитектура](./architecture/README.md) — понимание структуры кода
5. [Тестирование](./testing.md) — запуск и написание тестов
6. [План разработки](./development/DEVELOPMENT_PLAN.md) — детальный план по этапам

### Деплой?

1. [Деплой приложения](./deployment/DEPLOYMENT.md) — полная инструкция
2. [HTTPS настройка](./deployment/HTTPS_SETUP.md) — настройка SSL
3. [Миграция данных](./deployment/DATA_MIGRATION.md) — бэкап и восстановление

### Планирование?

1. [План разработки](./development/DEVELOPMENT_PLAN.md) — детальный план по этапам
2. [Статус проекта](./status.md) — текущий прогресс
3. [Техническое задание Frontend](./development/FRONTEND_TASKS.md) — задачи для Frontend

## Структура документации

```
docs/
├── README.md                    # Этот файл
├── getting-started/             # Для новичков
│   ├── setup.md
│   └── workflow.md
├── development/                 # Разработка
│   ├── DEVELOPMENT_PLAN.md
│   ├── FRONTEND_TASKS.md
│   └── ...
├── deployment/                  # Деплой
│   ├── DEPLOYMENT.md
│   ├── HTTPS_SETUP.md
│   └── ...
├── features/                    # Функции
│   ├── ANKI_SYNC.md
│   ├── APKG_GENERATION_GUIDE.md
│   └── ...
├── api/                         # API документация
│   └── README.md
├── architecture/                # Архитектура
│   └── README.md
├── testing.md                   # Тестирование
├── status.md                    # Статус проекта
└── TOKEN_SYSTEM.md             # Система токенов
```

## Полезные ссылки

- [GitHub репозиторий](https://github.com/Prygunov-Andrei/anki_cards)
- [Документация Django](https://docs.djangoproject.com/)
- [Документация React](https://react.dev/)
- [Документация Anki](https://docs.ankiweb.net/)
