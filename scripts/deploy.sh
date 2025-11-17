#!/bin/bash

# Скрипт деплоя на сервер
# Использование: ./deploy.sh

set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Параметры сервера
SERVER_IP="72.56.83.95"
SERVER_USER="root"
SERVER_PASS="hN9DVVo_pu6d_X"
DEPLOY_DIR="/opt/anki_cards"

echo -e "${BLUE}🚀 Начало деплоя на сервер ${SERVER_IP}...${NC}\n"

# Проверка наличия SSH
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}⚠️  sshpass не установлен. Устанавливаю...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass || echo -e "${RED}❌ Не удалось установить sshpass. Установите вручную: brew install hudochenkov/sshpass/sshpass${NC}"
    else
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
fi

# Функция для выполнения команд на сервере
run_remote() {
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$1"
}

# Функция для копирования файлов на сервер
copy_to_server() {
    sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no -r "$1" "$SERVER_USER@$SERVER_IP:$2"
}

echo -e "${BLUE}📦 Подготовка к деплою...${NC}"

# 1. Проверка и установка Docker на сервере
echo -e "${BLUE}1️⃣  Проверка Docker на сервере...${NC}"
if ! run_remote "command -v docker &> /dev/null"; then
    echo -e "${YELLOW}⚠️  Docker не установлен. Устанавливаю...${NC}"
    run_remote "apt update && apt install -y ca-certificates curl gnupg"
    run_remote "install -m 0755 -d /etc/apt/keyrings"
    run_remote "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg"
    run_remote 'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list'
    run_remote "apt update && apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
else
    echo -e "${GREEN}✅ Docker уже установлен${NC}"
fi

# 2. Создание директории для деплоя
echo -e "${BLUE}2️⃣  Создание директории для деплоя...${NC}"
run_remote "mkdir -p $DEPLOY_DIR"

# 3. Копирование проекта на сервер
echo -e "${BLUE}3️⃣  Копирование проекта на сервер...${NC}"
# Создание временного архива
TEMP_ARCHIVE=$(mktemp -t anki_cards_XXXXXX.tar.gz)
tar --exclude='.git' \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='*.log' \
    --exclude='db.sqlite3' \
    --exclude='media' \
    --exclude='staticfiles' \
    --exclude='build' \
    -czf "$TEMP_ARCHIVE" .

copy_to_server "$TEMP_ARCHIVE" "$DEPLOY_DIR/"
rm "$TEMP_ARCHIVE"

# Распаковка на сервере
run_remote "cd $DEPLOY_DIR && tar -xzf $(basename $TEMP_ARCHIVE) && rm $(basename $TEMP_ARCHIVE)"

# 4. Создание .env файла на сервере (если не существует)
echo -e "${BLUE}4️⃣  Настройка переменных окружения...${NC}"
if ! run_remote "test -f $DEPLOY_DIR/.env"; then
    echo -e "${YELLOW}⚠️  Файл .env не найден. Создаю из примера...${NC}"
    run_remote "cd $DEPLOY_DIR && cp .env.example .env"
    echo -e "${RED}⚠️  ВАЖНО: Отредактируйте файл .env на сервере перед запуском!${NC}"
    echo -e "${YELLOW}   ssh $SERVER_USER@$SERVER_IP${NC}"
    echo -e "${YELLOW}   nano $DEPLOY_DIR/.env${NC}"
else
    echo -e "${GREEN}✅ Файл .env уже существует${NC}"
fi

# 5. Сборка и запуск контейнеров
echo -e "${BLUE}5️⃣  Сборка и запуск контейнеров...${NC}"
run_remote "cd $DEPLOY_DIR && docker compose down || true"
run_remote "cd $DEPLOY_DIR && docker compose build"
run_remote "cd $DEPLOY_DIR && docker compose up -d"

# 6. Ожидание запуска сервисов
echo -e "${BLUE}6️⃣  Ожидание запуска сервисов...${NC}"
sleep 10

# 7. Применение миграций
echo -e "${BLUE}7️⃣  Применение миграций...${NC}"
run_remote "cd $DEPLOY_DIR && docker compose exec -T backend python manage.py migrate --noinput"

# 8. Сборка статики
echo -e "${BLUE}8️⃣  Сборка статических файлов...${NC}"
run_remote "cd $DEPLOY_DIR && docker compose exec -T backend python manage.py collectstatic --noinput"

# 9. Проверка статуса
echo -e "${BLUE}9️⃣  Проверка статуса контейнеров...${NC}"
run_remote "cd $DEPLOY_DIR && docker compose ps"

echo -e "\n${GREEN}✅ Деплой завершен!${NC}\n"
echo -e "${BLUE}📝 Проверьте логи:${NC}"
echo -e "${YELLOW}   docker compose -f $DEPLOY_DIR/docker-compose.yml logs -f${NC}\n"
echo -e "${BLUE}📝 Приложение должно быть доступно по адресу:${NC}"
echo -e "${GREEN}   http://${SERVER_IP}${NC}\n"
echo -e "${YELLOW}⚠️  Не забудьте:${NC}"
echo -e "${YELLOW}   1. Настроить SSL сертификаты (certbot)${NC}"
echo -e "${YELLOW}   2. Проверить файл .env на сервере${NC}"
echo -e "${YELLOW}   3. Создать суперпользователя: docker compose -f $DEPLOY_DIR/docker-compose.yml exec backend python manage.py createsuperuser${NC}\n"

