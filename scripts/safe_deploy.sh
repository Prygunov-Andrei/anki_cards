#!/bin/bash
# Безопасный скрипт деплоя с проверками и ограничениями

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SERVER_IP="72.56.83.95"
SERVER_USER="root"
SERVER_PASS="hN9DVVo_pu6d_X"
DEPLOY_DIR="/opt/anki_cards"

echo -e "${BLUE}🔒 Безопасный деплой на сервер ${SERVER_IP}...${NC}\n"

# Функция для безопасного выполнения команд
safe_remote_exec() {
    local cmd="$1"
    local description="$2"
    
    echo -e "${BLUE}${description}...${NC}"
    if sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 "$SERVER_USER@$SERVER_IP" "$cmd"; then
        echo -e "${GREEN}✅ Успешно${NC}\n"
        return 0
    else
        echo -e "${RED}❌ Ошибка${NC}\n"
        return 1
    fi
}

# 1. Проверка подключения
echo -e "${BLUE}1️⃣  Проверка подключения к серверу...${NC}"
if ! ping -c 2 "$SERVER_IP" > /dev/null 2>&1; then
    echo -e "${RED}❌ Сервер недоступен${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Сервер доступен${NC}\n"

# 2. Остановка существующих контейнеров (осторожно)
echo -e "${BLUE}2️⃣  Остановка существующих контейнеров...${NC}"
safe_remote_exec "cd $DEPLOY_DIR && docker compose down" "Остановка контейнеров"

# 3. Проверка использования ресурсов перед деплоем
echo -e "${BLUE}3️⃣  Проверка ресурсов сервера...${NC}"
safe_remote_exec "top -bn1 | head -5 && free -h" "Проверка ресурсов"

# 4. Сборка backend (пошагово)
echo -e "${BLUE}4️⃣  Сборка backend...${NC}"
safe_remote_exec "cd $DEPLOY_DIR && docker compose build backend" "Сборка backend"

# 5. Сборка frontend (пошагово)
echo -e "${BLUE}5️⃣  Сборка frontend...${NC}"
safe_remote_exec "cd $DEPLOY_DIR && docker compose build frontend" "Сборка frontend"

# 6. Запуск базы данных
echo -e "${BLUE}6️⃣  Запуск базы данных...${NC}"
safe_remote_exec "cd $DEPLOY_DIR && docker compose up -d db" "Запуск БД"

# 7. Ожидание готовности БД
echo -e "${BLUE}7️⃣  Ожидание готовности базы данных...${NC}"
sleep 10
safe_remote_exec "cd $DEPLOY_DIR && docker compose ps db" "Проверка БД"

# 8. Запуск backend
echo -e "${BLUE}8️⃣  Запуск backend...${NC}"
safe_remote_exec "cd $DEPLOY_DIR && docker compose up -d backend" "Запуск backend"

# 9. Проверка логов backend
echo -e "${BLUE}9️⃣  Проверка логов backend...${NC}"
safe_remote_exec "cd $DEPLOY_DIR && docker compose logs backend --tail 20" "Логи backend"

# 10. Запуск frontend
echo -e "${BLUE}🔟 Запуск frontend...${NC}"
safe_remote_exec "cd $DEPLOY_DIR && docker compose up -d frontend" "Запуск frontend"

# 11. Финальная проверка
echo -e "${BLUE}1️⃣1️⃣  Финальная проверка...${NC}"
safe_remote_exec "cd $DEPLOY_DIR && docker compose ps" "Статус контейнеров"
safe_remote_exec "docker stats --no-stream" "Использование ресурсов"

echo -e "\n${GREEN}✅ Деплой завершен успешно!${NC}\n"
echo -e "${BLUE}📝 Приложение доступно по адресу:${NC}"
echo -e "${GREEN}   http://${SERVER_IP}${NC}\n"

