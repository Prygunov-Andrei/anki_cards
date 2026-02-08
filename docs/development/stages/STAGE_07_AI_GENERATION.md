# Этап 7: Генерация контента (AI) - Детальный план

## Цель этапа

Реализовать автоматическую генерацию контента для слов через AI:
- **Этимология** — происхождение слова
- **Подсказки** — текстовые и аудио подсказки (описание слова без перевода)
- **Предложения** — примеры использования слова
- **Синонимы** — генерация связанных слов

## Требования

1. Интеграция с системой токенов (списание за генерацию)
2. Использование существующей инфраструктуры LLM (OpenAI, Gemini)
3. Поддержка пользовательских промптов (как для изображений)
4. Обработка ошибок и валидация
5. Автоматическая генерация этимологии при создании слова
6. Генерация по запросу пользователя

---

## Архитектура

### Структура файлов

```
backend/apps/training/
├── ai_generation.py       # Основные функции генерации
├── prompts.py             # Промпты для генерации
├── tasks.py               # Celery задачи для асинхронной генерации (опционально)
└── signals.py             # Django signals для автоматической генерации
```

---

## 1. Файл: `backend/apps/training/ai_generation.py`

### 1.1. Функция: `generate_etymology()`

**Назначение:** Генерирует этимологию слова через AI

**Сигнатура:**
```python
def generate_etymology(
    word: str,
    translation: str,
    language: str,
    user: User,
    force_regenerate: bool = False
) -> str:
    """
    Генерирует этимологию слова через AI
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова (ru, en, de, es, fr, it, pt)
        user: Пользователь (для проверки баланса и пользовательского промпта)
        force_regenerate: Перегенерировать, даже если уже есть этимология
    
    Returns:
        Строка с этимологией
    
    Raises:
        ValueError: Недостаточно токенов или неверные параметры
        Exception: Ошибка при вызове AI API
    """
```

**Логика:**
1. Проверка баланса токенов (`check_balance()`)
2. Получение промпта (пользовательский или дефолтный)
3. Вызов LLM API (OpenAI GPT-4o-mini для текста)
4. Парсинг ответа
5. Списание токенов (`spend_tokens()`)
6. Возврат результата

**Стоимость:** 1 токен

**Модель:** `gpt-4o-mini` (дешевая модель для текста)

---

### 1.2. Функция: `generate_hint()`

**Назначение:** Генерирует текстовую и аудио подсказку

**Сигнатура:**
```python
def generate_hint(
    word: str,
    translation: str,
    language: str,
    user: User,
    force_regenerate: bool = False
) -> Tuple[str, Optional[str]]:
    """
    Генерирует текстовую и аудио подсказку
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова
        user: Пользователь
        force_regenerate: Перегенерировать, даже если уже есть подсказка
    
    Returns:
        Tuple[строка с текстовой подсказкой, путь к аудио файлу или None]
    
    Raises:
        ValueError: Недостаточно токенов
        Exception: Ошибка при генерации
    """
```

**Логика:**
1. Проверка баланса (стоимость: 1 токен за текст + 1 токен за аудио = 2 токена)
2. Генерация текстовой подсказки через LLM
3. Генерация аудио через TTS (используя существующую функцию `generate_audio_with_tts()`)
4. Списание токенов
5. Сохранение аудио файла
6. Возврат результата

**Стоимость:** 
- Текстовая подсказка: 1 токен
- Аудио подсказка: 1 токен
- **Итого: 2 токена**

**Модели:**
- Текст: `gpt-4o-mini`
- Аудио: `tts-1-hd` (OpenAI) или `gTTS` (бесплатно, но требует интернет)

**Пример подсказки:**
- Слово: "Hund" (собака)
- Подсказка (на немецком): "Ein Tier mit vier Beinen, das oft als Haustier gehalten wird und als bester Freund des Menschen gilt."

---

### 1.3. Функция: `generate_sentence()`

**Назначение:** Генерирует пример предложения с использованием слова

**Сигнатура:**
```python
def generate_sentence(
    word: str,
    translation: str,
    language: str,
    user: User,
    context: Optional[str] = None,
    count: int = 1
) -> Union[str, List[str]]:
    """
    Генерирует пример(ы) предложения с использованием слова
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова
        user: Пользователь
        context: Дополнительный контекст (например, "формальное общение", "разговорная речь")
        count: Количество предложений (1-5)
    
    Returns:
        Если count=1: строка с предложением
        Если count>1: список строк с предложениями
    
    Raises:
        ValueError: Недостаточно токенов или неверный count
        Exception: Ошибка при генерации
    """
```

**Логика:**
1. Проверка баланса (стоимость: 0.5 токена за предложение, минимум 1 токен)
2. Получение промпта с учетом контекста
3. Вызов LLM API
4. Парсинг ответа (может быть несколько предложений)
5. Валидация (предложение должно содержать слово)
6. Списание токенов
7. Возврат результата

**Стоимость:** 
- 1 предложение: 1 токен
- 2-5 предложений: 1 токен (пакетная генерация)

**Модель:** `gpt-4o-mini`

**Пример:**
- Слово: "Haus" (дом)
- Предложение: "Ich wohne in einem großen Haus mit einem Garten."

---

### 1.4. Функция: `generate_synonym_word()`

**Назначение:** Создаёт новое слово-синоним

**Сигнатура:**
```python
def generate_synonym_word(
    word: Word,
    user: User,
    create_card: bool = True
) -> Word:
    """
    Генерирует и создаёт новое слово-синоним
    
    Args:
        word: Исходное слово
        user: Пользователь
        create_card: Создать автоматически normal карточку для нового слова
    
    Returns:
        Объект Word (новое слово-синоним)
    
    Raises:
        ValueError: Недостаточно токенов или слово уже существует
        Exception: Ошибка при генерации
    
    Note:
        Автоматически создаёт двустороннюю связь через WordRelation
    """
```

**Логика:**
1. Проверка баланса (стоимость: 1 токен)
2. Генерация синонима через LLM (должен быть на том же языке)
3. Проверка, что слово не существует у пользователя
4. Создание нового объекта Word
5. Автоматическая генерация этимологии (если включена)
6. Создание двусторонней связи через `WordRelation.create_bidirectional()`
7. Создание normal карточки (если `create_card=True`)
8. Списание токенов
9. Возврат нового слова

**Стоимость:** 1 токен

**Модель:** `gpt-4o-mini`

**Пример:**
- Исходное слово: "Haus" (дом) → перевод: "дом"
- Генерированный синоним: "Gebäude" (дом, здание) → перевод: "здание"

---

## 2. Файл: `backend/apps/training/prompts.py`

### 2.1. Дефолтные промпты

```python
# Дефолтные промпты для генерации контента

DEFAULT_ETYMOLOGY_PROMPT = """Erkläre die Herkunft und Bedeutung des Wortes '{word}' ({language}).
Bitte gib eine kurze, aber informative Erklärung (2-3 Sätze).
Übersetzung des Wortes: {translation}"""

DEFAULT_HINT_PROMPT = """Erstelle eine Hinweis für das Wort '{word}' auf {language}.
Der Hinweis sollte das Wort beschreiben, OHNE das Wort oder seine Übersetzung zu erwähnen.
Beschreibung sollte 1-2 Sätze lang sein und auf {language} sein.
Übersetzung des Wortes (nur für Kontext): {translation}

Beispiel für "Hund":
"Ein Tier mit vier Beinen, das oft als Haustier gehalten wird.""""

DEFAULT_SENTENCE_PROMPT = """Erstelle {count} Beispielsatz(ätze) mit dem Wort '{word}' auf {language}.
Die Sätze sollten natürlich und alltäglich sein.
Kontext: {context}

Format: Ein Satz pro Zeile."""

DEFAULT_SYNONYM_PROMPT = """Finde ein Synonym für das Wort '{word}' ({language}).
Das Synonym sollte:
1. Auf dem gleichen {language} sein
2. Eine ähnliche, aber не идентичная Bedeutung haben
3. Ein gängiges Wort sein

Aktuelles Wort: {word}
Übersetzung: {translation}

Antworte im Format: Synonym|Übersetzung_синонима
Beispiel: Gebäude|здание"""
```

### 2.2. Функция получения промптов

```python
def get_etymology_prompt(user: Optional[User] = None) -> str:
    """Получает промпт для генерации этимологии"""
    # Используем систему пользовательских промптов (аналогично изображениям)
    # Если пользовательский промпт не найден, используем дефолтный
    ...

def get_hint_prompt(user: Optional[User] = None) -> str:
    """Получает промпт для генерации подсказки"""
    ...

def get_sentence_prompt(user: Optional[User] = None) -> str:
    """Получает промпт для генерации предложения"""
    ...

def get_synonym_prompt(user: Optional[User] = None) -> str:
    """Получает промпт для генерации синонима"""
    ...
```

---

## 3. API эндпоинты

### 3.1. `POST /api/training/generate-etymology/`

**Назначение:** Генерация этимологии для слова

**Request:**
```json
{
  "word_id": 123,
  "force_regenerate": false
}
```

**Response:**
```json
{
  "word_id": 123,
  "etymology": "Das Wort 'Haus' stammt vom...",
  "tokens_spent": 1,
  "balance_after": 99
}
```

**Ошибки:**
- `400`: Недостаточно токенов или неверные параметры
- `404`: Слово не найдено
- `500`: Ошибка при генерации

---

### 3.2. `POST /api/training/generate-hint/`

**Назначение:** Генерация подсказки (текст + аудио)

**Request:**
```json
{
  "word_id": 123,
  "force_regenerate": false,
  "generate_audio": true
}
```

**Response:**
```json
{
  "word_id": 123,
  "hint_text": "Ein Tier mit vier Beinen...",
  "hint_audio_url": "/media/hints/hint_123_abc.mp3",
  "tokens_spent": 2,
  "balance_after": 98
}
```

---

### 3.3. `POST /api/training/generate-sentence/`

**Назначение:** Генерация примеров предложений

**Request:**
```json
{
  "word_id": 123,
  "count": 3,
  "context": "формальное общение"
}
```

**Response:**
```json
{
  "word_id": 123,
  "sentences": [
    "Ich wohne in einem großen Haus.",
    "Das Haus hat drei Stockwerke.",
    "Wir haben gestern das Haus gekauft."
  ],
  "tokens_spent": 1,
  "balance_after": 99
}
```

**Note:** Предложения добавляются в `word.sentences` с `source: "ai"`

---

### 3.4. `POST /api/training/generate-synonym/`

**Назначение:** Генерация синонима

**Request:**
```json
{
  "word_id": 123,
  "create_card": true
}
```

**Response:**
```json
{
  "original_word_id": 123,
  "synonym_word": {
    "id": 124,
    "original_word": "Gebäude",
    "translation": "здание",
    "language": "de",
    "etymology": "...",
    ...
  },
  "relation_created": true,
  "tokens_spent": 1,
  "balance_after": 99
}
```

---

## 4. Django Signals для автоматической генерации

### 4.1. `post_save` signal для Word

**Файл:** `backend/apps/training/signals.py`

```python
@receiver(post_save, sender=Word)
def auto_generate_etymology(sender, instance: Word, created: bool, **kwargs):
    """
    Автоматически генерирует этимологию при создании нового слова
    
    Условия:
    - Слово только что создано (created=True)
    - У пользователя достаточно токенов (>= 1)
    - Этимология ещё не заполнена
    - Пользователь не отключил автоматическую генерацию (опционально)
    """
    if not created:
        return
    
    if instance.etymology:
        return  # Этимология уже есть
    
    # Проверка баланса
    from apps.cards.token_utils import check_balance
    balance = check_balance(instance.user)
    if balance < 2:  # Минимум 2 единицы = 1 токен
        logger.info(f"Недостаточно токенов для автоматической генерации этимологии для слова {instance.id}")
        return
    
    try:
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from .ai_generation import generate_etymology
        
        etymology = generate_etymology(
            word=instance.original_word,
            translation=instance.translation,
            language=instance.language,
            user=instance.user
        )
        
        instance.etymology = etymology
        instance.save(update_fields=['etymology'])
        
        logger.info(f"✅ Автоматически сгенерирована этимология для слова {instance.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при автоматической генерации этимологии: {e}")
        # Не выбрасываем исключение, чтобы не сломать создание слова
```

---

## 5. Интеграция с существующим кодом

### 5.1. Использование существующих утилит

- `apps.cards.token_utils.check_balance()` — проверка баланса
- `apps.cards.token_utils.spend_tokens()` — списание токенов
- `apps.cards.llm_utils.get_openai_client()` — клиент OpenAI
- `apps.cards.llm_utils.generate_audio_with_tts()` — генерация аудио
- `apps.cards.prompt_utils.get_user_prompt()` — получение пользовательских промптов

### 5.2. Обновление модели Word

Модель уже имеет необходимые поля:
- `etymology` — TextField
- `hint_text` — TextField
- `hint_audio` — FileField
- `sentences` — JSONField

### 5.3. Обновление сериализаторов

**Файл:** `backend/apps/words/serializers.py` (если есть)

Добавить поля для API ответов:
- `etymology`
- `hint_text`
- `hint_audio_url`
- `sentences`

---

## 6. Тесты

### 6.1. Unit-тесты для `ai_generation.py`

**Файл:** `backend/apps/training/tests.py`

#### Тест 1: `test_generate_etymology_success`
- Создать пользователя с достаточным балансом
- Вызвать `generate_etymology()`
- Проверить, что этимология сгенерирована
- Проверить списание токенов

#### Тест 2: `test_generate_etymology_insufficient_balance`
- Создать пользователя без токенов
- Вызвать `generate_etymology()`
- Проверить, что выбрасывается `ValueError`

#### Тест 3: `test_generate_hint_with_audio`
- Создать слово
- Вызвать `generate_hint()`
- Проверить текстовую подсказку
- Проверить создание аудио файла
- Проверить списание 2 токенов

#### Тест 4: `test_generate_sentence_single`
- Вызвать `generate_sentence(count=1)`
- Проверить, что возвращается строка
- Проверить, что предложение содержит слово

#### Тест 5: `test_generate_sentence_multiple`
- Вызвать `generate_sentence(count=3)`
- Проверить, что возвращается список из 3 предложений

#### Тест 6: `test_generate_synonym_word`
- Создать исходное слово
- Вызвать `generate_synonym_word()`
- Проверить создание нового слова
- Проверить создание двусторонней связи
- Проверить создание normal карточки

#### Тест 7: `test_generate_synonym_duplicate_prevention`
- Создать слово
- Попытаться сгенерировать синоним, который уже существует
- Проверить обработку ошибки

#### Тест 8: `test_auto_generate_etymology_signal`
- Создать новое слово
- Проверить, что этимология автоматически сгенерирована
- Проверить, что токены списаны

### 6.2. API тесты

#### Тест 9: `test_generate_etymology_api`
- `POST /api/training/generate-etymology/`
- Проверить успешный ответ
- Проверить обновление `word.etymology`

#### Тест 10: `test_generate_hint_api`
- `POST /api/training/generate-hint/`
- Проверить генерацию текста и аудио

#### Тест 11: `test_generate_sentence_api`
- `POST /api/training/generate-sentence/`
- Проверить добавление предложений в `word.sentences`

#### Тест 12: `test_generate_synonym_api`
- `POST /api/training/generate-synonym/`
- Проверить создание нового слова и связи

---

## 7. Стоимость операций

| Операция | Токены | Примечание |
|----------|--------|------------|
| Этимология | 1 | Автоматически при создании слова |
| Текстовая подсказка | 1 | По запросу пользователя |
| Аудио подсказка | 1 | По запросу пользователя |
| Подсказка (текст + аудио) | 2 | Комбинированная операция |
| Предложение (1-5 шт.) | 1 | Пакетная генерация |
| Синоним | 1 | + автоматическая этимология (+1 токен) |

**Итого при создании слова с полным контентом:**
- Этимология (авто): 1 токен
- Подсказка (текст + аудио): 2 токена
- 3 предложения: 1 токен
- **Итого: 4 токена** (если всё сгенерировать)

---

## 8. Задачи реализации

### Приоритет 1 (Основной функционал)
- [ ] Реализация `generate_etymology()`
- [ ] Реализация `generate_hint()` (только текст)
- [ ] Реализация `generate_sentence()`
- [ ] Дефолтные промпты
- [ ] Интеграция с системой токенов
- [ ] Базовые тесты (5 тестов)

### Приоритет 2 (Дополнительный функционал)
- [ ] Реализация `generate_synonym_word()`
- [ ] API эндпоинты (4 эндпоинта)
- [ ] Автоматическая генерация этимологии через signals
- [ ] Генерация аудио для подсказок
- [ ] API тесты (4 теста)

### Приоритет 3 (Оптимизация)
- [ ] Поддержка пользовательских промптов
- [ ] Асинхронная генерация через Celery (опционально)
- [ ] Кэширование результатов (опционально)
- [ ] Обработка ошибок и retry логика

---

## 9. Примеры использования

### Пример 1: Автоматическая генерация этимологии

```python
# При создании слова через Django admin или API
word = Word.objects.create(
    user=user,
    original_word="Haus",
    translation="дом",
    language="de"
)
# Signal автоматически генерирует этимологию
# word.etymology будет заполнена автоматически
```

### Пример 2: Генерация подсказки по запросу

```python
from apps.training.ai_generation import generate_hint

hint_text, hint_audio_path = generate_hint(
    word="Hund",
    translation="собака",
    language="de",
    user=user
)

word.hint_text = hint_text
word.hint_audio = hint_audio_path
word.save()
```

### Пример 3: Генерация предложений

```python
from apps.training.ai_generation import generate_sentence

sentences = generate_sentence(
    word="Haus",
    translation="дом",
    language="de",
    user=user,
    count=3
)

for sentence in sentences:
    word.add_sentence(sentence, source='ai')
```

---

## 10. Потенциальные проблемы и решения

### Проблема 1: Медленная генерация

**Решение:**
- Использовать более быстрые модели (`gpt-4o-mini` вместо `gpt-4`)
- Асинхронная генерация через Celery для больших объёмов

### Проблема 2: Некачественные результаты

**Решение:**
- Улучшение промптов на основе тестирования
- Поддержка пользовательских промптов

### Проблема 3: Высокая стоимость

**Решение:**
- Использовать дешевые модели для простых задач
- Пакетная генерация предложений

### Проблема 4: Ошибки API

**Решение:**
- Retry логика с экспоненциальной задержкой
- Graceful degradation (возврат пустого результата вместо ошибки)

---

## 11. Критерии завершения этапа

✅ Все функции реализованы (`generate_etymology`, `generate_hint`, `generate_sentence`, `generate_synonym_word`)  
✅ API эндпоинты реализованы и работают  
✅ Интеграция с системой токенов работает корректно  
✅ Автоматическая генерация этимологии через signals работает  
✅ Все тесты проходят (12+ тестов)  
✅ Обработка ошибок реализована  
✅ Промпты протестированы и дают качественные результаты  

---

## Примечания

1. **Языки промптов**: Промпты должны быть многоязычными или определять язык автоматически
2. **Валидация**: Проверять, что сгенерированный контент соответствует требованиям (например, предложение содержит слово)
3. **Безопасность**: Валидировать входные данные, предотвращать injection через промпты
4. **Логирование**: Логировать все операции генерации для отладки
5. **Мониторинг**: Отслеживать успешность генерации и качество результатов
