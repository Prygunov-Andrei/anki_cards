#!/bin/bash

# Скрипт для запуска автоматических тестов этапов 9 и 10

set -e

echo "=========================================="
echo "Запуск автоматических тестов этапов 9 и 10"
echo "=========================================="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Переходим в директорию проекта
cd "$(dirname "$0")/.." || exit 1

# Backend тесты
echo -e "${YELLOW}=== Backend тесты ===${NC}"
echo ""

cd backend || exit 1

# Активируем виртуальное окружение, если оно существует
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Запуск тестов для этапа 9 (Редактирование промптов)..."
pytest apps/cards/tests.py::TestUserPrompts -v --tb=short || {
    echo -e "${RED}❌ Тесты этапа 9 провалились${NC}"
    exit 1
}

echo ""
echo "Запуск тестов для этапа 10 (Определение части речи)..."
pytest apps/cards/tests.py::TestPartOfSpeechDetection -v --tb=short || {
    echo -e "${RED}❌ Тесты определения части речи провалились${NC}"
    exit 1
}

echo ""
echo "Запуск тестов форматирования промптов..."
pytest apps/cards/tests.py::TestPromptFormatting -v --tb=short || {
    echo -e "${RED}❌ Тесты форматирования промптов провалились${NC}"
    exit 1
}

echo ""
echo "Запуск тестов заводских промптов..."
pytest apps/cards/tests.py::TestDefaultPrompts -v --tb=short || {
    echo -e "${RED}❌ Тесты заводских промптов провалились${NC}"
    exit 1
}

echo ""
echo "Запуск тестов модели PartOfSpeechCache..."
pytest apps/cards/tests.py::TestPartOfSpeechCacheModel -v --tb=short || {
    echo -e "${RED}❌ Тесты модели PartOfSpeechCache провалились${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}✅ Все backend тесты пройдены успешно!${NC}"
echo ""

# Frontend тесты
cd ../frontend || exit 1

echo -e "${YELLOW}=== Frontend тесты ===${NC}"
echo ""

if [ ! -d "node_modules" ]; then
    echo "Установка зависимостей..."
    npm install
fi

echo "Запуск тестов компонента PromptEditor..."
npm test -- PromptEditor.test.tsx --watchAll=false --coverage=false || {
    echo -e "${RED}❌ Frontend тесты провалились${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}✅ Все frontend тесты пройдены успешно!${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}✅ Все автоматические тесты пройдены!${NC}"
echo "=========================================="
echo ""
echo "Для ручного тестирования см. docs/MANUAL_TESTING_STAGES_9_10.md"

