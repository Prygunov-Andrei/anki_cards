# Задание для фронтенда: Инвертирование слов в колоде

## Обзор

Добавлена возможность создавать инвертированные версии слов в колоде. Это позволяет изучать язык в обе стороны:
- **Прямое направление**: изучаемый язык → родной язык (например, "essen" → "кушать")
- **Обратное направление**: родной язык → изучаемый язык (например, "кушать" → "essen")

## API эндпоинты

### 1. Инвертирование всех слов в колоде

**Эндпоинт:** `POST /api/cards/decks/<deck_id>/invert_all/`

**Параметры:**
- `deck_id` (в URL) - ID колоды

**Тело запроса:**
```json
{}
```
(Пустое тело, все параметры в URL)

**Ответ (успех):**
```typescript
{
  message: string;  // "Инвертировано N слов"
  deck_id: number;
  deck_name: string;
  inverted_words_count: number;
  inverted_words: Array<{
    id: number;
    original_word: string;
    translation: string;
    language: string;
    created: boolean;  // true - создано новое, false - обновлено существующее
  }>;
  skipped_words?: Array<{
    id: number;
    original_word: string;
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
  "message": "Инвертировано 5 слов",
  "deck_id": 1,
  "deck_name": "Немецкие слова",
  "inverted_words_count": 5,
  "inverted_words": [
    {
      "id": 10,
      "original_word": "кушать",
      "translation": "essen",
      "language": "ru",
      "created": true
    }
  ],
  "skipped_words": null,
  "errors": null
}
```

**Ошибки:**
- `400 Bad Request` - Колода пуста
- `404 Not Found` - Колода не найдена
- `401 Unauthorized` - Не авторизован

### 2. Инвертирование одного слова

**Эндпоинт:** `POST /api/cards/decks/<deck_id>/invert_word/`

**Параметры:**
- `deck_id` (в URL) - ID колоды

**Тело запроса:**
```typescript
{
  word_id: number;  // ID слова для инвертирования
}
```

**Ответ (успех):**
```typescript
{
  message: string;  // "Слово успешно инвертировано"
  original_word: {
    id: number;
    original_word: string;
    translation: string;
    language: string;
  };
  inverted_word: {
    id: number;
    original_word: string;
    translation: string;
    language: string;
    created: boolean;  // true - создано новое, false - обновлено существующее
    added_to_deck: boolean;  // true - добавлено в колоду, false - уже было в колоде
  };
}
```

**Пример ответа:**
```json
{
  "message": "Слово успешно инвертировано",
  "original_word": {
    "id": 5,
    "original_word": "essen",
    "translation": "кушать",
    "language": "de"
  },
  "inverted_word": {
    "id": 10,
    "original_word": "кушать",
    "translation": "essen",
    "language": "ru",
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

### 1. Кнопка "Инвертировать все слова" в интерфейсе колоды

**Местоположение:** Страница детального просмотра колоды (Deck Detail)

**UI компонент:**
- Кнопка/иконка с подписью "Инвертировать все слова" или "Создать обратные карточки"
- Разместить рядом с другими действиями колоды (например, "Сгенерировать .apkg", "Объединить колоды")

**Поведение:**
1. При клике показывать подтверждение (модальное окно или диалог):
   ```
   Вы уверены, что хотите инвертировать все слова в колоде?
   
   Это создаст обратные карточки для каждого слова:
   - "essen" → "кушать" станет также "кушать" → "essen"
   - Колода удвоится (N слов станет 2N слов)
   - Медиафайлы будут переиспользованы
   ```
2. При подтверждении:
   - Показать индикатор загрузки
   - Отправить `POST /api/cards/decks/{deckId}/invert_all/`
   - При успехе:
     - Показать уведомление: "Инвертировано {count} слов"
     - Обновить список слов в колоде
     - Обновить счетчик слов в колоде
   - При ошибке:
     - Показать сообщение об ошибке
     - Если есть `errors` в ответе, показать детали

**Пример кода:**
```typescript
const handleInvertAllWords = async () => {
  const confirmed = await showConfirmDialog({
    title: 'Инвертировать все слова',
    message: 'Это создаст обратные карточки для каждого слова. Колода удвоится.',
    confirmText: 'Инвертировать',
    cancelText: 'Отмена'
  });
  
  if (!confirmed) return;
  
  try {
    setLoading(true);
    const response = await api.post(`/api/cards/decks/${deckId}/invert_all/`);
    
    showNotification({
      type: 'success',
      message: `Инвертировано ${response.data.inverted_words_count} слов`
    });
    
    // Обновить колоду
    await refreshDeck();
  } catch (error) {
    showNotification({
      type: 'error',
      message: error.response?.data?.error || 'Ошибка при инвертировании слов'
    });
  } finally {
    setLoading(false);
  }
};
```

### 2. Кнопка "Инвертировать" для отдельного слова

**Местоположение:** Список слов в колоде (рядом с каждым словом)

**UI компонент:**
- Иконка/кнопка "Инвертировать" или "↔️" рядом с каждым словом
- Можно разместить в меню действий слова (три точки или dropdown)

**Поведение:**
1. При клике:
   - Показать индикатор загрузки
   - Отправить `POST /api/cards/decks/{deckId}/invert_word/` с `{ word_id: wordId }`
   - При успехе:
     - Показать уведомление: "Слово инвертировано"
     - Добавить инвертированное слово в список (или обновить список)
     - Обновить счетчик слов
   - При ошибке:
     - Показать сообщение об ошибке

**Пример кода:**
```typescript
const handleInvertWord = async (wordId: number) => {
  try {
    setLoading(true);
    const response = await api.post(`/api/cards/decks/${deckId}/invert_word/`, {
      word_id: wordId
    });
    
    showNotification({
      type: 'success',
      message: 'Слово успешно инвертировано'
    });
    
    // Добавить инвертированное слово в список
    const invertedWord = response.data.inverted_word;
    addWordToDeck(invertedWord);
    
    // Или обновить весь список
    await refreshDeck();
  } catch (error) {
    showNotification({
      type: 'error',
      message: error.response?.data?.error || 'Ошибка при инвертировании слова'
    });
  } finally {
    setLoading(false);
  }
};
```

### 3. Визуальное отображение инвертированных слов

**Рекомендации:**
- Можно добавить визуальный индикатор, что слово является инвертированным (например, иконка "↔️" или метка)
- Можно группировать исходные и инвертированные слова вместе
- Можно показывать связь между исходным и инвертированным словом

**Пример:**
```typescript
// В списке слов
{words.map(word => (
  <WordCard
    key={word.id}
    word={word}
    isInverted={isInvertedWord(word)}  // Проверка, является ли слово инвертированным
    originalWordId={word.original_word_id}  // Если есть связь
    onInvert={() => handleInvertWord(word.id)}
  />
))}
```

### 4. Обновление сервиса

**В `frontend/src/services/deck.service.ts`:**

```typescript
/**
 * Инвертировать все слова в колоде
 */
async invertAllWords(deckId: number): Promise<{
  message: string;
  deck_id: number;
  deck_name: string;
  inverted_words_count: number;
  inverted_words: Array<{
    id: number;
    original_word: string;
    translation: string;
    language: string;
    created: boolean;
  }>;
  skipped_words?: Array<{
    id: number;
    original_word: string;
    reason: string;
  }>;
  errors?: Array<{
    word_id: number;
    original_word: string;
    error: string;
  }>;
}> {
  const response = await api.post(`/api/cards/decks/${deckId}/invert_all/`);
  return response.data;
}

/**
 * Инвертировать одно слово в колоде
 */
async invertWord(deckId: number, wordId: number): Promise<{
  message: string;
  original_word: {
    id: number;
    original_word: string;
    translation: string;
    language: string;
  };
  inverted_word: {
    id: number;
    original_word: string;
    translation: string;
    language: string;
    created: boolean;
    added_to_deck: boolean;
  };
}> {
  const response = await api.post(`/api/cards/decks/${deckId}/invert_word/`, {
    word_id: wordId
  });
  return response.data;
}
```

## Важные моменты

1. **Медиафайлы:**
   - Инвертированные слова используют те же медиафайлы (audio, image)
   - При генерации .apkg файла медиафайлы не дублируются (логика на бэкенде)

2. **Обновление существующих слов:**
   - Если инвертированное слово уже существует, оно обновляется (`created: false`)
   - Если слово уже в колоде, оно не добавляется повторно (`added_to_deck: false`)

3. **Языки:**
   - Инвертированное слово получает `language = source_lang` колоды
   - Например, если колода: `target_lang='de'`, `source_lang='ru'`
   - Исходное слово: `language='de'`
   - Инвертированное слово: `language='ru'`

4. **Размер колоды:**
   - После инвертирования всех слов колода удваивается (N → 2N)
   - Это нужно учитывать при отображении и предупреждать пользователя

5. **Производительность:**
   - Инвертирование всех слов может занять время для больших колод
   - Показывать индикатор загрузки и прогресс, если возможно

## Примеры использования

### Пример 1: Инвертирование всех слов

```typescript
// В компоненте DeckDetail
const DeckDetail = ({ deckId }) => {
  const [loading, setLoading] = useState(false);
  
  const handleInvertAll = async () => {
    if (!confirm('Инвертировать все слова? Колода удвоится.')) {
      return;
    }
    
    setLoading(true);
    try {
      const result = await deckService.invertAllWords(deckId);
      toast.success(`Инвертировано ${result.inverted_words_count} слов`);
      refreshDeck();
    } catch (error) {
      toast.error('Ошибка при инвертировании');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <Button onClick={handleInvertAll} disabled={loading}>
        {loading ? 'Инвертирование...' : 'Инвертировать все слова'}
      </Button>
    </div>
  );
};
```

### Пример 2: Инвертирование одного слова

```typescript
// В компоненте WordList
const WordList = ({ words, deckId }) => {
  const handleInvert = async (wordId) => {
    try {
      const result = await deckService.invertWord(deckId, wordId);
      toast.success('Слово инвертировано');
      // Обновить список
      refreshWords();
    } catch (error) {
      toast.error('Ошибка при инвертировании');
    }
  };
  
  return (
    <div>
      {words.map(word => (
        <div key={word.id}>
          <span>{word.original_word} → {word.translation}</span>
          <Button onClick={() => handleInvert(word.id)}>
            Инвертировать
          </Button>
        </div>
      ))}
    </div>
  );
};
```

## Тестирование

1. ✅ Инвертирование всех слов работает
2. ✅ Инвертирование одного слова работает
3. ✅ Уведомления показываются корректно
4. ✅ Список слов обновляется после инвертирования
5. ✅ Счетчик слов обновляется
6. ✅ Обработка ошибок работает
7. ✅ Индикатор загрузки показывается
8. ✅ Подтверждение перед инвертированием всех слов работает

