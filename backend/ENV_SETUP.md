# Настройка переменных окружения (.env)

## Быстрая настройка

1. **Скопируйте пример файла:**
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Откройте файл `.env` и заполните необходимые переменные:**
   ```bash
   nano .env  # или используйте любой текстовый редактор
   ```

## Обязательные переменные

### SECRET_KEY
Секретный ключ Django для безопасности. Используйте сгенерированный ключ:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### OPENAI_API_KEY
**ВАЖНО:** Без этого ключа генерация медиафайлов не будет работать!

#### Как получить API ключ OpenAI:

1. Перейдите на https://platform.openai.com/
2. Зарегистрируйтесь или войдите в аккаунт
3. Перейдите в раздел [API Keys](https://platform.openai.com/api-keys)
4. Нажмите "Create new secret key"
5. Скопируйте ключ (он показывается только один раз!)
6. Вставьте ключ в `.env` файл:
   ```
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

**Примечание:** 
- API ключ начинается с `sk-`
- Храните ключ в секрете, не коммитьте `.env` в Git
- При использовании API будут списываться средства с вашего баланса OpenAI

## Опциональные переменные

### DATABASE_URL
Для использования PostgreSQL вместо SQLite:
```
DATABASE_URL=postgresql://username:password@localhost:5432/anki_db
```

Если оставить пустым, будет использоваться SQLite (для разработки).

### DEBUG
Режим отладки (True/False):
```
DEBUG=True
```

### ALLOWED_HOSTS
Разрешенные хосты (через запятую):
```
ALLOWED_HOSTS=localhost,127.0.0.1
```

### CORS_ALLOWED_ORIGINS
Разрешенные источники для CORS:
```
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### MEDIA_ROOT и MEDIA_URL
Пути для медиафайлов (обычно не нужно менять):
```
MEDIA_ROOT=media
MEDIA_URL=/media/
```

## Пример готового .env файла

```env
# Django настройки
SECRET_KEY=ie#v95yw*g9^k5q0z9q@i=qxy(=p*tf9=loia%r!^jyt7m)#0h
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# База данных (SQLite по умолчанию)
# DATABASE_URL=

# CORS настройки
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Медиафайлы
MEDIA_ROOT=media
MEDIA_URL=/media/

# OpenAI API (ОБЯЗАТЕЛЬНО для генерации медиа!)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Проверка настройки

После настройки `.env` файла, проверьте что все работает:

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Проверьте что Django видит переменные
python manage.py shell
>>> import os
>>> from dotenv import load_dotenv
>>> load_dotenv()
>>> os.getenv('OPENAI_API_KEY')
'sk-proj-...'  # Должен показать ваш ключ
```

## Безопасность

⚠️ **ВАЖНО:**
- Файл `.env` уже добавлен в `.gitignore` и не будет закоммичен в Git
- Никогда не публикуйте ваш API ключ OpenAI
- В production используйте переменные окружения сервера вместо `.env` файла

