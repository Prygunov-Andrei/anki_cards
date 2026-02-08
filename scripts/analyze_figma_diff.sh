#!/bin/bash

# Скрипт анализа различий между Figma репозиторием и текущим фронтендом
# Цель: определить, какие файлы нужно добавить в Figma вручную
# ВАЖНО: Этот скрипт НЕ изменяет файлы, только анализирует различия

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Конфигурация
FIGMA_REPO_URL="https://github.com/Prygunov-Andrei/Ankiflashcardgenerator.git"
TEMP_DIR="/tmp/figma-diff-analysis"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
OUTPUT_REPORT="$PROJECT_ROOT/docs/FIGMA_SYNC_REPORT.md"

echo -e "${BLUE}🔍 Анализ различий между Figma репозиторием и текущим фронтендом...${NC}"
echo -e "${YELLOW}⚠️  ВАЖНО: Этот скрипт только анализирует, не изменяет файлы!${NC}"
echo ""

# Проверка наличия git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git не установлен!${NC}"
    exit 1
fi

# Создание временной директории
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Клонирование или обновление репозитория Figma
if [ -d "figma-repo" ]; then
    echo -e "${BLUE}📥 Обновление существующего репозитория Figma...${NC}"
    cd figma-repo
    git fetch origin
    git reset --hard origin/main 2>/dev/null || git reset --hard origin/master 2>/dev/null || true
    cd ..
else
    echo -e "${BLUE}📥 Клонирование репозитория Figma Make...${NC}"
    git clone "$FIGMA_REPO_URL" figma-repo
fi

FIGMA_REPO_DIR="$TEMP_DIR/figma-repo"

# Проверка существования текущего фронтенда
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Директория frontend/ не найдена в основном репозитории!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Репозитории готовы к анализу${NC}"
echo ""

# Определение структуры Figma репозитория
echo -e "${BLUE}📋 Анализ структуры репозиториев...${NC}"

# Находим корень фронтенда в Figma репозитории
FIGMA_FRONTEND_DIR=""
if [ -d "$FIGMA_REPO_DIR/src" ]; then
    FIGMA_FRONTEND_DIR="$FIGMA_REPO_DIR"
elif [ -d "$FIGMA_REPO_DIR/frontend" ]; then
    FIGMA_FRONTEND_DIR="$FIGMA_REPO_DIR/frontend"
else
    # Проверяем, может быть файлы в корне
    if [ -f "$FIGMA_REPO_DIR/package.json" ]; then
        FIGMA_FRONTEND_DIR="$FIGMA_REPO_DIR"
    else
        echo -e "${RED}❌ Не удалось определить структуру Figma репозитория${NC}"
        echo -e "${YELLOW}Содержимое корня репозитория:${NC}"
        ls -la "$FIGMA_REPO_DIR" | head -20
        exit 1
    fi
fi

echo -e "${GREEN}✅ Figma фронтенд найден: $FIGMA_FRONTEND_DIR${NC}"
echo -e "${GREEN}✅ Текущий фронтенд: $FRONTEND_DIR${NC}"
echo ""

# Создание отчета
mkdir -p "$(dirname "$OUTPUT_REPORT")"
cat > "$OUTPUT_REPORT" << 'EOF'
# Отчет о различиях между Figma репозиторием и текущим фронтендом

**Дата анализа:** $(date '+%Y-%m-%d %H:%M:%S')
**Figma репозиторий:** https://github.com/Prygunov-Andrei/Ankiflashcardgenerator.git

## ⚠️ ВАЖНО

Этот отчет показывает, какие файлы/изменения есть в **текущем репозитории**, но отсутствуют в **Figma репозитории**.

**Направление синхронизации:** Текущий репозиторий → Figma (вручную)

---

## 📊 Сводка

EOF

# Функция для получения относительного пути
get_relative_path() {
    local file="$1"
    local base_dir="$2"
    echo "${file#$base_dir/}"
}

# Функция для проверки, является ли файл важным для синхронизации
is_important_file() {
    local file="$1"
    # Игнорируем:
    # - node_modules
    # - .git
    # - build/dist
    # - .env файлы (кроме примеров)
    # - логи
    # - временные файлы
    
    if [[ "$file" == *"node_modules"* ]] || \
       [[ "$file" == *".git"* ]] || \
       [[ "$file" == *"build"* ]] || \
       [[ "$file" == *"dist"* ]] || \
       [[ "$file" == *".env.local"* ]] || \
       [[ "$file" == *".env.production"* ]] || \
       [[ "$file" == *".log"* ]] || \
       [[ "$file" == *".DS_Store"* ]] || \
       [[ "$file" == *"htmlcov"* ]]; then
        return 1
    fi
    return 0
}

# Счетчики
NEW_FILES_COUNT=0
MODIFIED_FILES_COUNT=0
ONLY_IN_FIGMA_COUNT=0

# Временные файлы для хранения списков
NEW_FILES_LIST="$TEMP_DIR/new_files.txt"
MODIFIED_FILES_LIST="$TEMP_DIR/modified_files.txt"
ONLY_IN_FIGMA_LIST="$TEMP_DIR/only_in_figma.txt"
DIFF_DETAILS="$TEMP_DIR/diff_details.txt"

> "$NEW_FILES_LIST"
> "$MODIFIED_FILES_LIST"
> "$ONLY_IN_FIGMA_LIST"
> "$DIFF_DETAILS"

echo -e "${BLUE}🔍 Поиск новых файлов (есть в текущем, нет в Figma)...${NC}"

# Поиск новых файлов
find "$FRONTEND_DIR" -type f | while read -r file; do
    if ! is_important_file "$file"; then
        continue
    fi
    
    rel_path=$(get_relative_path "$file" "$FRONTEND_DIR")
    figma_file="$FIGMA_FRONTEND_DIR/$rel_path"
    
    if [ ! -f "$figma_file" ]; then
        echo "$rel_path" >> "$NEW_FILES_LIST"
        ((NEW_FILES_COUNT++)) || true
    fi
done

echo -e "${BLUE}🔍 Поиск измененных файлов...${NC}"

# Поиск измененных файлов
find "$FRONTEND_DIR" -type f | while read -r file; do
    if ! is_important_file "$file"; then
        continue
    fi
    
    rel_path=$(get_relative_path "$file" "$FRONTEND_DIR")
    figma_file="$FIGMA_FRONTEND_DIR/$rel_path"
    
    if [ -f "$figma_file" ]; then
        # Сравниваем файлы
        if ! diff -q "$file" "$figma_file" > /dev/null 2>&1; then
            echo "$rel_path" >> "$MODIFIED_FILES_LIST"
            ((MODIFIED_FILES_COUNT++)) || true
            
            # Сохраняем краткий diff
            echo "" >> "$DIFF_DETAILS"
            echo "### $rel_path" >> "$DIFF_DETAILS"
            echo "\`\`\`diff" >> "$DIFF_DETAILS"
            diff -u "$figma_file" "$file" | head -50 >> "$DIFF_DETAILS" 2>&1 || true
            echo "\`\`\`" >> "$DIFF_DETAILS"
        fi
    fi
done

echo -e "${BLUE}🔍 Поиск файлов только в Figma (для информации)...${NC}"

# Поиск файлов только в Figma (для информации)
find "$FIGMA_FRONTEND_DIR" -type f | while read -r file; do
    if ! is_important_file "$file"; then
        continue
    fi
    
    rel_path=$(get_relative_path "$file" "$FIGMA_FRONTEND_DIR")
    current_file="$FRONTEND_DIR/$rel_path"
    
    if [ ! -f "$current_file" ]; then
        echo "$rel_path" >> "$ONLY_IN_FIGMA_LIST"
        ((ONLY_IN_FIGMA_COUNT++)) || true
    fi
done

# Обновляем счетчики (правильный способ)
NEW_FILES_COUNT=$(wc -l < "$NEW_FILES_LIST" | tr -d ' ')
MODIFIED_FILES_COUNT=$(wc -l < "$MODIFIED_FILES_LIST" | tr -d ' ')
ONLY_IN_FIGMA_COUNT=$(wc -l < "$ONLY_IN_FIGMA_LIST" | tr -d ' ')

# Добавляем сводку в отчет
cat >> "$OUTPUT_REPORT" << EOF
- **Новых файлов** (только в текущем): $NEW_FILES_COUNT
- **Измененных файлов**: $MODIFIED_FILES_COUNT
- **Файлов только в Figma** (для справки): $ONLY_IN_FIGMA_COUNT

---

## 📁 Новые файлы (нужно добавить в Figma)

Эти файлы есть в текущем репозитории, но отсутствуют в Figma репозитории.

**Действие:** Скопировать эти файлы в Figma вручную.

EOF

if [ "$NEW_FILES_COUNT" -gt 0 ]; then
    echo "" >> "$OUTPUT_REPORT"
    echo "\`\`\`" >> "$OUTPUT_REPORT"
    cat "$NEW_FILES_LIST" >> "$OUTPUT_REPORT"
    echo "\`\`\`" >> "$OUTPUT_REPORT"
else
    echo "" >> "$OUTPUT_REPORT"
    echo "*Новых файлов не найдено*" >> "$OUTPUT_REPORT"
fi

cat >> "$OUTPUT_REPORT" << 'EOF'

---

## ✏️ Измененные файлы (нужно обновить в Figma)

Эти файлы существуют в обоих репозиториях, но имеют различия.

**Действие:** Обновить содержимое этих файлов в Figma вручную.

EOF

if [ "$MODIFIED_FILES_COUNT" -gt 0 ]; then
    echo "" >> "$OUTPUT_REPORT"
    echo "\`\`\`" >> "$OUTPUT_REPORT"
    cat "$MODIFIED_FILES_LIST" >> "$OUTPUT_REPORT"
    echo "\`\`\`" >> "$OUTPUT_REPORT"
    echo "" >> "$OUTPUT_REPORT"
    echo "### Детали изменений" >> "$OUTPUT_REPORT"
    echo "" >> "$OUTPUT_REPORT"
    cat "$DIFF_DETAILS" >> "$OUTPUT_REPORT"
else
    echo "" >> "$OUTPUT_REPORT"
    echo "*Измененных файлов не найдено*" >> "$OUTPUT_REPORT"
fi

cat >> "$OUTPUT_REPORT" << 'EOF'

---

## 📋 Файлы только в Figma (для справки)

Эти файлы есть в Figma репозитории, но отсутствуют в текущем.

**Действие:** Решить, нужно ли их добавить в текущий репозиторий или удалить из Figma.

EOF

if [ "$ONLY_IN_FIGMA_COUNT" -gt 0 ]; then
    echo "" >> "$OUTPUT_REPORT"
    echo "\`\`\`" >> "$OUTPUT_REPORT"
    head -50 "$ONLY_IN_FIGMA_LIST" >> "$OUTPUT_REPORT"
    echo "\`\`\`" >> "$OUTPUT_REPORT"
    if [ "$ONLY_IN_FIGMA_COUNT" -gt 50 ]; then
        echo "" >> "$OUTPUT_REPORT"
        echo "*... и еще $((ONLY_IN_FIGMA_COUNT - 50)) файлов*" >> "$OUTPUT_REPORT"
    fi
else
    echo "" >> "$OUTPUT_REPORT"
    echo "*Файлов только в Figma не найдено*" >> "$OUTPUT_REPORT"
fi

cat >> "$OUTPUT_REPORT" << 'EOF'

---

## 📝 Инструкции по синхронизации

### Для новых файлов:
1. Откройте файл в текущем репозитории
2. Скопируйте его содержимое
3. Создайте файл с таким же путем в Figma
4. Вставьте содержимое

### Для измененных файлов:
1. Откройте файл в текущем репозитории
2. Сравните с версией в Figma (используйте детали изменений выше)
3. Обновите файл в Figma согласно изменениям

### Приоритет файлов:
1. **Высокий приоритет:** `src/` файлы (компоненты, страницы, сервисы)
2. **Средний приоритет:** Конфигурационные файлы (`package.json`, `vite.config.ts`)
3. **Низкий приоритет:** Документация, скрипты

---

## ⚠️ Важные замечания

- **НЕ удаляйте** файлы из Figma, которые есть только там (если не уверены)
- **НЕ перезаписывайте** файлы без проверки различий
- Сохраняйте резервные копии перед массовыми изменениями
- Проверяйте работу после синхронизации

---

**Сгенерировано автоматически скриптом:** `scripts/analyze_figma_diff.sh`

EOF

# Заменяем дату в отчете
sed -i '' "s/\$(date[^)]*)/$(date '+%Y-%m-%d %H:%M:%S')/g" "$OUTPUT_REPORT" 2>/dev/null || \
sed -i "s/\$(date[^)]*)/$(date '+%Y-%m-%d %H:%M:%S')/g" "$OUTPUT_REPORT"

echo ""
echo -e "${GREEN}✅ Анализ завершен!${NC}"
echo ""
echo -e "${CYAN}📊 Результаты:${NC}"
echo -e "   Новых файлов: ${GREEN}$NEW_FILES_COUNT${NC}"
echo -e "   Измененных файлов: ${YELLOW}$MODIFIED_FILES_COUNT${NC}"
echo -e "   Файлов только в Figma: ${BLUE}$ONLY_IN_FIGMA_COUNT${NC}"
echo ""
echo -e "${GREEN}📄 Подробный отчет сохранен в:${NC}"
echo -e "   ${CYAN}$OUTPUT_REPORT${NC}"
echo ""

# Показываем краткую сводку
if [ "$NEW_FILES_COUNT" -gt 0 ] || [ "$MODIFIED_FILES_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Обнаружены различия, требующие синхронизации!${NC}"
    echo ""
    if [ "$NEW_FILES_COUNT" -gt 0 ]; then
        echo -e "${BLUE}Первые 10 новых файлов:${NC}"
        head -10 "$NEW_FILES_LIST" | while read -r file; do
            echo -e "   ${GREEN}+${NC} $file"
        done
        echo ""
    fi
    if [ "$MODIFIED_FILES_COUNT" -gt 0 ]; then
        echo -e "${BLUE}Первые 10 измененных файлов:${NC}"
        head -10 "$MODIFIED_FILES_LIST" | while read -r file; do
            echo -e "   ${YELLOW}~${NC} $file"
        done
        echo ""
    fi
else
    echo -e "${GREEN}✅ Репозитории синхронизированы!${NC}"
fi

# Очистка
echo -e "${BLUE}🧹 Очистка временных файлов...${NC}"
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}✨ Готово!${NC}"
