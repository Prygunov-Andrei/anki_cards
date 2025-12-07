#!/bin/bash

# Скрипт синхронизации фронтенда из репозитория Figma Make
# Использование: ./scripts/sync_frontend.sh [--auto-commit] [--review]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
FIGMA_REPO_URL="https://github.com/Prygunov-Andrei/Ankiflashcardgenerator.git"
TEMP_DIR="/tmp/figma-frontend-sync"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Параметры
AUTO_COMMIT=false
REVIEW_MODE=false

# Парсинг аргументов
for arg in "$@"; do
    case $arg in
        --auto-commit)
            AUTO_COMMIT=true
            shift
            ;;
        --review)
            REVIEW_MODE=true
            shift
            ;;
        *)
            echo -e "${YELLOW}Неизвестный параметр: $arg${NC}"
            ;;
    esac
done

echo -e "${BLUE}🔄 Синхронизация фронтенда из Figma Make...${NC}"
echo ""

# Проверка наличия git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git не установлен!${NC}"
    exit 1
fi

# Создание временной директории
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Клонирование или обновление репозитория
if [ -d "figma-repo" ]; then
    echo -e "${BLUE}📥 Обновление существующего репозитория...${NC}"
    cd figma-repo
    git fetch origin
    git reset --hard origin/main
    cd ..
else
    echo -e "${BLUE}📥 Клонирование репозитория Figma Make...${NC}"
    git clone "$FIGMA_REPO_URL" figma-repo
fi

FIGMA_REPO_DIR="$TEMP_DIR/figma-repo"

# Проверка изменений
echo ""
echo -e "${BLUE}🔍 Проверка изменений...${NC}"

# Получаем последний коммит из Figma репозитория
cd "$FIGMA_REPO_DIR"
LATEST_COMMIT=$(git log -1 --format="%H %s")
LATEST_COMMIT_HASH=$(echo "$LATEST_COMMIT" | cut -d' ' -f1)
LATEST_COMMIT_MSG=$(echo "$LATEST_COMMIT" | cut -d' ' -f2-)

# Проверяем, есть ли файл с последним синхронизированным коммитом
SYNC_MARKER="$PROJECT_ROOT/.last_frontend_sync"
if [ -f "$SYNC_MARKER" ]; then
    LAST_SYNCED=$(cat "$SYNC_MARKER")
    if [ "$LATEST_COMMIT_HASH" == "$LAST_SYNCED" ]; then
        echo -e "${GREEN}✅ Фронтенд уже синхронизирован (коммит: ${LATEST_COMMIT_HASH:0:7})${NC}"
        echo -e "${GREEN}   Сообщение: $LATEST_COMMIT_MSG${NC}"
        rm -rf "$TEMP_DIR"
        exit 0
    else
        echo -e "${YELLOW}📝 Найдены новые изменения в Figma Make репозитории${NC}"
        echo -e "${YELLOW}   Последний синхронизированный: ${LAST_SYNCED:0:7}${NC}"
        echo -e "${YELLOW}   Текущий в Figma Make: ${LATEST_COMMIT_HASH:0:7}${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}📝 Первая синхронизация${NC}"
    echo -e "${YELLOW}   Коммит: ${LATEST_COMMIT_HASH:0:7} - $LATEST_COMMIT_MSG${NC}"
    echo ""
fi

# Показываем последние коммиты
echo -e "${BLUE}📋 Последние коммиты в Figma Make:${NC}"
git log --oneline -5
echo ""

# Копирование файлов
echo -e "${BLUE}📦 Копирование файлов в frontend/...${NC}"

# Создаем резервную копию текущего frontend (если есть)
if [ -d "$FRONTEND_DIR" ]; then
    BACKUP_DIR="$TEMP_DIR/frontend-backup-$(date +%Y%m%d-%H%M%S)"
    echo -e "${YELLOW}💾 Создание резервной копии текущего frontend...${NC}"
    cp -r "$FRONTEND_DIR" "$BACKUP_DIR"
fi

# Сохраняем защищенные файлы (не перезаписываются при синхронизации)
PROTECTED_FILES=(
    ".env.production"
    ".env.production.local"
)
BACKUP_PROTECTED="$TEMP_DIR/protected-files-backup"
mkdir -p "$BACKUP_PROTECTED"

for file in "${PROTECTED_FILES[@]}"; do
    if [ -f "$FRONTEND_DIR/$file" ]; then
        echo -e "${YELLOW}💾 Сохранение защищенного файла: $file${NC}"
        cp "$FRONTEND_DIR/$file" "$BACKUP_PROTECTED/$file"
    fi
done

# Удаляем старый frontend (кроме .git, если есть)
if [ -d "$FRONTEND_DIR" ]; then
    rm -rf "$FRONTEND_DIR"
fi

# Копируем новый frontend
mkdir -p "$FRONTEND_DIR"
cp -r "$FIGMA_REPO_DIR"/* "$FRONTEND_DIR/"
cp -r "$FIGMA_REPO_DIR"/.gitignore "$FRONTEND_DIR/" 2>/dev/null || true

# Восстанавливаем защищенные файлы
for file in "${PROTECTED_FILES[@]}"; do
    if [ -f "$BACKUP_PROTECTED/$file" ]; then
        echo -e "${GREEN}✅ Восстановление защищенного файла: $file${NC}"
        cp "$BACKUP_PROTECTED/$file" "$FRONTEND_DIR/$file"
    fi
done

# Сохраняем маркер синхронизации
echo "$LATEST_COMMIT_HASH" > "$SYNC_MARKER"

echo -e "${GREEN}✅ Файлы скопированы${NC}"
echo ""

# Показываем diff (если включен режим review)
if [ "$REVIEW_MODE" = true ] && [ -d "$BACKUP_DIR" ]; then
    echo -e "${BLUE}📊 Просмотр изменений (diff):${NC}"
    echo ""
    diff -rq "$BACKUP_DIR" "$FRONTEND_DIR" | head -20 || true
    echo ""
    echo -e "${YELLOW}Показаны первые 20 изменений. Полный diff можно посмотреть вручную.${NC}"
    echo ""
fi

# Проверка статуса git
cd "$PROJECT_ROOT"
if [ -n "$(git status --porcelain frontend/)" ]; then
    echo -e "${GREEN}📝 Обнаружены изменения в frontend/${NC}"
    echo ""
    
    if [ "$AUTO_COMMIT" = true ]; then
        echo -e "${BLUE}💾 Автоматический коммит...${NC}"
        git add frontend/
        git commit -m "[SYNC] Update frontend from Figma Make

Source commit: ${LATEST_COMMIT_HASH:0:7}
Message: $LATEST_COMMIT_MSG
Synced at: $(date '+%Y-%m-%d %H:%M:%S')"
        echo -e "${GREEN}✅ Изменения закоммичены${NC}"
    else
        echo -e "${YELLOW}💡 Изменения готовы к коммиту. Запустите:${NC}"
        echo ""
        echo -e "${BLUE}  git add frontend/${NC}"
        echo -e "${BLUE}  git commit -m \"[SYNC] Update frontend from Figma Make\"${NC}"
        echo ""
        echo -e "${YELLOW}Или используйте флаг --auto-commit для автоматического коммита${NC}"
    fi
else
    echo -e "${GREEN}✅ Нет изменений для коммита${NC}"
fi

# Очистка
echo ""
echo -e "${BLUE}🧹 Очистка временных файлов...${NC}"
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}✨ Синхронизация завершена!${NC}"
echo ""
echo -e "${BLUE}📌 Последний синхронизированный коммит: ${LATEST_COMMIT_HASH:0:7}${NC}"
echo -e "${BLUE}   Сообщение: $LATEST_COMMIT_MSG${NC}"

