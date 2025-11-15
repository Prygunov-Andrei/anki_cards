## План деплоя контейнеризированного приложения

### 1. Инфраструктура и доступ
- **ОС:** Ubuntu 24.04 LTS (сервер арендован).
- **IPv4:** 194.87.200.188.
- **IPv6:** 2a03:6f02::1:b8a.
- **SSH-доступ:** `ssh root@194.87.200.188`.
- **Пароль root:** `qwnZY,nX43mSeA`.
- **Закрытые порты провайдера:** 25, 3389, 2525, 465, 53413, 389, 587 — учесть при настройке сервисов и мониторинга.

### 2. Цели контейнеризации
- Унифицировать окружение backend (Django) и frontend (React/Vite/CRA) через Docker.
- Обеспечить воспроизводимую сборку: образы backend, frontend, nginx (reverse proxy), база данных (при необходимости).
- Изолировать зависимости и минимизировать ручные действия на сервере.

### 3. Предварительная подготовка сервера
1. **SSH-подключение:** зайти как root.
2. **Обновления:** `apt update && apt upgrade -y`.
3. **Часовой пояс и локаль:** `timedatectl`, `locale`.
4. **Создание пользователя деплоя (опционально):**
   - `adduser deploy && usermod -aG sudo deploy`.
   - Настроить SSH-ключи, отключить парольный вход для root после успешного деплоя.
5. **Базовая защита:**
   - Установить `ufw`, открыть нужные порты (например, 22, 80, 443; остальные закрыть, с учётом уже заблокированных провайдером).
   - Включить `fail2ban`.

### 4. Установка Docker-окружения
1. Удалить старые версии: `apt remove docker docker-engine docker.io containerd runc`.
2. Установить зависимости: `apt install ca-certificates curl gnupg`.
3. Добавить репозиторий Docker: 
   - `install -m 0755 -d /etc/apt/keyrings`
   - `curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg`
   - `echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list`
4. Установить Docker Engine + Compose: `apt update && apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y`.
5. (Опционально) Добавить пользователя деплоя в группу `docker`.

### 5. Подготовка проекта к контейнеризации
1. Создать Dockerfile для backend (Python/Django) с использованием `python:3.11-slim` (пример): установка зависимостей, копирование кода, миграции, запуск через `gunicorn`.
2. Создать Dockerfile для frontend (Node 18 LTS): сборка статических файлов, отдача через nginx или тот же контейнер nginx.
3. Создать общий `docker-compose.yml`, включающий:
   - `backend` (Django + gunicorn).
   - `frontend` (статические файлы nginx) или сборочный контейнер + nginx.
   - `db` (PostgreSQL или текущая БД, если планируется миграция с sqlite).
   - `reverse-proxy` (nginx/traefik) с SSL-терминацией.
4. Перед деплоем подготовить `.env` файлы и скрипты миграций.

### 6. План деплоя на сервер
1. **Передача репозитория:**
   - Использовать `git clone` на сервере или `scp` архивов.
   - Хранить `.env` только на сервере.
2. **Конфигурация переменных окружения:**
   - Создать `backend/.env` (секреты Django, токены, ключи БД).
   - Создать `frontend/.env` при необходимости.
   - Настроить переменные nginx (`SERVER_NAME`, пути к сертификатам).
3. **Сборка и запуск контейнеров:**
   - `docker compose build`.
   - `docker compose up -d`.
4. **Миграции и статика:**
   - `docker compose exec backend python manage.py migrate`.
   - `docker compose exec backend python manage.py collectstatic --noinput` (если используется).
5. **Настройка HTTPS:**
   - Получить сертификаты через `certbot` (контейнер или отдельная установка).
   - Добавить автоматическое обновление сертификатов.
6. **Проверки после запуска:**
   - Убедиться, что сервисы слушают открытые порты (80/443).
   - Проверить логи: `docker compose logs -f backend`, `frontend`, `nginx`.
   - Прогнать smoke-тесты API и UI.
7. **Мониторинг и резервное копирование:**
   - Настроить системные метрики (Netdata/Prometheus).
   - Регулярные бэкапы БД (cron + `pg_dump` или snapshot).

### 7. Дальнейшие шаги
- Автоматизировать деплой (GitHub Actions + SSH/Docker context).
- Перевести root-вход на ключи и закрыть парольный доступ.
- Документировать процессы обновления и отката.

Документ необходимо обновлять по мере уточнения архитектуры контейнеров и CI/CD.

