#!/bin/bash

# Скрипт для настройки переменных окружения на сервере
# Использование: ./scripts/setup_server_env.sh

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SERVER="${1:-root@72.56.83.95}"
REMOTE_PATH="/opt/anki_cards"

echo -e "${BLUE}⚙️  Настройка переменных окружения на сервере...${NC}\n"

# Генерация SECRET_KEY
echo -e "${BLUE}🔑 Генерация SECRET_KEY...${NC}"
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -hex 32)
echo -e "${GREEN}✅ SECRET_KEY сгенерирован${NC}"

# Генерация пароля для БД
echo -e "${BLUE}🔑 Генерация пароля для БД...${NC}"
DB_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-32)
echo -e "${GREEN}✅ Пароль БД сгенерирован${NC}"

# Запрос API ключей
echo -e "\n${YELLOW}📝 Введите API ключи:${NC}"
read -p "OPENAI_API_KEY: " OPENAI_KEY
read -p "GEMINI_API_KEY (опционально, нажмите Enter чтобы пропустить): " GEMINI_KEY

# Создание .env файла
echo -e "\n${BLUE}📄 Создание .env файла...${NC}"
cat > /tmp/.env.production <<EOF
# Production Environment Variables
# Generated on $(date)

# Database
POSTGRES_DB=anki_db
POSTGRES_USER=anki_user
POSTGRES_PASSWORD=${DB_PASSWORD}

# Django
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=72.56.83.95,get-anki.fan.ngrok.app

# OpenAI
OPENAI_API_KEY=${OPENAI_KEY}

# Google Gemini (опционально)
GEMINI_API_KEY=${GEMINI_KEY:-}
EOF

# Создание backend/.env файла
echo -e "${BLUE}📄 Создание backend/.env файла...${NC}"
cat > /tmp/backend.env.production <<EOF
# Backend Production Environment Variables
# Generated on $(date)

SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=72.56.83.95,get-anki.fan.ngrok.app

# OpenAI
OPENAI_API_KEY=${OPENAI_KEY}

# Google Gemini (опционально)
GEMINI_API_KEY=${GEMINI_KEY:-}
EOF

echo -e "${GREEN}✅ Файлы .env созданы локально${NC}"

# Копирование на сервер
echo -e "\n${BLUE}📤 Копирование .env файлов на сервер...${NC}"
echo -e "${YELLOW}⚠️  Введите пароль для root@72.56.83.95 (из переменной SSH_PASSWORD)${NC}"

# Создаем директорию на сервере
ssh -o StrictHostKeyChecking=no "$SERVER" "mkdir -p ${REMOTE_PATH}/backend" || {
    echo -e "${RED}❌ Не удалось подключиться к серверу${NC}"
    echo -e "${YELLOW}Попробуйте подключиться вручную:${NC}"
    echo -e "  ssh root@72.56.83.95"
    exit 1
}

# Копируем файлы
scp /tmp/.env.production "$SERVER:${REMOTE_PATH}/.env"
scp /tmp/backend.env.production "$SERVER:${REMOTE_PATH}/backend/.env"

# Очистка
rm -f /tmp/.env.production /tmp/backend.env.production

echo -e "\n${GREEN}✅ Переменные окружения настроены на сервере!${NC}"
echo -e "${BLUE}📝 Файлы созданы:${NC}"
echo -e "  - ${REMOTE_PATH}/.env"
echo -e "  - ${REMOTE_PATH}/backend/.env"
echo -e "\n${YELLOW}⚠️  ВАЖНО: Сохраните эти значения в безопасном месте!${NC}"
echo -e "${BLUE}SECRET_KEY: ${SECRET_KEY}${NC}"
echo -e "${BLUE}DB_PASSWORD: ${DB_PASSWORD}${NC}"

