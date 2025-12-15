#!/bin/bash

# Скрипт для авторизации Docker на сервере
# Использование: ./scripts/docker_login.sh [password_or_token]

set -e

SERVER="root@72.56.83.95"
SSH_PASSWORD="hN9DVVo_pu6d_X"
DOCKER_USERNAME="prygunov1979"

if [ -z "$1" ]; then
    echo "Использование: $0 <docker_password_or_token>"
    echo ""
    echo "Для получения access token:"
    echo "1. Зайдите на https://hub.docker.com/settings/security"
    echo "2. Создайте новый access token"
    echo "3. Используйте его вместо пароля"
    exit 1
fi

DOCKER_PASSWORD="$1"

echo "🔐 Авторизация Docker на сервере..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" <<EOF
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker info | grep -i username || echo "Проверка авторизации..."
EOF

echo "✅ Авторизация завершена!"
echo ""
echo "Теперь можно продолжить деплой - rate limits будут выше."

