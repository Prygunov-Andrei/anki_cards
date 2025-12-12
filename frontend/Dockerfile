# Frontend Dockerfile (Multi-stage build)
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Копирование package.json и установка зависимостей
COPY package.json ./
RUN npm install

# Копирование исходного кода
COPY . .

# Сборка приложения (использует .env.production если есть)
RUN npm run build

# Stage 2: Production (Nginx)
FROM nginx:alpine

# Копирование собранных файлов из builder (Vite настроен на build/)
COPY --from=builder /app/build /usr/share/nginx/html

# Копирование конфигурации Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Порт
EXPOSE 80

# Запуск Nginx
CMD ["nginx", "-g", "daemon off;"]

