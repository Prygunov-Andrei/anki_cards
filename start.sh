#!/bin/bash

# Скрипт запуска Anki Card Generator (Backend Only)
# Запускает backend (Django)

set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Запуск Anki Card Generator (Backend)...${NC}\n"

# Проверяем, что мы в корне проекта
if [ ! -d "backend" ]; then
    echo -e "${YELLOW}❌ Ошибка: скрипт должен запускаться из корня проекта${NC}"
    exit 1
fi

# Функция для очистки при выходе
cleanup() {
    echo -e "\n${YELLOW}🛑 Остановка сервера...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Проверяем виртуальное окружение backend
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено. Создаю...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
fi

# Применяем миграции
echo -e "${BLUE}📦 Проверка миграций...${NC}"
cd backend
source venv/bin/activate
python manage.py migrate --noinput
cd ..

# Запускаем backend
echo -e "${GREEN}🔧 Запуск backend (Django) на http://localhost:8000${NC}"
cd backend
source venv/bin/activate
python manage.py runserver > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo -e "\n${GREEN}✅ Сервер запущен!${NC}\n"
echo -e "${BLUE}📝 API:      http://localhost:8000/api/${NC}"
echo -e "${BLUE}📝 Admin:    http://localhost:8000/admin/${NC}\n"
echo -e "${YELLOW}💡 Логи backend:  tail -f backend.log${NC}\n"
echo -e "${YELLOW}Нажмите Ctrl+C для остановки${NC}\n"

# Ждем завершения процесса
wait
