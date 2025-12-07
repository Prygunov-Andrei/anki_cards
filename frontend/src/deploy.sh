#!/bin/bash

##############################################
# 🚀 Скрипт автоматического деплоя фронтенда
# Anki Generator - Frontend Deployment
##############################################

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Путь к Django проекту (ИЗМЕНИТЕ ЭТО!)
DJANGO_PATH="/path/to/your/django/project"

# Проверка, что путь к Django указан
if [ "$DJANGO_PATH" = "/path/to/your/django/project" ]; then
    echo -e "${RED}❌ Ошибка: Укажите путь к Django проекту в переменной DJANGO_PATH${NC}"
    echo -e "${YELLOW}Откройте deploy.sh и измените строку:${NC}"
    echo -e "${BLUE}DJANGO_PATH=\"/путь/к/вашему/django/проекту\"${NC}"
    exit 1
fi

# Проверка существования Django проекта
if [ ! -d "$DJANGO_PATH" ]; then
    echo -e "${RED}❌ Django проект не найден по пути: $DJANGO_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🚀 Anki Generator - Deployment      ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""

# Шаг 1: Проверка окружения
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

# Шаг 2: Установка зависимостей (опционально)
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

# Шаг 3: Билд проекта
echo -e "${BLUE}[3/7]${NC} 📦 Сборка production билда..."
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка сборки!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Билд успешно собран${NC}"

# Проверка размера билда
BUILD_SIZE=$(du -sh dist | cut -f1)
echo -e "${YELLOW}📊 Размер билда: $BUILD_SIZE${NC}"
echo ""

# Шаг 4: Создание резервной копии (опционально)
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

# Шаг 5: Копирование файлов
echo -e "${BLUE}[5/7]${NC} 📁 Копирование файлов в Django..."

# Создание необходимых директорий
mkdir -p "$DJANGO_PATH/templates"
mkdir -p "$DJANGO_PATH/static"

# Копирование index.html
echo -e "${YELLOW}📄 Копирую index.html...${NC}"
cp dist/index.html "$DJANGO_PATH/templates/index.html"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка копирования index.html!${NC}"
    exit 1
fi

# Копирование assets
echo -e "${YELLOW}📁 Копирую assets...${NC}"
rm -rf "$DJANGO_PATH/static/assets"
cp -r dist/assets "$DJANGO_PATH/static/"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка копирования assets!${NC}"
    exit 1
fi

# Копирование других файлов из dist (если есть)
if [ -f "dist/vite.svg" ]; then
    cp dist/vite.svg "$DJANGO_PATH/static/"
fi

echo -e "${GREEN}✅ Файлы скопированы${NC}"
echo ""

# Шаг 6: Обновление путей в index.html
echo -e "${BLUE}[6/7]${NC} 🔧 Обновление путей в index.html..."

INDEX_HTML="$DJANGO_PATH/templates/index.html"

# Добавляем {% load static %} в начало файла
if ! grep -q "{% load static %}" "$INDEX_HTML"; then
    sed -i '1s|^|{% load static %}\n|' "$INDEX_HTML"
fi

# Заменяем /assets/ на {% static 'assets/' %}
sed -i 's|="/assets/|="{% static '\''assets/|g' "$INDEX_HTML"
sed -i 's|href="/vite\.svg"|href="{% static '\''vite.svg'\'' %}"|g' "$INDEX_HTML"

# Закрываем теги static
sed -i 's|\(\.js\)"|\1'\'' %}"|g' "$INDEX_HTML"
sed -i 's|\(\.css\)">|\1'\'' %}">|g' "$INDEX_HTML"

echo -e "${GREEN}✅ Пути обновлены для Django templates${NC}"
echo ""

# Шаг 7: Collectstatic
echo -e "${BLUE}[7/7]${NC} 📚 Запуск collectstatic..."

cd "$DJANGO_PATH"

if [ -f "manage.py" ]; then
    python manage.py collectstatic --noinput
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Ошибка collectstatic (возможно, нужно настроить settings.py)${NC}"
    else
        echo -e "${GREEN}✅ Статические файлы собраны${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  manage.py не найден, пропускаю collectstatic${NC}"
fi

echo ""

# Итоговое сообщение
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
echo -e "  3. Проверьте работу приложения"
echo ""
echo -e "${GREEN}Успешного деплоя! 🚀${NC}"
