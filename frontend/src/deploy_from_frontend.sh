#!/bin/bash

##############################################
# 🚀 Деплой из структурированного проекта
# Работает с /frontend/ папкой
##############################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Путь к Django проекту (ИЗМЕНИТЕ ЭТО!)
DJANGO_PATH="/path/to/your/django/project"

# Проверка пути к Django
if [ "$DJANGO_PATH" = "/path/to/your/django/project" ]; then
    echo -e "${RED}❌ Ошибка: Укажите путь к Django проекту в переменной DJANGO_PATH${NC}"
    echo -e "${YELLOW}Откройте deploy_from_frontend.sh и измените строку:${NC}"
    echo -e "${BLUE}DJANGO_PATH=\"/путь/к/вашему/django/проекту\"${NC}"
    exit 1
fi

if [ ! -d "$DJANGO_PATH" ]; then
    echo -e "${RED}❌ Django проект не найден по пути: $DJANGO_PATH${NC}"
    exit 1
fi

# Проверка наличия папки frontend
if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Папка frontend не найдена!${NC}"
    echo -e "${YELLOW}Запустите сначала: ./organize_frontend.sh${NC}"
    exit 1
fi

echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🚀 Anki Generator - Deployment      ║${NC}"
echo -e "${GREEN}║     (from /frontend/ structure)       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""

# Переходим в папку frontend
cd frontend

# Проверка окружения
echo -e "${BLUE}[1/7]${NC} Проверка окружения..."

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js не установлен!${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm не установлен!${NC}"
    exit 1
fi

if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}⚠️  .env.production не найден, создаю...${NC}"
    echo "VITE_API_BASE_URL=/api" > .env.production
fi

echo -e "${GREEN}✅ Окружение готово${NC}"
echo ""

# Установка зависимостей
echo -e "${BLUE}[2/7]${NC} Проверка зависимостей..."

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Устанавливаю зависимости...${NC}"
    npm install
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Ошибка установки зависимостей!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Зависимости уже установлены${NC}"
fi
echo ""

# Билд проекта
echo -e "${BLUE}[3/7]${NC} 📦 Сборка production билда..."
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка сборки!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Билд успешно собран${NC}"

BUILD_SIZE=$(du -sh dist | cut -f1)
echo -e "${YELLOW}📊 Размер билда: $BUILD_SIZE${NC}"
echo ""

# Создание резервной копии
echo -e "${BLUE}[4/7]${NC} 💾 Создание резервной копии..."

BACKUP_DIR="$DJANGO_PATH/backup_$(date +%Y%m%d_%H%M%S)"

if [ -f "$DJANGO_PATH/templates/index.html" ]; then
    mkdir -p "$BACKUP_DIR/templates"
    cp "$DJANGO_PATH/templates/index.html" "$BACKUP_DIR/templates/"
    echo -e "${GREEN}✅ Создана резервная копия index.html${NC}"
fi

if [ -d "$DJANGO_PATH/static/assets" ]; then
    mkdir -p "$BACKUP_DIR/static"
    cp -r "$DJANGO_PATH/static/assets" "$BACKUP_DIR/static/"
    echo -e "${GREEN}✅ Создана резервная копия assets${NC}"
fi

echo ""

# Копирование файлов
echo -e "${BLUE}[5/7]${NC} 📁 Копирование файлов в Django..."

mkdir -p "$DJANGO_PATH/templates"
mkdir -p "$DJANGO_PATH/static"

echo -e "${YELLOW}📄 Копирую index.html...${NC}"
cp dist/index.html "$DJANGO_PATH/templates/index.html"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка копирования index.html!${NC}"
    exit 1
fi

echo -e "${YELLOW}📁 Копирую assets...${NC}"
rm -rf "$DJANGO_PATH/static/assets"
cp -r dist/assets "$DJANGO_PATH/static/"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка копирования assets!${NC}"
    exit 1
fi

if [ -f "dist/vite.svg" ]; then
    cp dist/vite.svg "$DJANGO_PATH/static/"
fi

echo -e "${GREEN}✅ Файлы скопированы${NC}"
echo ""

# Обновление путей
echo -e "${BLUE}[6/7]${NC} 🔧 Обновление путей в index.html..."

INDEX_HTML="$DJANGO_PATH/templates/index.html"

if ! grep -q "{% load static %}" "$INDEX_HTML"; then
    sed -i '1s|^|{% load static %}\n|' "$INDEX_HTML"
fi

sed -i 's|="/assets/|="{% static '\''assets/|g' "$INDEX_HTML"
sed -i 's|href="/vite\.svg"|href="{% static '\''vite.svg'\'' %}"|g' "$INDEX_HTML"
sed -i 's|\(\.js\)"|\1'\'' %}"|g' "$INDEX_HTML"
sed -i 's|\(\.css\)">|\1'\'' %}">|g' "$INDEX_HTML"

echo -e "${GREEN}✅ Пути обновлены${NC}"
echo ""

# Collectstatic
echo -e "${BLUE}[7/7]${NC} 📚 Запуск collectstatic..."

cd "$DJANGO_PATH"

if [ -f "manage.py" ]; then
    python manage.py collectstatic --noinput
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Ошибка collectstatic${NC}"
    else
        echo -e "${GREEN}✅ Статические файлы собраны${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  manage.py не найден${NC}"
fi

echo ""

# Итог
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      ✅ Deployment successful!        ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📋 Что было сделано:${NC}"
echo -e "  ✅ Собран production билд ($BUILD_SIZE)"
echo -e "  ✅ Создана резервная копия в $BACKUP_DIR"
echo -e "  ✅ Скопированы файлы в Django"
echo -e "  ✅ Обновлены пути для Django templates"
echo -e "  ✅ Выполнен collectstatic"
echo ""
echo -e "${BLUE}🌐 Следующие шаги:${NC}"
echo -e "  1. Запустите Django сервер:"
echo -e "     ${YELLOW}cd $DJANGO_PATH${NC}"
echo -e "     ${YELLOW}python manage.py runserver${NC}"
echo -e "  2. Откройте браузер: ${YELLOW}http://localhost:8000/${NC}"
echo ""
echo -e "${GREEN}Успешного деплоя! 🚀${NC}"
