# Задание для фронтенда: Создание пустых карточек

## Обзор

Добавлена возможность создавать пустые карточки для слов в колоде. Пустая карточка имеет:
- **Лицевая сторона:** пусто (ничего не отображается)
- **Обратная сторона:** `<слово на изучаемом языке> // <перевод>` (например, "essen // кушать")

Это позволяет пользователю тренировать активное вспоминание слов без подсказок.

## API эндпоинты

### 1. Создание пустых карточек для всех слов в колоде

**Эндпоинт:** `POST /api/cards/decks/<deck_id>/create_empty_cards/`

**Параметры:**
- `deck_id` (в URL) - ID колоды

**Тело запроса:**
```json
{}
```
(Пустое тело)

**Ответ (успех):**
```typescript
{
  message: string;  // "Создано N пустых карточек"
  deck_id: number;
  deck_name: string;
  empty_cards_count: number;
  empty_cards: Array<{
    id: number;
    original_word: string;  // '' (пусто)
    translation: string;     // "essen // кушать"
    language: string;
    created: boolean;  // true - создано новое, false - обновлено существующее
  }>;
  skipped_cards?: Array<{
    id: number;
    translation: string;
    reason: string;  // "Уже в колоде"
  }>;
  errors?: Array<{
    word_id: number;
    original_word: string;
    error: string;
  }>;
}
```

**Пример ответа:**
```json
{
  "message": "Создано 5 пустых карточек",
  "deck_id": 1,
  "deck_name": "Немецкие слова",
  "empty_cards_count": 5,
  "empty_cards": [
    {
      "id": 10,
      "original_word": "",
      "translation": "essen // кушать",
      "language": "de",
      "created": true
    }
  ],
  "skipped_cards": null,
  "errors": null
}
```

**Ошибки:**
- `400 Bad Request` - Колода пуста
- `404 Not Found` - Колода не найдена
- `401 Unauthorized` - Не авторизован

### 2. Создание пустой карточки для одного слова

**Эндпоинт:** `POST /api/cards/decks/<deck_id>/create_empty_card/`

**Параметры:**
- `deck_id` (в URL) - ID колоды

**Тело запроса:**
```typescript
{
  word_id: number;  // ID слова для создания пустой карточки
}
```

**Ответ (успех):**
```typescript
{
  message: string;  // "Пустая карточка успешно создана"
  original_word: {
    id: number;
    original_word: string;
    translation: string;
    language: string;
  };
  empty_card: {
    id: number;
    original_word: string;  // '' (пусто)
    translation: string;    // "essen // кушать"
    language: string;
    created: boolean;  // true - создано новое, false - обновлено существующее
    added_to_deck: boolean;  // true - добавлено в колоду, false - уже было в колоде
  };
}
```

**Пример ответа:**
```json
{
  "message": "Пустая карточка успешно создана",
  "original_word": {
    "id": 5,
    "original_word": "essen",
    "translation": "кушать",
    "language": "de"
  },
  "empty_card": {
    "id": 10,
    "original_word": "",
    "translation": "essen // кушать",
    "language": "de",
    "created": true,
    "added_to_deck": true
  }
}
```

**Ошибки:**
- `400 Bad Request` - Неверные данные запроса
- `404 Not Found` - Колода или слово не найдено
- `401 Unauthorized` - Не авторизован
- `500 Internal Server Error` - Ошибка сервера

## Что нужно реализовать

### 1. Функция для создания пустых карточек для всех слов

**Местоположение:** На усмотрение фронтенда (например, в меню действий колоды)

**Поведение:**
- При вызове отправлять `POST /api/cards/decks/{deckId}/create_empty_cards/`
- Показывать индикатор загрузки
- При успехе:
  - Показать уведомление: "Создано {count} пустых карточек"
  - Обновить список слов в колоде
  - Обновить счетчик слов
- При ошибке:
  - Показать сообщение об ошибке

### 2. Функция для создания пустой карточки для одного слова

**Местоположение:** На усмотрение фронтенда (например, в меню действий слова)

**Поведение:**
- При вызове отправлять `POST /api/cards/decks/{deckId}/create_empty_card/` с `{ word_id: wordId }`
- Показывать индикатор загрузки
- При успехе:
  - Показать уведомление: "Пустая карточка создана"
  - Добавить пустую карточку в список (или обновить список)
  - Обновить счетчик слов
- При ошибке:
  - Показать сообщение об ошибке

### 3. Обновление сервиса

**В `frontend/src/services/deck.service.ts`:**

```typescript
/**
 * Создать пустые карточки для всех слов в колоде
 */
async createEmptyCards(deckId: number): Promise<{
  message: string;
  deck_id: number;
  deck_name: string;
  empty_cards_count: number;
  empty_cards: Array<{
    id: number;
    original_word: string;
    translation: string;
    language: string;
    created: boolean;
  }>;
  skipped_cards?: Array<{
    id: number;
    translation: string;
    reason: string;
  }>;
  errors?: Array<{
    word_id: number;
    original_word: string;
    error: string;
  }>;
}> {
  const response = await api.post(`/api/cards/decks/${deckId}/create_empty_cards/`);
  return response.data;
}

/**
 * Создать пустую карточку для одного слова
 */
async createEmptyCard(deckId: number, wordId: number): Promise<{
  message: string;
  original_word: {
    id: number;
    original_word: string;
    translation: string;
    language: string;
  };
  empty_card: {
    id: number;
    original_word: string;
    translation: string;
    language: string;
    created: boolean;
    added_to_deck: boolean;
  };
}> {
  const response = await api.post(`/api/cards/decks/${deckId}/create_empty_card/`, {
    word_id: wordId
  });
  return response.data;
}
```

## Важные моменты

1. **Формат пустой карточки:**
   - `original_word = '_empty_{word_id}'` (внутренний идентификатор, например "_empty_5")
   - `translation = '<слово> // <перевод>'` (например, "essen // кушать")
   - `language = target_lang` колоды (изучаемый язык)
   - **Важно:** При отображении пустых карточек нужно проверять, начинается ли `original_word` с `_empty_`, и если да, то показывать пустую строку вместо `original_word`

2. **Медиафайлы:**
   - Пустые карточки используют те же медиафайлы (audio, image), что и исходные слова
   - При генерации .apkg файла медиафайлы не дублируются

3. **Обновление существующих карточек:**
   - Если пустая карточка уже существует (проверка по `original_word=''`, `language` и `translation`), она обновляется (`created: false`)
   - Если карточка уже в колоде, она не добавляется повторно (`added_to_deck: false`)

4. **Визуальное отображение:**
   - При отображении пустых карточек можно показывать `translation` как "essen // кушать"
   - Или разделять на две части для лучшей читаемости

## Примеры использования

### Пример 1: Создание пустых карточек для всех слов

```typescript
const handleCreateEmptyCards = async () => {
  try {
    setLoading(true);
    const result = await deckService.createEmptyCards(deckId);
    toast.success(`Создано ${result.empty_cards_count} пустых карточек`);
    refreshDeck();
  } catch (error) {
    toast.error('Ошибка при создании пустых карточек');
  } finally {
    setLoading(false);
  }
};
```

### Пример 2: Создание пустой карточки для одного слова

```typescript
const handleCreateEmptyCard = async (wordId: number) => {
  try {
    setLoading(true);
    const result = await deckService.createEmptyCard(deckId, wordId);
    toast.success('Пустая карточка создана');
    refreshWords();
  } catch (error) {
    toast.error('Ошибка при создании пустой карточки');
  } finally {
    setLoading(false);
  }
};
```

## Тестирование

1. ✅ Создание пустых карточек для всех слов работает
2. ✅ Создание пустой карточки для одного слова работает
3. ✅ Уведомления показываются корректно
4. ✅ Список слов обновляется после создания
5. ✅ Счетчик слов обновляется
6. ✅ Обработка ошибок работает
7. ✅ Индикатор загрузки показывается
8. ✅ Пустые карточки отображаются корректно (original_word='', translation с //)

