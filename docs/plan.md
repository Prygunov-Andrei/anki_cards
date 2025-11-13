# План реализации приложения для генерации карточек Anki

## Общая информация о структуре файлов Anki

### Формат .apkg
- **Один файл .apkg = одна колода карточек** (может содержать множество карточек)
- Файл .apkg представляет собой ZIP-архив, содержащий:
  - Базу данных SQLite с записями (notes) и карточками (cards)
  - Папку `media/` с медиафайлами (изображения, аудио)
  - Метаданные колоды (название, описание, настройки)
- **Колода обязательно должна иметь название** при создании
- Для создания .apkg файлов используется библиотека `genanki` (Python)

### Структура данных Anki
- **Запись (Note)** — набор полей (слово, перевод, аудио, изображение)
- **Карточка (Card)** — визуальное представление записи для изучения
- Из одной записи можно создать несколько карточек (двусторонние карточки)

---

## Технический стек

### Backend
- **Python 3.10+**
- **Django 4.x** — веб-фреймворк
- **PostgreSQL** — база данных
- **genanki** — библиотека для создания .apkg файлов
- **Django REST Framework** — для API

### Frontend
- **React 18+**
- **TypeScript**
- **TailwindCSS** — стилизация
- **Axios** — HTTP-клиент

---

## Структура проекта

```
anki-card-generator/
├── backend/                 # Django проект
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/             # Настройки Django
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── users/          # Модель пользователя и аутентификация
│   │   ├── words/          # Модель слов и логика обработки
│   │   └── cards/          # Генерация .apkg файлов
│   └── media/              # Временное хранение медиафайлов
│
├── frontend/               # React приложение
│   ├── src/
│   │   ├── components/
│   │   │   ├── WordInput.tsx
│   │   │   ├── LanguageSelector.tsx
│   │   │   └── GenerateButton.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── App.tsx
│   └── package.json
│
└── README.md
```

---

## Модели базы данных (PostgreSQL)

### Модель User (расширение стандартной Django User)
- `id` — первичный ключ
- `username` — имя пользователя
- `email` — email
- `preferred_language` — предпочитаемый язык для создания карточек (`pt` или `de`)
- `created_at` — дата регистрации

### Модель Word
- `id` — первичный ключ
- `user` — ForeignKey к User
- `original_word` — исходное слово (португальское или немецкое)
- `translation` — перевод на русский
- `language` — язык исходного слова (`pt` или `de`)
- `audio_file` — путь к аудиофайлу (пока NULL, будет заполняться автоматически)
- `image_file` — путь к изображению (пока NULL, будет заполняться автоматически)
- `created_at` — дата создания
- `updated_at` — дата обновления
- **Индексы**: `(user, original_word, language)` — для быстрого поиска дубликатов

---

## API Endpoints (Django REST Framework)

### POST `/api/auth/register/`
Регистрация нового пользователя
- **Request**: `{ "username": "...", "email": "...", "password": "...", "preferred_language": "pt|de" }`
- **Response**: `{ "user_id": ..., "token": "..." }`

### POST `/api/auth/login/`
Вход пользователя
- **Request**: `{ "username": "...", "password": "..." }`
- **Response**: `{ "token": "..." }`

### GET `/api/user/profile/`
Получение профиля пользователя (требует аутентификации)
- **Response**: `{ "username": "...", "preferred_language": "pt|de" }`

### PATCH `/api/user/profile/`
Обновление профиля пользователя (требует аутентификации)
- **Request**: `{ "preferred_language": "pt|de" }`

### POST `/api/cards/generate/`
Генерация карточек Anki (требует аутентификации)
- **Request**: 
  ```json
  {
    "words": "casa, palavra, livro",
    "language": "pt",
    "translations": {
      "casa": "дом",
      "palavra": "слово",
      "livro": "книга"
    },
    "audio_files": {
      "casa": "/path/to/casa.mp3",
      "palavra": "/path/to/palavra.mp3",
      "livro": "/path/to/livro.mp3"
    },
    "image_files": {
      "casa": "/path/to/casa.jpg",
      "palavra": "/path/to/palavra.jpg",
      "livro": "/path/to/livro.jpg"
    },
    "deck_name": "Португальские слова - 2024"
  }
  ```
- **Response**: 
  ```json
  {
    "file_id": "uuid",
    "download_url": "/api/cards/download/uuid/",
    "deck_name": "Португальские слова - 2024",
    "cards_count": 6
  }
  ```

### GET `/api/cards/download/<file_id>/`
Скачивание сгенерированного .apkg файла
- **Response**: файл .apkg для скачивания

### GET `/api/words/list/`
Получение списка всех слов пользователя (требует аутентификации)
- **Query params**: `?language=pt|de&search=...`
- **Response**: 
  ```json
  {
    "words": [
      {
        "id": 1,
        "original_word": "casa",
        "translation": "дом",
        "language": "pt",
        "created_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
  ```

---

## Frontend компоненты (React)

### WordInput.tsx
- Текстовое поле для ввода слов через запятую
- Валидация ввода
- Отображение списка введенных слов

### LanguageSelector.tsx
- Выпадающий список для выбора языка (`pt` или `de`)
- По умолчанию берется из профиля пользователя
- Сохранение выбора в профиле пользователя

### GenerateButton.tsx
- Кнопка "Сгенерировать карточки"
- Индикатор загрузки
- Обработка ошибок

### App.tsx
- Главный компонент
- Интеграция всех компонентов
- Обработка ответа от API и скачивание файла

---

## Логика генерации .apkg файла

### Использование библиотеки genanki

```python
# Псевдокод логики
from genanki import Deck, Note, Model, Package

# 1. Создание модели карточки (Note Type)
model = Model(
    model_id=1234567890,
    name="Двусторонние карточки",
    fields=[
        {"name": "OriginalWord"},
        {"name": "Translation"},
        {"name": "Audio"},
        {"name": "Image"}
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{OriginalWord}}<br>{{Image}}",
            "afmt": "{{OriginalWord}}<br>{{Image}}<br>{{Audio}}<br>{{Translation}}"
        },
        {
            "name": "Card 2",
            "qfmt": "{{Translation}}<br>{{Image}}",
            "afmt": "{{Translation}}<br>{{Image}}<br>{{OriginalWord}}<br>{{Audio}}"
        }
    ]
)

# 2. Создание колоды с названием
deck = Deck(
    deck_id=9876543210,
    name="Португальские слова - 2024"  # Название колоды обязательно!
)

# 3. Добавление карточек для каждого слова
for word_data in words:
    note = Note(
        model=model,
        fields=[
            word_data["original"],
            word_data["translation"],
            f'[sound:{word_data["audio_filename"]}]',
            f'<img src="{word_data["image_filename"]}">'
        ]
    )
    deck.add_note(note)

# 4. Добавление медиафайлов
package = Package(deck)
package.media_files = [audio_paths, image_paths]

# 5. Генерация .apkg файла
package.write_to_file("deck.apkg")
```

---

## Процесс работы приложения (первый этап)

### Шаг 1: Пользователь вводит данные
1. Пользователь вводит слова через запятую: `"casa, palavra, livro"`
2. Выбирает язык: `pt` или `de`
3. Нажимает кнопку "Сгенерировать"

### Шаг 2: Backend обработка (пока ручной ввод)
1. Парсинг введенных слов (разделение по запятой, очистка пробелов)
2. Проверка на дубликаты в базе данных для данного пользователя
3. **ПОКА**: Пользователь вручную вводит переводы, загружает аудио и изображения
4. Сохранение слов в базу данных PostgreSQL
5. Генерация .apkg файла с использованием genanki
6. Сохранение .apkg файла во временное хранилище
7. Возврат ссылки на скачивание

### Шаг 3: Скачивание файла
1. Frontend получает ссылку на скачивание
2. Автоматическое скачивание .apkg файла
3. Пользователь импортирует файл в Anki

---

## База данных - сохранение слов

### Логика сохранения
- Все введенные пользователем слова сохраняются в таблицу `Word`
- Привязка к пользователю через ForeignKey
- Проверка на дубликаты: `(user, original_word, language)` должно быть уникально
- При попытке добавить дубликат — возвращается существующая запись

### Будущие возможности
- Механизм запрета выбора уже существующих слов (опционально)
- Механизм выбора из существующих слов для создания новых карточек
- История использования слов

---

## Настройки и конфигурация

### Django settings.py
- `DATABASES` — подключение к PostgreSQL
- `MEDIA_ROOT` — путь для хранения медиафайлов
- `MEDIA_URL` — URL для доступа к медиафайлам
- `CORS_ALLOWED_ORIGINS` — разрешенные домены для CORS (React приложение)

### Переменные окружения (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/anki_db
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Этапы разработки

### Этап 1: Базовая структура (текущий)
- ✅ Настройка Django проекта
- ✅ Настройка PostgreSQL
- ✅ Создание моделей User и Word
- ✅ Базовый API для регистрации/входа
- ✅ Простой React фронтенд с формой ввода
- ✅ Ручной ввод переводов, аудио и изображений
- ✅ Генерация .apkg файла с использованием genanki
- ✅ Скачивание файла

### Этап 2: Автоматизация (будущее)
- Автоматический перевод через API (Google Translate, DeepL)
- Автоматическая генерация аудио через TTS API (Google TTS, Azure)
- Автоматическая генерация/поиск изображений (DALL-E, Unsplash)

### Этап 3: Дополнительные функции (будущее)
- Механизм выбора из существующих слов
- Механизм запрета дубликатов (опционально)
- История создания колод
- Статистика использования слов

---

## Важные замечания

### О структуре .apkg файла
- **Один .apkg файл = одна колода карточек**
- Колода может содержать множество карточек
- **Название колоды обязательно** при создании через genanki
- Рекомендуется использовать уникальные названия: `"Португальские слова - {дата}"` или `"Немецкие слова - {дата}"`

### О двусторонних карточках
- Из одной записи (Note) создаются 2 карточки:
  1. Португальский/Немецкий → Русский
  2. Русский → Португальский/Немецкий
- Это настраивается в шаблоне модели (Model) через genanki

### О медиафайлах
- Аудиофайлы должны быть в формате MP3
- Изображения должны быть в формате JPG или PNG
- Имена файлов должны быть уникальными (рекомендуется использовать хеш или UUID)
- Медиафайлы упаковываются в .apkg архив автоматически через genanki

---

## Зависимости (requirements.txt)

```
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
psycopg2-binary==2.9.9
genanki==0.13.0
python-dotenv==1.0.0
```

---

## Ссылки на документацию

- [Anki Documentation](https://docs.ankiweb.net/)
- [genanki Library](https://github.com/kerrickstaley/genanki)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Documentation](https://react.dev/)

