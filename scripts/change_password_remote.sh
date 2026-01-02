#!/bin/bash

# Скрипт для изменения пароля пользователя на удаленном сервере

SERVER="root@72.56.83.95"
SERVER_PASSWORD="hN9DVVo_pu6d_X"
PROJECT_PATH="/opt/anki_cards"
USERNAME="Maxim"
NEW_PASSWORD="Maxim"

echo "🔐 Изменение пароля пользователя $USERNAME на удаленном сервере..."

# Используем sshpass для автоматического ввода пароля (если установлен)
if command -v sshpass &> /dev/null; then
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" << EOF
cd $PROJECT_PATH
docker-compose exec -T backend python manage.py shell << PYTHON_EOF
from apps.users.models import User
u = User.objects.get(username='$USERNAME')
u.set_password('$NEW_PASSWORD')
u.save()
print('✅ Пароль успешно изменен для пользователя $USERNAME')
PYTHON_EOF
EOF
else
    echo "⚠️  sshpass не установлен. Выполните команду вручную:"
    echo ""
    echo "ssh $SERVER"
    echo "cd $PROJECT_PATH"
    echo "docker-compose exec backend python manage.py shell"
    echo ""
    echo "Затем в Python shell выполните:"
    echo "from apps.users.models import User"
    echo "u = User.objects.get(username='$USERNAME')"
    echo "u.set_password('$NEW_PASSWORD')"
    echo "u.save()"
    echo "print('✅ Пароль успешно изменен')"
fi
