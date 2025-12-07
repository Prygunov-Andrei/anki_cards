#!/bin/bash

# Скрипт для создания бэкапа данных перед деплоем
# Использование: ./scripts/backup_data.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="anki_backup_${TIMESTAMP}"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

echo -e "${BLUE}📦 Создание бэкапа данных...${NC}"
echo ""

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

# Проверка наличия manage.py
if [ ! -f "$BACKEND_DIR/manage.py" ]; then
    echo -e "${RED}❌ Ошибка: manage.py не найден в $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

# Проверка виртуального окружения и определение команды Python
if [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
elif [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_CMD="python"
else
    # Пробуем python3, если виртуальное окружение не найдено
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ Ошибка: Python не найден${NC}"
        exit 1
    fi
    echo -e "${YELLOW}⚠️  Виртуальное окружение не активировано, используется: $PYTHON_CMD${NC}"
fi

# Создание временной директории для бэкапа
mkdir -p "$BACKUP_PATH"

echo -e "${BLUE}📊 Экспорт данных из базы данных...${NC}"

# Экспорт данных (исключаем системные таблицы)
$PYTHON_CMD manage.py dumpdata \
    --exclude auth.permission \
    --exclude contenttypes \
    --exclude admin.logentry \
    --exclude sessions.session \
    --indent 2 \
    > "$BACKUP_PATH/data.json" 2>&1

if [ $? -eq 0 ]; then
    DATA_SIZE=$(du -h "$BACKUP_PATH/data.json" | cut -f1)
    echo -e "${GREEN}✅ Данные экспортированы (размер: $DATA_SIZE)${NC}"
else
    echo -e "${RED}❌ Ошибка при экспорте данных${NC}"
    exit 1
fi

# Копирование медиафайлов
echo ""
echo -e "${BLUE}📁 Копирование медиафайлов...${NC}"

if [ -d "media" ] && [ "$(ls -A media 2>/dev/null)" ]; then
    cp -r media "$BACKUP_PATH/"
    MEDIA_SIZE=$(du -sh "$BACKUP_PATH/media" | cut -f1)
    echo -e "${GREEN}✅ Медиафайлы скопированы (размер: $MEDIA_SIZE)${NC}"
else
    echo -e "${YELLOW}⚠️  Папка media пуста или не существует${NC}"
    mkdir -p "$BACKUP_PATH/media"
fi

# Создание файла с информацией о бэкапе
cat > "$BACKUP_PATH/backup_info.txt" << EOF
Backup created: $(date '+%Y-%m-%d %H:%M:%S')
Backup name: $BACKUP_NAME
Database: $(grep -o '"ENGINE": "[^"]*"' "$BACKUP_PATH/data.json" | head -1 || echo "Unknown")
Data file size: $(du -h "$BACKUP_PATH/data.json" | cut -f1)
Media size: $(du -sh "$BACKUP_PATH/media" 2>/dev/null | cut -f1 || echo "0")
EOF

# Создание архива
echo ""
echo -e "${BLUE}🗜️  Создание архива...${NC}"

cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

if [ $? -eq 0 ]; then
    ARCHIVE_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    echo -e "${GREEN}✅ Архив создан: ${BACKUP_NAME}.tar.gz (размер: $ARCHIVE_SIZE)${NC}"
    
    # Удаление временной директории
    rm -rf "$BACKUP_NAME"
    
    echo ""
    echo -e "${GREEN}✨ Бэкап успешно создан!${NC}"
    echo ""
    echo -e "${BLUE}📋 Информация о бэкапе:${NC}"
    cat "$BACKUP_PATH/backup_info.txt" 2>/dev/null || echo "Информация недоступна"
    echo ""
    echo -e "${BLUE}📦 Файл бэкапа:${NC}"
    echo -e "${GREEN}   $BACKUP_DIR/${BACKUP_NAME}.tar.gz${NC}"
    echo ""
    echo -e "${YELLOW}💡 Для восстановления используйте:${NC}"
    echo -e "${BLUE}   ./scripts/restore_data.sh $BACKUP_DIR/${BACKUP_NAME}.tar.gz${NC}"
else
    echo -e "${RED}❌ Ошибка при создании архива${NC}"
    exit 1
fi

