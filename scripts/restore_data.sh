#!/bin/bash

# Скрипт для восстановления данных из бэкапа на сервере
# Использование: ./scripts/restore_data.sh <путь_к_архиву.tar.gz>

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Проверка аргументов
if [ -z "$1" ]; then
    echo -e "${RED}❌ Ошибка: не указан путь к архиву бэкапа${NC}"
    echo ""
    echo -e "${YELLOW}Использование:${NC}"
    echo -e "${BLUE}  ./scripts/restore_data.sh <путь_к_архиву.tar.gz>${NC}"
    echo ""
    echo -e "${YELLOW}Пример:${NC}"
    echo -e "${BLUE}  ./scripts/restore_data.sh backups/anki_backup_20241207_120000.tar.gz${NC}"
    exit 1
fi

BACKUP_ARCHIVE="$1"

# Проверка существования архива
if [ ! -f "$BACKUP_ARCHIVE" ]; then
    echo -e "${RED}❌ Ошибка: файл бэкапа не найден: $BACKUP_ARCHIVE${NC}"
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMP_DIR="/tmp/anki_restore_$$"

echo -e "${BLUE}📦 Восстановление данных из бэкапа...${NC}"
echo -e "${BLUE}   Архив: $BACKUP_ARCHIVE${NC}"
echo ""

# Проверка, запущен ли Docker Compose
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Docker Compose контейнеры не запущены${NC}"
    echo -e "${YELLOW}   Запускаю контейнеры...${NC}"
    docker-compose up -d
    sleep 5
fi

# Распаковка архива
echo -e "${BLUE}📂 Распаковка архива...${NC}"
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_ARCHIVE" -C "$TEMP_DIR"

# Определяем имя папки внутри архива (может быть разным)
BACKUP_DIR=$(find "$TEMP_DIR" -name "data.json" -type f | head -1 | xargs dirname)
if [ -z "$BACKUP_DIR" ]; then
    # Пробуем найти по паттерну data_*
    BACKUP_DIR=$(find "$TEMP_DIR" -type d -name "data_*" | head -1)
fi

if [ -z "$BACKUP_DIR" ] || [ ! -f "$BACKUP_DIR/data.json" ]; then
    echo -e "${RED}❌ Ошибка: файл data.json не найден в архиве${NC}"
    echo -e "${YELLOW}   Содержимое архива:${NC}"
    ls -la "$TEMP_DIR"
    rm -rf "$TEMP_DIR"
    exit 1
fi

BACKUP_NAME=$(basename "$BACKUP_DIR")
echo -e "${GREEN}✅ Найден бэкап в папке: $BACKUP_NAME${NC}"

echo -e "${GREEN}✅ Архив распакован${NC}"
echo ""

# Показываем информацию о бэкапе
if [ -f "$TEMP_DIR/$BACKUP_NAME/backup_info.txt" ]; then
    echo -e "${BLUE}📋 Информация о бэкапе:${NC}"
    cat "$TEMP_DIR/$BACKUP_NAME/backup_info.txt"
    echo ""
fi

# Подтверждение
echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Это действие перезапишет существующие данные!${NC}"
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}❌ Восстановление отменено${NC}"
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Применение миграций (на всякий случай)
echo ""
echo -e "${BLUE}🔄 Применение миграций...${NC}"
docker-compose exec -T backend python manage.py migrate --noinput

# Импорт данных
echo ""
echo -e "${BLUE}📥 Импорт данных в базу данных...${NC}"

# Копируем data.json в контейнер
docker cp "$TEMP_DIR/$BACKUP_NAME/data.json" "$(docker-compose ps -q backend):/tmp/data.json"

# Импортируем данные
docker-compose exec -T backend python manage.py loaddata /tmp/data.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Данные успешно импортированы${NC}"
else
    echo -e "${RED}❌ Ошибка при импорте данных${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Копирование медиафайлов
echo ""
echo -e "${BLUE}📁 Копирование медиафайлов...${NC}"

if [ -d "$TEMP_DIR/$BACKUP_NAME/media" ] && [ "$(ls -A $TEMP_DIR/$BACKUP_NAME/media 2>/dev/null)" ]; then
    # Копируем медиафайлы в контейнер
    docker cp "$TEMP_DIR/$BACKUP_NAME/media/." "$(docker-compose ps -q backend):/app/media/"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Медиафайлы успешно скопированы${NC}"
    else
        echo -e "${YELLOW}⚠️  Предупреждение: ошибка при копировании медиафайлов${NC}"
        echo -e "${YELLOW}   Попробуйте скопировать вручную:${NC}"
        echo -e "${BLUE}   docker cp $TEMP_DIR/$BACKUP_NAME/media/. <container_id>:/app/media/${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Медиафайлы не найдены в бэкапе${NC}"
fi

# Очистка
rm -rf "$TEMP_DIR"

# Сборка статики (на всякий случай)
echo ""
echo -e "${BLUE}🎨 Сборка статических файлов...${NC}"
docker-compose exec -T backend python manage.py collectstatic --noinput

echo ""
echo -e "${GREEN}✨ Восстановление данных завершено!${NC}"
echo ""
echo -e "${BLUE}📋 Следующие шаги:${NC}"
echo -e "${GREEN}   1. Проверьте данные в админке: http://localhost/admin/${NC}"
echo -e "${GREEN}   2. Проверьте медиафайлы${NC}"
echo -e "${GREEN}   3. Проверьте работу приложения${NC}"

