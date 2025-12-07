# 🔄 Смена туннеля: ngrok → Cloudflare Tunnel

**Дата:** 1 декабря 2025  
**Причина:** Закончился бесплатный ngrok

---

## 📝 Что изменилось

### Старый URL (ngrok)
```
https://f6c058cfd2ea.ngrok-free.app
```

### Новый URL (Cloudflare Tunnel)
```
https://spouse-safer-being-luke.trycloudflare.com
```

---

## ✅ Обновленные файлы

### Конфигурация приложения
- ✅ `/lib/config.ts` - базовый URL API
- ✅ `/services/api.ts` - Axios клиент
- ✅ `/utils/url-helpers.ts` - утилиты для URL
- ✅ `/contexts/ThemeContext.tsx` - синхронизация темы
- ✅ `/components/BackendDiagnostics.tsx` - диагностика

### Документация
- ✅ `/README_BACKEND.md` - туннель упоминается как Cloudflare
- ✅ `/API_REFERENCE.md` - обновлен Base URL
- ✅ `/BACKEND_FIX.md` - обновлены checklist
- ✅ `/DJANGO_TRAILING_SLASH.md` - примеры curl
- ✅ `/SUMMARY.md` - примеры curl
- ✅ `/INDEX.md` - Backend URL
- ✅ `/STAGE_10_TESTING_GUIDE.md` - комментарии
- ✅ `/AVATAR_FIX.md` - примеры URL

### Сообщения об ошибках
- ✅ `/components/NetworkErrorBanner.tsx` - "Туннель активен (Cloudflare/ngrok)"
- ✅ `/pages/LoginPage.tsx` - сообщения об ошибках

---

## 🔧 Как работает Cloudflare Tunnel

Cloudflare Tunnel (ранее известный как Argo Tunnel) - это альтернатива ngrok для создания безопасных туннелей.

### Установка
```bash
# Установите cloudflared
# macOS
brew install cloudflare/cloudflare/cloudflared

# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Windows
# Скачайте .exe с https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

### Запуск туннеля
```bash
# Без логина (быстрый туннель)
cloudflared tunnel --url http://localhost:8000

# С логином (постоянный туннель)
cloudflared tunnel login
cloudflared tunnel create my-tunnel
cloudflared tunnel route dns my-tunnel my-subdomain.example.com
cloudflared tunnel run my-tunnel
```

### Преимущества Cloudflare Tunnel
- ✅ Бесплатный без лимитов
- ✅ Интеграция с Cloudflare DNS
- ✅ Высокая скорость
- ✅ Без предупреждений (как у ngrok)
- ✅ Встроенная защита от DDoS

---

## 🧪 Проверка работы

### 1. Проверка через браузер
Откройте: https://spouse-safer-being-luke.trycloudflare.com/api/health/

Должен вернуть:
```json
{
  "status": "ok",
  "message": "Backend is running"
}
```

### 2. Проверка через curl
```bash
curl https://spouse-safer-being-luke.trycloudflare.com/api/health/ \
  -H "ngrok-skip-browser-warning: true"
```

### 3. Через фронтенд
1. Откройте страницу логина
2. Нажмите "🔽 Расширенная диагностика"
3. Нажмите "▶️ Запустить тесты"
4. Все тесты должны быть ✅ зелеными

---

## 🔍 Совместимость

### Заголовки остались прежними
Хотя мы используем Cloudflare Tunnel, заголовок `ngrok-skip-browser-warning` остался для совместимости. Cloudflare Tunnel его игнорирует, но он не мешает.

```typescript
headers: {
  'Content-Type': 'application/json',
  'ngrok-skip-browser-warning': 'true', // Для совместимости
}
```

### Django CORS настройки
Настройки CORS остаются прежними:

```python
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'ngrok-skip-browser-warning',  # Для совместимости
]
```

---

## 📋 Checklist для Backend разработчика

Если вы используете Cloudflare Tunnel:

- [ ] cloudflared установлен
- [ ] Туннель запущен: `cloudflared tunnel --url http://localhost:8000`
- [ ] URL скопирован и обновлен в `/lib/config.ts`
- [ ] Django запущен на порту 8000
- [ ] CORS настроен (allow_origins=[\"*\"])
- [ ] Все эндпоинты работают со слешем: `/api/health/`

---

## 🆘 Если не работает

### Проблема: ERR_NETWORK
**Решение:**
1. Проверьте, что Django запущен: `python manage.py runserver`
2. Проверьте, что cloudflared запущен
3. Проверьте URL в консоли cloudflared

### Проблема: 502 Bad Gateway
**Решение:**
1. Django может быть не запущен
2. Порт 8000 может быть занят
3. Перезапустите cloudflared

### Проблема: CORS ошибка
**Решение:**
Убедитесь, что в Django settings.py:
```python
CORS_ALLOW_ALL_ORIGINS = True
```

---

## 💡 Альтернативы

Если Cloudflare Tunnel не работает, можно использовать:
- **ngrok** (платный после лимита)
- **localtunnel** (`npm install -g localtunnel`)
- **serveo.net** (SSH туннель)
- **expose** (Laravel)

---

## 🎯 Результат

✅ Туннель успешно изменен на Cloudflare  
✅ Все URL обновлены  
✅ Документация обновлена  
✅ Совместимость сохранена  
✅ Приложение работает как раньше

---

**Обновление завершено! 🎉**
