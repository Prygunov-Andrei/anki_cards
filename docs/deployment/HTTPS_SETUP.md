# 🔒 Настройка HTTPS для get-anki.fun

## Текущая ситуация

- ✅ HTTP работает: http://www.get-anki.fun/admin/
- ❌ HTTPS не настроен на сервере (порт 443 не слушается)

## Варианты настройки HTTPS

### Вариант 1: Cloudflare (Рекомендуется)

Если вы используете Cloudflare для DNS и SSL:

1. **В панели Cloudflare:**
   - Убедитесь, что SSL/TLS режим установлен в "Full" или "Full (strict)"
   - Включите "Always Use HTTPS"
   - Убедитесь, что проксирование включено (оранжевое облако)

2. **Настройки уже применены:**
   - ✅ `ALLOWED_HOSTS` включает `www.get-anki.fun` и `get-anki.fun`
   - ✅ `CSRF_TRUSTED_ORIGINS` включает HTTPS домены
   - ✅ `SECURE_PROXY_SSL_HEADER` настроен для работы за прокси
   - ✅ Nginx передает `X-Forwarded-Proto` от Cloudflare

3. **Проверка:**
   ```bash
   curl -I https://www.get-anki.fun/admin/
   ```

### Вариант 2: Certbot + Let's Encrypt (Прямой SSL на сервере)

Если нужно настроить SSL напрямую на сервере:

1. **Установка Certbot:**
   ```bash
   ssh root@72.56.83.95
   apt update
   apt install certbot python3-certbot-nginx -y
   ```

2. **Получение сертификата:**
   ```bash
   certbot --nginx -d www.get-anki.fun -d get-anki.fun
   ```

3. **Настройка Nginx для HTTPS:**
   - Certbot автоматически обновит конфигурацию
   - Нужно будет добавить блок `server` для порта 443 в `frontend/nginx.conf`

4. **Обновление Docker контейнера:**
   - Добавить volume для SSL сертификатов
   - Обновить nginx.conf для поддержки HTTPS

### Вариант 3: Внешний Nginx на хосте

Если используется внешний Nginx на хосте (не в Docker):

1. **Создать конфигурацию:**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name www.get-anki.fun get-anki.fun;
       
       ssl_certificate /etc/letsencrypt/live/www.get-anki.fun/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/www.get-anki.fun/privkey.pem;
       
       location / {
           proxy_pass http://127.0.0.1:80;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## Текущие настройки Django

- ✅ `ALLOWED_HOSTS`: включает `www.get-anki.fun`, `get-anki.fun`
- ✅ `CSRF_TRUSTED_ORIGINS`: включает HTTPS домены
- ✅ `SECURE_PROXY_SSL_HEADER`: настроен для работы за прокси
- ✅ Nginx передает заголовки от внешнего прокси

## Проверка работы

После настройки HTTPS проверьте:

```bash
# Проверка редиректа
curl -I https://www.get-anki.fun/admin/

# Проверка страницы входа
curl -s https://www.get-anki.fun/admin/login/ | grep -o "<title>.*</title>"
```

## Важно

Если используется Cloudflare:
- Убедитесь, что режим SSL/TLS = "Full" или "Full (strict)"
- Django уже настроен для работы за прокси через `SECURE_PROXY_SSL_HEADER`
- Nginx передает `X-Forwarded-Proto` от Cloudflare

Если HTTPS все еще не работает:
1. Проверьте настройки Cloudflare (если используется)
2. Проверьте, что домен правильно указывает на сервер
3. Проверьте логи: `docker compose logs backend frontend`

