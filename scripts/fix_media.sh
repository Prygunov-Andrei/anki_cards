#!/bin/bash
# Скрипт для исправления раздачи медиафайлов на сервере

SERVER="root@194.87.200.188"
PASS="qwnZY,nX43mSeA"
REMOTE_DIR="/opt/anki_cards"

echo "🔄 Перезапускаю backend..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$SERVER" "cd $REMOTE_DIR && docker compose restart backend"

echo "🔨 Пересобираю frontend..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$SERVER" "cd $REMOTE_DIR && docker compose build frontend"

echo "🚀 Запускаю frontend..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$SERVER" "cd $REMOTE_DIR && docker compose up -d frontend"

echo "✅ Готово!"

