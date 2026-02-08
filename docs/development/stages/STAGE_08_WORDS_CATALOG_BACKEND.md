# Этап 8: Каталог слов - Детальный план (Backend)

## Цель этапа

Расширить API для каталога слов с поддержкой:
- Расширенной фильтрации (по статусу обучения, части речи, категориям, колодам)
- Сортировки (по дате, алфавиту, статусу, следующему повторению)
- Пагинации
- Статистики по словам
- Действий со словами (редактирование, удаление, отправка в режим изучения)

---

## Требования

1. Определение статуса обучения слова на основе его карточек
2. Расширенная фильтрация и сортировка в `words_list_view`
3. Пагинация для больших списков
4. Статистика по словам (общая и по слову)
5. Эндпоинты для действий со словами
6. Обновление `learning_status` слова на основе карточек

---

## Архитектура

### Структура файлов

```
backend/apps/words/
├── views.py              # Обновить: расширить words_list_view, добавить новые эндпоинты
├── serializers.py        # Обновить: добавить сериализаторы для статистики
├── utils.py              # Новый: утилиты для определения статуса слова
└── urls.py               # Обновить: добавить новые маршруты
```

---

## 1. Утилиты для определения статуса слова

**Файл:** `backend/apps/words/utils.py` (новый)

### 1.1. Функция: `get_word_learning_status()`

**Назначение:** Определяет статус обучения слова на основе его карточек

**Логика:**
1. Получаем все карточки слова
2. Если нет карточек → `'new'`
3. Если есть карточки в режиме изучения → `'learning'`
4. Если есть карточки на повторении (next_review <= now) → `'reviewing'`
5. Если все карточки освоены (next_review > now, interval >= 30) → `'mastered'`
6. Иначе → `'reviewing'`

**Сигнатура:**
```python
def get_word_learning_status(word: Word) -> str:
    """
    Определяет статус обучения слова на основе его карточек.
    
    Args:
        word: Объект Word
    
    Returns:
        'new' | 'learning' | 'reviewing' | 'mastered'
    """
```

### 1.2. Функция: `update_word_learning_status()`

**Назначение:** Обновляет `learning_status` слова на основе карточек

**Сигнатура:**
```python
def update_word_learning_status(word: Word) -> Word:
    """
    Обновляет learning_status слова на основе его карточек.
    
    Args:
        word: Объект Word
    
    Returns:
        Обновлённый объект Word
    """
```

### 1.3. Функция: `get_word_next_review()`

**Назначение:** Возвращает ближайшую дату следующего повторения среди всех карточек слова

**Сигнатура:**
```python
def get_word_next_review(word: Word) -> Optional[datetime]:
    """
    Возвращает ближайшую дату следующего повторения среди всех карточек слова.
    
    Args:
        word: Объект Word
    
    Returns:
        datetime или None, если нет карточек на повторении
    """
```

### 1.4. Функция: `get_word_cards_stats()`

**Назначение:** Возвращает статистику по карточкам слова

**Сигнатура:**
```python
def get_word_cards_stats(word: Word) -> Dict[str, Any]:
    """
    Возвращает статистику по карточкам слова.
    
    Returns:
        {
            'total_cards': int,
            'normal_cards': int,
            'inverted_cards': int,
            'empty_cards': int,
            'cloze_cards': int,
            'in_learning_mode': int,
            'due_for_review': int,
            'mastered': int,
            'next_review': Optional[datetime],
        }
    """
```

---

## 2. Обновление `words_list_view`

**Файл:** `backend/apps/words/views.py`

### 2.1. Расширенная фильтрация

**Query параметры:**
- `language` — фильтр по языку (уже есть)
- `learning_status` — фильтр по статусу (уже есть, но нужно обновлять статус динамически)
- `part_of_speech` — фильтр по части речи (новое)
- `category_id` — фильтр по категории (новое)
- `deck_id` — фильтр по колоде (новое)
- `search` — поиск по тексту (уже есть)
- `has_etymology` — есть/нет этимология (новое, опционально)
- `has_hint` — есть/нет подсказка (новое, опционально)
- `has_sentences` — есть/нет предложения (новое, опционально)

### 2.2. Сортировка

**Query параметр:** `ordering`

**Варианты:**
- `created_at` — по дате добавления (по умолчанию, убывание)
- `-created_at` — по дате добавления (возрастание)
- `original_word` — по алфавиту (A-Z)
- `-original_word` — по алфавиту (Z-A)
- `learning_status` — по статусу обучения
- `next_review` — по следующему повторению (ближайшие первыми)
- `-next_review` — по следующему повторению (дальние первыми)

### 2.3. Пагинация

**Query параметры:**
- `page` — номер страницы (по умолчанию 1)
- `page_size` — размер страницы (по умолчанию 20, максимум 100)

**Формат ответа:**
```json
{
  "count": 150,
  "next": "/api/words/list/?page=2",
  "previous": null,
  "results": [...]
}
```

### 2.4. Аннотации для сортировки

Для сортировки по `next_review` нужно добавить аннотацию:
```python
from django.db.models import Min
from django.utils import timezone

words = words.annotate(
    next_review=Min('cards__next_review')
)
```

---

## 3. Новые эндпоинты

### 3.1. Обновление слова

**Эндпоинт:** `PATCH /api/words/{word_id}/`

**Файл:** `backend/apps/words/views.py`

**Функция:** `word_update_view()`

**Логика:**
- Использовать `WordUpdateSerializer`
- Обновить только переданные поля
- Валидация данных
- Автоматическое обновление `learning_status` после обновления

### 3.2. Удаление слова

**Эндпоинт:** `DELETE /api/words/{word_id}/`

**Файл:** `backend/apps/words/views.py`

**Функция:** `word_delete_view()`

**Логика:**
- Проверка, что слово принадлежит пользователю
- Удаление слова (CASCADE удалит карточки, связи)
- Возврат подтверждения

### 3.3. Статистика по слову

**Эндпоинт:** `GET /api/words/{word_id}/stats/`

**Файл:** `backend/apps/words/views.py`

**Функция:** `word_stats_view()`

**Ответ:**
```json
{
  "word_id": 123,
  "cards_stats": {
    "total_cards": 3,
    "normal_cards": 1,
    "inverted_cards": 1,
    "empty_cards": 1,
    "cloze_cards": 0,
    "in_learning_mode": 1,
    "due_for_review": 2,
    "mastered": 0,
    "next_review": "2026-01-12T10:00:00Z"
  },
  "learning_status": "reviewing",
  "has_etymology": true,
  "has_hint": true,
  "has_sentences": true,
  "sentences_count": 3,
  "relations_count": {
    "synonyms": 2,
    "antonyms": 1
  },
  "categories_count": 2,
  "decks_count": 1
}
```

### 3.4. Общая статистика по словам

**Эндпоинт:** `GET /api/words/stats/`

**Файл:** `backend/apps/words/views.py`

**Функция:** `words_stats_view()`

**Ответ:**
```json
{
  "total_words": 150,
  "by_language": {
    "de": 80,
    "pt": 70
  },
  "by_status": {
    "new": 20,
    "learning": 30,
    "reviewing": 50,
    "mastered": 50
  },
  "by_part_of_speech": {
    "noun": 60,
    "verb": 40,
    "adjective": 30,
    "other": 20
  },
  "with_etymology": 120,
  "with_hint": 80,
  "with_sentences": 100,
  "total_cards": 300,
  "due_for_review": 45
}
```

### 3.5. Отправка слова в режим изучения

**Эндпоинт:** `POST /api/words/{word_id}/enter-learning/`

**Файл:** `backend/apps/words/views.py`

**Функция:** `word_enter_learning_view()`

**Логика:**
- Получить все карточки слова
- Для каждой карточки вызвать `card.enter_learning_mode()`
- Обновить `learning_status` слова
- Вернуть обновлённое слово

### 3.6. Массовые действия

**Эндпоинт:** `POST /api/words/bulk-action/`

**Файл:** `backend/apps/words/views.py`

**Функция:** `words_bulk_action_view()`

**Body:**
```json
{
  "word_ids": [1, 2, 3],
  "action": "enter_learning" | "delete" | "add_to_deck" | "add_to_category" | "remove_from_category",
  "params": {
    "deck_id": 123,  // для add_to_deck
    "category_id": 456  // для add_to_category/remove_from_category
  }
}
```

**Ответ:**
```json
{
  "action": "enter_learning",
  "processed": 3,
  "successful": 3,
  "failed": 0,
  "errors": []
}
```

---

## 4. Сериализаторы

**Файл:** `backend/apps/words/serializers.py`

### 4.1. Обновить `WordListSerializer`

Добавить поля:
- `next_review` — ближайшая дата повторения
- `cards_count` — количество карточек
- `categories` — список категорий (компактный)
- `decks` — список колод (компактный)

### 4.2. Новый: `WordStatsSerializer`

```python
class WordStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики слова"""
    
    word_id = serializers.IntegerField()
    cards_stats = serializers.DictField()
    learning_status = serializers.CharField()
    has_etymology = serializers.BooleanField()
    has_hint = serializers.BooleanField()
    has_sentences = serializers.BooleanField()
    sentences_count = serializers.IntegerField()
    relations_count = serializers.DictField()
    categories_count = serializers.IntegerField()
    decks_count = serializers.IntegerField()
```

### 4.3. Новый: `WordsStatsSerializer`

```python
class WordsStatsSerializer(serializers.Serializer):
    """Сериализатор для общей статистики слов"""
    
    total_words = serializers.IntegerField()
    by_language = serializers.DictField(child=serializers.IntegerField())
    by_status = serializers.DictField(child=serializers.IntegerField())
    by_part_of_speech = serializers.DictField(child=serializers.IntegerField())
    with_etymology = serializers.IntegerField()
    with_hint = serializers.IntegerField()
    with_sentences = serializers.IntegerField()
    total_cards = serializers.IntegerField()
    due_for_review = serializers.IntegerField()
```

### 4.4. Новый: `BulkActionRequestSerializer`

```python
class BulkActionRequestSerializer(serializers.Serializer):
    """Сериализатор для массовых действий"""
    
    word_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    action = serializers.ChoiceField(
        choices=[
            'enter_learning',
            'delete',
            'add_to_deck',
            'add_to_category',
            'remove_from_category'
        ]
    )
    params = serializers.DictField(required=False, default=dict)
```

### 4.5. Новый: `BulkActionResponseSerializer`

```python
class BulkActionResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа массовых действий"""
    
    action = serializers.CharField()
    processed = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.DictField()
    )
```

---

## 5. Django Signals для автоматического обновления статуса

**Файл:** `backend/apps/words/signals.py` (новый или обновить)

### 5.1. Signal для обновления статуса при изменении карточки

```python
@receiver(post_save, sender='cards.Card')
@receiver(post_delete, sender='cards.Card')
def update_word_status_on_card_change(sender, instance, **kwargs):
    """
    Обновляет learning_status слова при изменении его карточек.
    """
    from .utils import update_word_learning_status
    
    if instance.word:
        update_word_learning_status(instance.word)
```

---

## 6. Обновление URLs

**Файл:** `backend/apps/words/urls.py`

Добавить маршруты:
```python
urlpatterns = [
    # ... существующие маршруты ...
    
    # Обновление/удаление слова
    path('<int:word_id>/', views.word_update_view, name='word-update'),  # PATCH, DELETE
    
    # Статистика
    path('<int:word_id>/stats/', views.word_stats_view, name='word-stats'),
    path('stats/', views.words_stats_view, name='words-stats'),
    
    # Действия
    path('<int:word_id>/enter-learning/', views.word_enter_learning_view, name='word-enter-learning'),
    path('bulk-action/', views.words_bulk_action_view, name='words-bulk-action'),
]
```

---

## 7. Тесты

**Файл:** `backend/apps/words/tests.py`

### 7.1. Тесты для утилит

#### Тест 1: `test_get_word_learning_status_new`
- Слово без карточек → `'new'`

#### Тест 2: `test_get_word_learning_status_learning`
- Слово с карточкой в режиме изучения → `'learning'`

#### Тест 3: `test_get_word_learning_status_reviewing`
- Слово с карточкой на повторении → `'reviewing'`

#### Тест 4: `test_get_word_learning_status_mastered`
- Слово с освоенными карточками → `'mastered'`

#### Тест 5: `test_update_word_learning_status`
- Обновление статуса слова

#### Тест 6: `test_get_word_next_review`
- Получение ближайшей даты повторения

#### Тест 7: `test_get_word_cards_stats`
- Статистика по карточкам слова

### 7.2. Тесты для API

#### Тест 8: `test_words_list_filter_by_part_of_speech`
- Фильтрация по части речи

#### Тест 9: `test_words_list_filter_by_category`
- Фильтрация по категории

#### Тест 10: `test_words_list_filter_by_deck`
- Фильтрация по колоде

#### Тест 11: `test_words_list_sorting`
- Сортировка по разным полям

#### Тест 12: `test_words_list_pagination`
- Пагинация работает корректно

#### Тест 13: `test_word_update`
- Обновление слова через PATCH

#### Тест 14: `test_word_delete`
- Удаление слова

#### Тест 15: `test_word_stats`
- Статистика по слову

#### Тест 16: `test_words_stats`
- Общая статистика

#### Тест 17: `test_word_enter_learning`
- Отправка слова в режим изучения

#### Тест 18: `test_bulk_action_enter_learning`
- Массовая отправка в режим изучения

#### Тест 19: `test_bulk_action_delete`
- Массовое удаление

#### Тест 20: `test_bulk_action_add_to_deck`
- Массовое добавление в колоду

---

## 8. Интеграция с существующим кодом

### 8.1. Обновление `word_detail_view`

Добавить в ответ:
- Статистику по карточкам
- `next_review`
- Обновлённый `learning_status`

### 8.2. Обновление сигналов

При изменении карточки автоматически обновлять статус слова.

---

## 9. Оптимизация производительности

### 9.1. Использование `select_related` и `prefetch_related`

В `words_list_view`:
```python
words = words.select_related('user').prefetch_related(
    'categories',
    'decks',
    'cards'
)
```

### 9.2. Индексы БД

Убедиться, что есть индексы на:
- `user`, `learning_status`
- `user`, `part_of_speech`
- `user`, `language`
- `cards__word`, `cards__next_review`

---

## 10. Задачи реализации

### Приоритет 1 (Основной функционал)
- [ ] Создать `utils.py` с функциями определения статуса
- [ ] Обновить `words_list_view` с расширенной фильтрацией
- [ ] Добавить сортировку в `words_list_view`
- [ ] Добавить пагинацию в `words_list_view`
- [ ] Создать `word_update_view` (PATCH)
- [ ] Создать `word_delete_view` (DELETE)
- [ ] Создать `word_stats_view`
- [ ] Обновить сериализаторы

### Приоритет 2 (Дополнительный функционал)
- [ ] Создать `words_stats_view` (общая статистика)
- [ ] Создать `word_enter_learning_view`
- [ ] Создать `words_bulk_action_view`
- [ ] Добавить сигналы для автоматического обновления статуса
- [ ] Обновить `word_detail_view` с статистикой

### Приоритет 3 (Тесты и оптимизация)
- [ ] Unit-тесты для утилит (7 тестов)
- [ ] API тесты (13 тестов)
- [ ] Оптимизация запросов (select_related, prefetch_related)
- [ ] Проверка индексов БД

---

## 11. Критерии завершения

✅ Все функции утилит реализованы  
✅ `words_list_view` поддерживает расширенную фильтрацию и сортировку  
✅ Пагинация работает корректно  
✅ Эндпоинты для действий со словами реализованы  
✅ Статистика работает  
✅ Сигналы обновляют статус автоматически  
✅ Все тесты проходят (20+ тестов)  
✅ Оптимизация производительности выполнена  

---

## 12. Примеры использования

### Пример 1: Расширенная фильтрация

```
GET /api/words/list/?language=de&part_of_speech=noun&category_id=5&ordering=original_word&page=1&page_size=20
```

### Пример 2: Обновление слова

```
PATCH /api/words/123/
Body: {
  "notes": "Новая заметка",
  "part_of_speech": "noun"
}
```

### Пример 3: Статистика по слову

```
GET /api/words/123/stats/
Response: {
  "word_id": 123,
  "cards_stats": {...},
  "learning_status": "reviewing",
  ...
}
```

### Пример 4: Массовое действие

```
POST /api/words/bulk-action/
Body: {
  "word_ids": [1, 2, 3],
  "action": "enter_learning"
}
```

---

## 13. Примечания

1. **Статус обучения**: `learning_status` в модели Word может не совпадать с реальным статусом на основе карточек. Нужно либо обновлять его автоматически через сигналы, либо вычислять динамически в API.

2. **Производительность**: При большом количестве слов и карточек нужно оптимизировать запросы с помощью `select_related` и `prefetch_related`.

3. **Пагинация**: Использовать Django REST Framework пагинацию или реализовать свою.

4. **Валидация**: Все входные данные должны валидироваться через сериализаторы.

5. **Права доступа**: Все эндпоинты должны проверять, что пользователь имеет доступ только к своим словам.
