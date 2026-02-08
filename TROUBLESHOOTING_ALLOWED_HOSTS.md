# Решение проблемы: DisallowedHost для Docker network

## Проблема

Backend отклонял запросы от frontend контейнера с ошибкой:
```
DisallowedHost: Invalid HTTP_HOST header: 'backend:8000'
```

## Причина

В Docker Compose frontend обращается к backend по имени контейнера `backend:8000`, но это имя не было добавлено в `ALLOWED_HOSTS` Django.

## Решение

1. **Добавить в `.env` на сервере:**
```env
ALLOWED_HOSTS=backend,localhost,127.0.0.1,yourdomain.com,www.yourdomain.com
```

2. **Перезапустить backend:**
```bash
docker compose restart backend
```

## Что исправлено

- ✅ Добавлен `backend` в ALLOWED_HOSTS (для Docker network)
- ✅ Добавлены `localhost` и `127.0.0.1` (для healthcheck)
- ✅ Обновлен `.env.example` с правильными значениями
- ✅ Исправлен healthcheck в `docker-compose.yml` (использует python вместо curl)
- ✅ Обновлена документация `docs/deployment/DEPLOYMENT.md`

## Дата решения

19 января 2026
