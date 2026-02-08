#!/bin/bash

# Скрипт деплоя на удаленный сервер
# Использование: ./scripts/deploy.sh [server_user@server_host]

set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Параметры (значения по умолчанию для продакшн сервера)
SERVER="${1:-root@72.56.83.95}"
REMOTE_PATH="${2:-/opt/anki_cards}"
SSH_PASSWORD="${SSH_PASSWORD:?SSH_PASSWORD environment variable must be set}"

# Проверка наличия sshpass для автоматического ввода пароля
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}⚠️  sshpass не установлен. Потребуется ввод пароля вручную.${NC}"
    SSH_CMD="ssh"
    SCP_CMD="scp"
else
    SSH_CMD="sshpass -p '${SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no"
    SCP_CMD="sshpass -p '${SSH_PASSWORD}' scp -o StrictHostKeyChecking=no"
fi

echo -e "${BLUE}🚀 Начинаем деплой на сервер: ${SERVER}${NC}"
echo -e "${BLUE}📁 Удаленный путь: ${REMOTE_PATH}${NC}\n"

# Шаг 1: Создание бэкапа (опционально, можно пропустить)
echo -e "${BLUE}📦 Шаг 1: Создание бэкапа данных...${NC}"
if [ -f "./scripts/backup_data.sh" ]; then
    # Пытаемся создать бэкап, но не останавливаемся при ошибке
    ./scripts/backup_data.sh || echo -e "${YELLOW}⚠️  Не удалось создать локальный бэкап (возможно, контейнеры не запущены), продолжаем...${NC}"
    LATEST_BACKUP=$(ls -t backups/*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        echo -e "${GREEN}✅ Бэкап создан: ${LATEST_BACKUP}${NC}"
    else
        echo -e "${YELLOW}⚠️  Бэкап не создан (это нормально, если контейнеры не запущены локально), продолжаем...${NC}"
        echo -e "${BLUE}💡 Бэкап можно создать на сервере после деплоя${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Скрипт backup_data.sh не найден, пропускаем бэкап${NC}"
fi

# Шаг 2: Проверка подключения к серверу
echo -e "\n${BLUE}🔌 Шаг 2: Проверка подключения к серверу...${NC}"
if eval "$SSH_CMD" "$SERVER" "echo 'Connected'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Подключение к серверу установлено${NC}"
else
    echo -e "${RED}❌ Не удалось подключиться к серверу${NC}"
    echo -e "${YELLOW}Попробуйте подключиться вручную:${NC}"
    echo -e "  ssh ${SERVER}"
    echo -e "${YELLOW}Пароль: ${SSH_PASSWORD}${NC}"
    exit 1
fi

# Шаг 3: Создание архива проекта
echo -e "\n${BLUE}📦 Шаг 3: Создание архива проекта...${NC}"
TEMP_DIR=$(mktemp -d)
ARCHIVE_NAME="anki_cards_deploy_$(date +%Y%m%d_%H%M%S).tar.gz"

echo -e "${BLUE}Создаю архив (исключая ненужные файлы)...${NC}"
tar -czf "$TEMP_DIR/$ARCHIVE_NAME" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='backend/.env' \
    --exclude='frontend/.env.production' \
    --exclude='frontend/.env.production.local' \
    --exclude='backend/media' \
    --exclude='backend/staticfiles' \
    --exclude='backups' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='*.log' \
    .

echo -e "${GREEN}✅ Архив создан: ${TEMP_DIR}/${ARCHIVE_NAME}${NC}"

# Шаг 4: Копирование на сервер
echo -e "\n${BLUE}📤 Шаг 4: Копирование архива на сервер...${NC}"
eval "$SCP_CMD" "$TEMP_DIR/$ARCHIVE_NAME" "$SERVER:/tmp/"
echo -e "${GREEN}✅ Архив скопирован на сервер${NC}"

# Шаг 5: Проверка и установка Docker Compose
echo -e "\n${BLUE}🐳 Шаг 5: Проверка Docker Compose...${NC}"
eval "$SSH_CMD" "$SERVER" <<'EOF'
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Устанавливаю Docker Compose..."
    # Установка Docker Compose v2 (плагин для docker)
    mkdir -p ~/.docker/cli-plugins/
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
    chmod +x ~/.docker/cli-plugins/docker-compose
    # Альтернатива: установка через pip
    # pip3 install docker-compose || true
    echo "✅ Docker Compose установлен"
else
    echo "✅ Docker Compose уже установлен"
fi
EOF

# Шаг 6: Остановка старых контейнеров и удаление образов
echo -e "\n${BLUE}🛑 Шаг 6: Остановка старых контейнеров...${NC}"
eval "$SSH_CMD" "$SERVER" <<EOF
set -e
cd ${REMOTE_PATH} || { echo "Директория ${REMOTE_PATH} не существует, создаю..."; mkdir -p ${REMOTE_PATH}; cd ${REMOTE_PATH}; }

if [ -f "docker-compose.yml" ]; then
    echo "Останавливаю старые контейнеры..."
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || docker compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true
fi

echo "Удаляю старые образы..."
docker image prune -f || true
docker system prune -f || true

echo "Удаляю старые образы проекта..."
docker images | grep -E 'anki_cards|anki-cards' | awk '{print \$3}' | xargs -r docker rmi -f || true
EOF

echo -e "${GREEN}✅ Старые контейнеры остановлены, образы удалены${NC}"

# Шаг 7: Распаковка нового кода
echo -e "\n${BLUE}📦 Шаг 7: Распаковка нового кода на сервере...${NC}"
eval "$SSH_CMD" "$SERVER" <<EOF
set -e
cd ${REMOTE_PATH}

# Создаем бэкап старого кода (если есть)
if [ -d ".git" ] || [ -f "docker-compose.yml" ]; then
    echo "Создаю бэкап старого кода..."
    BACKUP_DIR="backup_old_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "../\$BACKUP_DIR"
    [ -f "docker-compose.yml" ] && cp docker-compose.yml "../\$BACKUP_DIR/" || true
    [ -f "docker-compose.prod.yml" ] && cp docker-compose.prod.yml "../\$BACKUP_DIR/" || true
    [ -f ".env" ] && cp .env "../\$BACKUP_DIR/" || true
    [ -d "backend/.env" ] && cp backend/.env "../\$BACKUP_DIR/backend.env" || true
fi

# Распаковываем новый код
echo "Распаковываю новый код..."
tar -xzf "/tmp/${ARCHIVE_NAME}" -C .

echo "Очищаю временный архив..."
rm -f "/tmp/${ARCHIVE_NAME}"
EOF

echo -e "${GREEN}✅ Код распакован${NC}"

# Шаг 8: Настройка переменных окружения
echo -e "\n${BLUE}⚙️  Шаг 8: Проверка переменных окружения...${NC}"
eval "$SSH_CMD" "$SERVER" <<EOF
set -e
cd ${REMOTE_PATH}

# Проверяем наличие .env
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден!"
    echo "Создайте .env файл с необходимыми переменными:"
    echo "  - POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD"
    echo "  - SECRET_KEY, DEBUG, ALLOWED_HOSTS"
    echo "  - OPENAI_API_KEY, GEMINI_API_KEY"
    exit 1
fi

# Проверяем наличие backend/.env
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Файл backend/.env не найден!"
    echo "Создайте backend/.env с:"
    echo "  - SECRET_KEY"
    echo "  - DEBUG=False"
    echo "  - OPENAI_API_KEY"
    exit 1
fi

echo "✅ Файлы .env найдены"
EOF

# Шаг 9: Сборка и запуск контейнеров
echo -e "\n${BLUE}🐳 Шаг 9: Сборка и запуск Docker контейнеров...${NC}"
eval "$SSH_CMD" "$SERVER" <<EOF
set -e
cd ${REMOTE_PATH}

# Определяем команду docker-compose (v1 или v2)
COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

echo "Собираю образы..."
# Пробуем собрать без обращения к Docker Hub (используем локальные образы)
# Если базовые образы уже есть, они будут использованы
if ! \$COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml build --pull=never 2>&1; then
    echo "⚠️  Ошибка при сборке с --pull=never, ждем 2 минуты и пробуем снова..."
    sleep 120
    echo "Повторная попытка сборки..."
    \$COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml build --pull=never || {
        echo "⚠️  Все еще проблемы, пробую обычную сборку..."
        \$COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml build
    }
fi

echo "Запускаю контейнеры..."
\$COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "Жду запуска контейнеров..."
sleep 10

echo "Проверяю статус контейнеров..."
\$COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps
EOF

echo -e "${GREEN}✅ Контейнеры запущены${NC}"

# Шаг 10: Применение миграций
echo -e "\n${BLUE}📊 Шаг 10: Применение миграций базы данных...${NC}"
eval "$SSH_CMD" "$SERVER" <<EOF
set -e
cd ${REMOTE_PATH}

# Определяем команду docker-compose
COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

echo "Применяю миграции..."
\$COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput

echo "Собираю статические файлы..."
\$COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput || true
EOF

echo -e "${GREEN}✅ Миграции применены${NC}"

# Шаг 11: Восстановление данных (если есть бэкап)
if [ -n "$LATEST_BACKUP" ] && [ -f "$LATEST_BACKUP" ]; then
    echo -e "\n${BLUE}📥 Шаг 11: Восстановление данных из бэкапа...${NC}"
    echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Это перезапишет существующие данные!${NC}"
    read -p "Восстановить данные из бэкапа? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        eval "$SCP_CMD" "$LATEST_BACKUP" "$SERVER:/tmp/"
        BACKUP_NAME=$(basename "$LATEST_BACKUP")
        eval "$SSH_CMD" "$SERVER" <<EOF
set -e
cd ${REMOTE_PATH}
if [ -f "./scripts/restore_data.sh" ]; then
    chmod +x ./scripts/restore_data.sh
    ./scripts/restore_data.sh "/tmp/${BACKUP_NAME}"
    rm -f "/tmp/${BACKUP_NAME}"
else
    echo "⚠️  Скрипт restore_data.sh не найден, пропускаем восстановление"
fi
EOF
        echo -e "${GREEN}✅ Данные восстановлены${NC}"
    else
        echo -e "${YELLOW}⏭️  Восстановление данных пропущено${NC}"
    fi
fi

# Шаг 12: Проверка здоровья
echo -e "\n${BLUE}🏥 Шаг 12: Проверка здоровья приложения...${NC}"
eval "$SSH_CMD" "$SERVER" <<EOF
set -e
cd ${REMOTE_PATH}

echo "Проверяю health check..."
sleep 5
curl -f http://localhost:8000/api/health/ || echo "⚠️  Health check не прошел"
EOF

# Очистка
rm -f "$TEMP_DIR/$ARCHIVE_NAME"
rmdir "$TEMP_DIR" 2>/dev/null || true

echo -e "\n${GREEN}✅ Деплой завершен!${NC}"
echo -e "${BLUE}📝 Проверьте логи:${NC}"
echo -e "  ssh ${SERVER} 'cd ${REMOTE_PATH} && docker-compose logs -f'"
echo -e "\n${BLUE}📊 Статус контейнеров:${NC}"
echo -e "  ssh ${SERVER} 'cd ${REMOTE_PATH} && docker-compose ps'"

