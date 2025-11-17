#!/bin/bash
# Скрипт настройки домена www.get-anki.fun

set -e

cd /opt/anki_cards

echo "🔄 Пересобираю frontend с новым доменом..."
docker compose build frontend

echo "🔄 Перезапускаю backend с обновленными переменными..."
docker compose restart backend

echo "🔄 Перезапускаю frontend..."
docker compose restart frontend

echo "✅ Контейнеры перезапущены"
docker compose ps

echo ""
echo "📝 Следующие шаги для настройки SSL:"
echo "1. Установите certbot: apt install -y certbot"
echo "2. Получите сертификат: certbot certonly --standalone -d www.get-anki.fun -d get-anki.fun"
echo "3. Раскомментируйте редирект на HTTPS в nginx.conf (строка 7)"
echo "4. Перезапустите frontend: docker compose restart frontend"

