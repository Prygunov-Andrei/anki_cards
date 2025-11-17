# Этап сборки
FROM node:18-alpine AS builder

WORKDIR /app

# Аргумент для API URL
ARG REACT_APP_API_URL=http://localhost:8000/api

# Копирование package файлов
COPY package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода
COPY . .

# Установка переменной окружения для сборки
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Сборка приложения
RUN npm run build

# Этап production
FROM nginx:alpine

# Копирование собранных файлов из builder
COPY --from=builder /app/build /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открытие порта
EXPOSE 80

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]

