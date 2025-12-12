# Процесс синхронизации и деплоя фронтенда

## Обзор

Фронтенд разрабатывается в отдельном репозитории на GitHub и синхронизируется в этот проект для деплоя. При синхронизации необходимо применять патчи для деплоя, чтобы сохранить конфигурацию продакшена.

## Структура процесса

```
[Фронтенд репозиторий] 
    ↓ (синхронизация)
[Текущий проект] 
    ↓ (применение патчей)
[Готово к деплою]
```

## Шаги процесса

### 1. Синхронизация фронтенда

```bash
./scripts/sync_frontend.sh
```

Этот скрипт:
- Клонирует/обновляет фронтенд из репозитория `https://github.com/Prygunov-Andrei/Ankiflashcardgenerator.git`
- Копирует файлы в `frontend/`
- Сохраняет защищенные файлы (`.env.production`)
- Создает маркер последней синхронизации

**Опции:**
- `--auto-commit` - автоматически закоммитить изменения
- `--review` - показать diff перед применением

### 2. Применение патчей для деплоя

```bash
./scripts/apply_deployment_patches.sh
```

Этот скрипт применяет необходимые изменения для деплоя:

1. **Создает `.env.production`** с `VITE_API_BASE_URL=/api`
2. **Проверяет/копирует `nginx.conf`** (конфигурация Nginx для фронтенда)
3. **Проверяет/копирует `Dockerfile`** (для сборки фронтенда)
4. **Проверяет `config.ts`** (логика определения API URL)
5. **Сохраняет патчи** в `scripts/deployment-patches/` для будущих синхронизаций

### 3. Проверка изменений

```bash
git status
git diff frontend/
```

### 4. Коммит изменений

```bash
git add frontend/
git commit -m "[SYNC] Update frontend and apply deployment patches

- Synced from Figma Make repository
- Applied deployment patches (nginx.conf, Dockerfile, .env.production)"
```

### 5. Деплой

Следуйте инструкциям в `docs/DEPLOYMENT.md`

## Файлы для деплоя

### Обязательные файлы

1. **`frontend/nginx.conf`**
   - Конфигурация Nginx для фронтенда
   - Проксирование запросов к бэкенду (`/api/`, `/admin/`, `/media/`)
   - Обработка SPA роутинга

2. **`frontend/Dockerfile`**
   - Multi-stage build для фронтенда
   - Сборка через Vite
   - Nginx для продакшена

3. **`frontend/.env.production`**
   - Переменные окружения для продакшена
   - `VITE_API_BASE_URL=/api` (относительный путь)

### Файлы, которые могут обновиться из репозитория

1. **`frontend/src/lib/config.ts`**
   - Логика определения API URL
   - Должна содержать проверку `import.meta.env?.PROD` для использования относительного пути `/api`

## Патчи для деплоя

Патчи хранятся в `scripts/deployment-patches/`:

- `nginx.conf` - конфигурация Nginx
- `Dockerfile` - Dockerfile для сборки

Эти файлы автоматически копируются при применении патчей, если они отсутствуют в `frontend/`.

## Автоматизация

### Полный процесс синхронизации и деплоя

```bash
# 1. Синхронизация
./scripts/sync_frontend.sh --auto-commit

# 2. Применение патчей
./scripts/apply_deployment_patches.sh

# 3. Коммит патчей
git add frontend/
git commit -m "[DEPLOY] Apply deployment patches"

# 4. Деплой
./scripts/deploy.sh
```

## Важные моменты

1. **`.env.production` не коммитится в репозиторий фронтенда**
   - Создается автоматически при применении патчей
   - Добавлен в `.gitignore` фронтенда

2. **`config.ts` должен содержать логику для продакшена**
   - Проверка `import.meta.env?.PROD`
   - Использование относительного пути `/api` в продакшене

3. **Патчи сохраняются автоматически**
   - При применении патчей файлы копируются в `scripts/deployment-patches/`
   - Это позволяет использовать их при следующих синхронизациях

4. **Маркер синхронизации**
   - Файл `.last_frontend_sync` содержит хеш последнего синхронизированного коммита
   - Скрипт пропускает синхронизацию, если коммит уже синхронизирован

## Устранение проблем

### Проблема: Патчи не применяются

**Решение:**
1. Проверьте наличие файлов в `scripts/deployment-patches/`
2. Если файлов нет, скопируйте их вручную:
   ```bash
   cp frontend/nginx.conf scripts/deployment-patches/
   cp frontend/Dockerfile scripts/deployment-patches/
   ```

### Проблема: API URL неправильный в продакшене

**Решение:**
1. Проверьте `frontend/src/lib/config.ts`
2. Убедитесь, что есть проверка `import.meta.env?.PROD`
3. Убедитесь, что `.env.production` содержит `VITE_API_BASE_URL=/api`

### Проблема: Nginx не проксирует запросы

**Решение:**
1. Проверьте `frontend/nginx.conf`
2. Убедитесь, что есть блоки для `/api/`, `/admin/`, `/media/`
3. Проверьте, что `proxy_pass` указывает на `http://backend:8000`

## Обновление патчей

Если нужно обновить патчи (например, изменили `nginx.conf`):

1. Обновите файл в `frontend/`
2. Скопируйте в патчи:
   ```bash
   cp frontend/nginx.conf scripts/deployment-patches/
   ```
3. Закоммитьте изменения:
   ```bash
   git add scripts/deployment-patches/
   git commit -m "[DEPLOY] Update deployment patches"
   ```

