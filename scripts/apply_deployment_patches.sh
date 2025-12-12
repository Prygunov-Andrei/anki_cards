#!/bin/bash

# Скрипт применения патчей для деплоя после синхронизации фронтенда
# Использование: ./scripts/apply_deployment_patches.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
PATCHES_DIR="$PROJECT_ROOT/scripts/deployment-patches"

echo -e "${BLUE}🔧 Применение патчей для деплоя...${NC}"
echo ""

# Проверка существования директории фронтенда
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Директория frontend/ не найдена!${NC}"
    exit 1
fi

# Создание директории для патчей, если её нет
mkdir -p "$PATCHES_DIR"

# 1. Создание/обновление .env.production
echo -e "${BLUE}📝 Создание .env.production...${NC}"
cat > "$FRONTEND_DIR/.env.production" << 'EOF'
# Production environment variables
# Этот файл создается автоматически при деплое
# Не коммитится в репозиторий фронтенда (добавлен в .gitignore)

# API Base URL для продакшена (относительный путь, т.к. фронтенд и бэкенд на одном домене)
VITE_API_BASE_URL=/api
EOF
echo -e "${GREEN}✅ .env.production создан${NC}"

# 2. Проверка наличия nginx.conf
if [ ! -f "$FRONTEND_DIR/nginx.conf" ]; then
    echo -e "${YELLOW}⚠️  nginx.conf не найден, копирую из патчей...${NC}"
    if [ -f "$PATCHES_DIR/nginx.conf" ]; then
        cp "$PATCHES_DIR/nginx.conf" "$FRONTEND_DIR/nginx.conf"
        echo -e "${GREEN}✅ nginx.conf скопирован${NC}"
    else
        echo -e "${RED}❌ nginx.conf не найден в патчах!${NC}"
        echo -e "${YELLOW}💡 Убедитесь, что файл существует в scripts/deployment-patches/nginx.conf${NC}"
    fi
else
    echo -e "${GREEN}✅ nginx.conf уже существует${NC}"
fi

# 3. Проверка наличия Dockerfile
if [ ! -f "$FRONTEND_DIR/Dockerfile" ]; then
    echo -e "${YELLOW}⚠️  Dockerfile не найден, копирую из патчей...${NC}"
    if [ -f "$PATCHES_DIR/Dockerfile" ]; then
        cp "$PATCHES_DIR/Dockerfile" "$FRONTEND_DIR/Dockerfile"
        echo -e "${GREEN}✅ Dockerfile скопирован${NC}"
    else
        echo -e "${RED}❌ Dockerfile не найден в патчах!${NC}"
        echo -e "${YELLOW}💡 Убедитесь, что файл существует в scripts/deployment-patches/Dockerfile${NC}"
    fi
else
    echo -e "${GREEN}✅ Dockerfile уже существует${NC}"
fi

# 4. Проверка логики в config.ts (должна быть логика для продакшена)
echo -e "${BLUE}🔍 Проверка config.ts...${NC}"
if grep -q "PROD\|import.meta.env?.PROD" "$FRONTEND_DIR/src/lib/config.ts" 2>/dev/null; then
    echo -e "${GREEN}✅ config.ts содержит логику для продакшена${NC}"
else
    echo -e "${YELLOW}⚠️  config.ts может не содержать логику для продакшена${NC}"
    echo -e "${YELLOW}💡 Проверьте, что используется относительный путь /api в продакшене${NC}"
fi

# 5. КРИТИЧНО: Исправление логотипов из Figma Make (Base64 -> PNG + абсолютные пути)
echo -e "${BLUE}🖼️  Исправление логотипов...${NC}"

# Создаем папку public если её нет
mkdir -p "$FRONTEND_DIR/public"

# Декодируем Base64 изображения в настоящие PNG
LOGO_DARK="8438de77d51aa44238d74565f4aecffecf7eb633.png"
LOGO_LIGHT="d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png"

for LOGO in "$LOGO_DARK" "$LOGO_LIGHT"; do
    SRC_FILE="$FRONTEND_DIR/src/assets/$LOGO"
    DEST_FILE="$FRONTEND_DIR/public/$LOGO"
    
    if [ -f "$SRC_FILE" ]; then
        # Проверяем, является ли файл Base64-encoded (ASCII текст)
        if file "$SRC_FILE" | grep -q "ASCII text"; then
            echo -e "${YELLOW}   Декодирую $LOGO из Base64...${NC}"
            base64 -D -i "$SRC_FILE" -o "$DEST_FILE"
            echo -e "${GREEN}   ✅ $LOGO декодирован${NC}"
        else
            # Если файл уже бинарный PNG, просто копируем
            cp "$SRC_FILE" "$DEST_FILE"
            echo -e "${GREEN}   ✅ $LOGO скопирован${NC}"
        fi
    fi
done

# Исправляем импорты в LoginPage.tsx
if [ -f "$FRONTEND_DIR/src/pages/LoginPage.tsx" ]; then
    echo -e "${BLUE}   Исправляю импорты в LoginPage.tsx...${NC}"
    # Заменяем figma:asset импорты на абсолютные пути
    sed -i.bak "s|import logoLight from 'figma:asset/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';|// Логотипы из папки public (абсолютные пути)\nconst logoLight = '/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';|g" "$FRONTEND_DIR/src/pages/LoginPage.tsx"
    sed -i.bak "s|import logoDark from 'figma:asset/8438de77d51aa44238d74565f4aecffecf7eb633.png';|const logoDark = '/8438de77d51aa44238d74565f4aecffecf7eb633.png';|g" "$FRONTEND_DIR/src/pages/LoginPage.tsx"
    # Исправляем использование isDark (если useTheme не экспортирует isDark)
    sed -i.bak "s|const { isDark } = useTheme();|const { theme } = useTheme();\n  const isDark = theme === 'dark';|g" "$FRONTEND_DIR/src/pages/LoginPage.tsx"
    rm -f "$FRONTEND_DIR/src/pages/LoginPage.tsx.bak"
    echo -e "${GREEN}   ✅ LoginPage.tsx исправлен${NC}"
fi

# Исправляем импорты в RegisterPage.tsx
if [ -f "$FRONTEND_DIR/src/pages/RegisterPage.tsx" ]; then
    echo -e "${BLUE}   Исправляю импорты в RegisterPage.tsx...${NC}"
    sed -i.bak "s|import logoLight from 'figma:asset/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';|// Логотипы из папки public (абсолютные пути)\nconst logoLight = '/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';|g" "$FRONTEND_DIR/src/pages/RegisterPage.tsx"
    sed -i.bak "s|import logoDark from 'figma:asset/8438de77d51aa44238d74565f4aecffecf7eb633.png';|const logoDark = '/8438de77d51aa44238d74565f4aecffecf7eb633.png';|g" "$FRONTEND_DIR/src/pages/RegisterPage.tsx"
    sed -i.bak "s|const { isDark } = useTheme();|const { theme } = useTheme();\n  const isDark = theme === 'dark';|g" "$FRONTEND_DIR/src/pages/RegisterPage.tsx"
    rm -f "$FRONTEND_DIR/src/pages/RegisterPage.tsx.bak"
    echo -e "${GREEN}   ✅ RegisterPage.tsx исправлен${NC}"
fi

# Исправляем импорты в Header.tsx
if [ -f "$FRONTEND_DIR/src/components/Header.tsx" ]; then
    echo -e "${BLUE}   Исправляю импорты в Header.tsx...${NC}"
    sed -i.bak "s|import logoLight from 'figma:asset/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';|// Логотипы из папки public (абсолютные пути)\nconst logoLight = '/d1bf380f0678c426adcf5d36e80ffe7d5981e49a.png';|g" "$FRONTEND_DIR/src/components/Header.tsx"
    sed -i.bak "s|import logoDark from 'figma:asset/8438de77d51aa44238d74565f4aecffecf7eb633.png';|const logoDark = '/8438de77d51aa44238d74565f4aecffecf7eb633.png';|g" "$FRONTEND_DIR/src/components/Header.tsx"
    rm -f "$FRONTEND_DIR/src/components/Header.tsx.bak"
    echo -e "${GREEN}   ✅ Header.tsx исправлен${NC}"
fi

# Добавляем isDark в ThemeContext если его нет
if [ -f "$FRONTEND_DIR/src/contexts/ThemeContext.tsx" ]; then
    if ! grep -q "isDark:" "$FRONTEND_DIR/src/contexts/ThemeContext.tsx"; then
        echo -e "${BLUE}   Добавляю isDark в ThemeContext...${NC}"
        # Добавляем isDark в интерфейс
        sed -i.bak "s|toggleTheme: () => void;|isDark: boolean;\n  toggleTheme: () => void;|g" "$FRONTEND_DIR/src/contexts/ThemeContext.tsx"
        # Добавляем isDark в value
        sed -i.bak "s|const value = {|const value = {\n    isDark: theme === 'dark',|g" "$FRONTEND_DIR/src/contexts/ThemeContext.tsx"
        rm -f "$FRONTEND_DIR/src/contexts/ThemeContext.tsx.bak"
        echo -e "${GREEN}   ✅ ThemeContext.tsx исправлен${NC}"
    else
        echo -e "${GREEN}   ✅ ThemeContext.tsx уже содержит isDark${NC}"
    fi
fi

echo -e "${GREEN}✅ Логотипы исправлены${NC}"

# 6. Сохранение копий файлов для деплоя в патчах (для будущих синхронизаций)
echo -e "${BLUE}💾 Сохранение патчей для будущих синхронизаций...${NC}"
if [ -f "$FRONTEND_DIR/nginx.conf" ]; then
    cp "$FRONTEND_DIR/nginx.conf" "$PATCHES_DIR/nginx.conf"
    echo -e "${GREEN}✅ nginx.conf сохранен в патчах${NC}"
fi

if [ -f "$FRONTEND_DIR/Dockerfile" ]; then
    cp "$FRONTEND_DIR/Dockerfile" "$PATCHES_DIR/Dockerfile"
    echo -e "${GREEN}✅ Dockerfile сохранен в патчах${NC}"
fi

echo ""
echo -e "${GREEN}✨ Патчи для деплоя применены!${NC}"
echo ""
echo -e "${BLUE}📌 Следующие шаги:${NC}"
echo -e "${BLUE}   1. Проверьте изменения: git status${NC}"
echo -e "${BLUE}   2. Закоммитьте изменения: git add frontend/ && git commit -m \"[DEPLOY] Apply deployment patches\"${NC}"
echo -e "${BLUE}   3. Запустите деплой${NC}"

