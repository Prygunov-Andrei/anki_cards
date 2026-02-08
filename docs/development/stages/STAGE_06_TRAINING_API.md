# Этап 6: API для тренировки

## Цель
Реализация API эндпоинтов для проведения тренировочных сессий, включая формирование очереди карточек, обработку ответов, управление режимом изучения и статистику.

## Обзор

Этап 6 реализует API для тренировки, который:
- Формирует очередь карточек для сессии с учётом фильтров (колода, время, новые карточки)
- Обрабатывает ответы пользователя через SM2Algorithm
- Управляет режимом изучения (вход/выход)
- Предоставляет статистику тренировок
- Интегрируется с существующими моделями (Card, Deck, Word, UserTrainingSettings)

## Структура файлов

```
backend/apps/training/
├── views.py            # API views (расширение существующего)
├── serializers.py      # Сериализаторы для API (расширение существующего)
├── urls.py             # URL-маршруты (расширение существующего)
├── session_utils.py    # Утилиты для формирования очереди карточек
└── stats_utils.py      # Утилиты для статистики (опционально)
```

## Детальная спецификация

### 1. Формирование очереди карточек

#### 1.1. Логика приоритизации

**Приоритеты карточек (в порядке показа):**

1. **Карточки в режиме обучения** (`is_in_learning_mode=True`)
   - Показываются первыми, так как требуют быстрого закрепления
   - Сортировка: по `next_review` (ASC), затем по `learning_step` (ASC)

2. **Карточки на повторение** (`due_for_review`)
   - Показываются вторыми, так как уже просрочены или готовы к повторению
   - Сортировка: по `next_review` (ASC) - самые просроченные первыми

3. **Новые карточки** (если `new_cards=True`)
   - Показываются последними, если есть время
   - Сортировка: по `created_at` (ASC) - самые старые новые карточки первыми

#### 1.2. Ограничение по времени

**Расчёт количества карточек:**

- **Время на карточку:**
  - В режиме обучения: ~2-3 минуты (с учётом повторов)
  - На повторение: ~10-20 секунд
  - Новая карточка: ~2-3 минуты (с учётом обучения)

- **Формула:**
  ```
  max_cards = duration_minutes / avg_time_per_card
  ```
  
  Где `avg_time_per_card` зависит от типа карточек:
  - Если есть карточки в режиме обучения: 2.5 минуты
  - Если только повторения: 0.25 минуты
  - Если смешанные: взвешенное среднее

#### 1.3. Фильтрация по колоде

- Если `deck_id` указан:
  - Фильтруем карточки через `Card.objects.by_deck(deck)`
  - Проверяем, что колода принадлежит пользователю

- Если `deck_id` не указан:
  - Берём все карточки пользователя

#### 1.4. Функция формирования очереди

```python
def build_card_queue(
    user: User,
    deck_id: Optional[int] = None,
    duration_minutes: int = 20,
    include_new_cards: bool = True,
    settings: UserTrainingSettings = None
) -> Dict:
    """
    Формирует очередь карточек для тренировочной сессии.
    
    Args:
        user: Пользователь
        deck_id: ID колоды (опционально)
        duration_minutes: Длительность сессии в минутах
        include_new_cards: Включать ли новые карточки
        settings: Настройки тренировки (если None, получаем автоматически)
    
    Returns:
        dict:
        {
            'cards': List[Card],
            'new_count': int,
            'review_count': int,
            'learning_count': int,
            'estimated_time': int (минуты),
            'total_count': int
        }
    """
```

**Алгоритм:**

1. Получаем настройки пользователя (если не переданы)
2. Фильтруем карточки по колоде (если указана)
3. Разделяем карточки на категории:
   - `learning_cards`: `Card.objects.in_learning(user)`
   - `review_cards`: `Card.objects.due_for_review(user)`
   - `new_cards`: новые карточки (если `include_new_cards=True`)
4. Сортируем каждую категорию
5. Ограничиваем общее количество по времени
6. Формируем финальную очередь: learning → review → new

### 2. API Эндпоинты

#### 2.1. GET /api/training/session/

**Назначение:** Получить карточки для тренировочной сессии

**Query параметры:**
- `deck_id` (int, опционально): ID колоды для фильтрации
- `duration` (int, опционально): Длительность сессии в минутах (по умолчанию из `settings.default_session_duration`)
- `new_cards` (bool, опционально): Включать новые карточки (по умолчанию `true`)

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "cards": [
    {
      "id": 123,
      "word": 45,
      "card_type": "normal",
      "word_original_word": "Haus",
      "word_translation": "дом",
      "word_language": "de",
      "is_in_learning_mode": true,
      "learning_step": 0,
      "front_content": {...},
      "back_content": {...}
    },
    ...
  ],
  "estimated_time": 20,
  "new_count": 5,
  "review_count": 15,
  "learning_count": 3,
  "total_count": 23
}
```

**Логика:**
1. Валидация параметров
2. Получение настроек пользователя
3. Вызов `build_card_queue()`
4. Генерация `session_id` (UUID)
5. Сериализация карточек
6. Возврат ответа

**Ошибки:**
- `400`: Невалидные параметры (duration < 1, deck_id не существует)
- `404`: Колода не найдена или не принадлежит пользователю

#### 2.2. POST /api/training/answer/

**Назначение:** Обработать ответ пользователя на карточку

**Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "card_id": 123,
  "answer": 2,  // 0=Again, 1=Hard, 2=Good, 3=Easy
  "time_spent": 5.2  // Секунды на ответ (опционально)
}
```

**Response:**
```json
{
  "card_id": 123,
  "new_interval": 4,
  "new_ease_factor": 2.5,
  "next_review": "2026-01-13T10:30:00Z",
  "entered_learning_mode": false,
  "exited_learning_mode": false,
  "learning_step": -1,
  "calibrated": false,
  "card": {
    // Полная информация о карточке после обработки
  }
}
```

**Логика:**
1. Валидация данных (card_id, answer в диапазоне 0-3)
2. Получение карточки (проверка принадлежности пользователю)
3. Получение настроек пользователя
4. Вызов `SM2Algorithm.process_answer(card, answer, settings, time_spent)`
5. Сериализация результата
6. Возврат ответа

**Ошибки:**
- `400`: Невалидные данные (answer не в диапазоне, card_id отсутствует)
- `404`: Карточка не найдена или не принадлежит пользователю

**Примечания:**
- `session_id` используется для логирования, но не обязателен для работы
- `time_spent` опционален, но может использоваться для статистики

#### 2.3. POST /api/training/enter-learning/

**Назначение:** Перевести карточку в режим изучения вручную

**Body:**
```json
{
  "card_id": 123
}
```

**Response:**
```json
{
  "card_id": 123,
  "message": "Карточка переведена в режим изучения",
  "card": {
    // Полная информация о карточке
  }
}
```

**Логика:**
1. Получение карточки
2. Вызов `card.enter_learning_mode()`
3. Сохранение карточки
4. Возврат ответа

#### 2.4. POST /api/training/exit-learning/

**Назначение:** Вывести карточку из режима изучения вручную

**Body:**
```json
{
  "card_id": 123
}
```

**Response:**
```json
{
  "card_id": 123,
  "message": "Карточка выведена из режима изучения",
  "card": {
    // Полная информация о карточке
  }
}
```

**Логика:**
1. Получение карточки
2. Вызов `card.exit_learning_mode()`
3. Сохранение карточки
4. Возврат ответа

#### 2.5. GET /api/training/stats/

**Назначение:** Получить статистику тренировок

**Query параметры:**
- `period` (str, опционально): Период статистики (`"day"`, `"week"`, `"month"`, `"all"`, по умолчанию `"all"`)

**Response:**
```json
{
  "period": "all",
  "total_reviews": 150,
  "successful_reviews": 130,
  "success_rate": 0.87,
  "streak_days": 5,
  "cards_by_status": {
    "new": 10,
    "learning": 5,
    "review": 25,
    "mastered": 100
  },
  "reviews_by_day": [
    {
      "date": "2026-01-13",
      "total": 20,
      "successful": 18,
      "success_rate": 0.9
    },
    ...
  ],
  "average_time_per_card": 12.5,  // Секунды
  "total_time_spent": 1800  // Секунды
}
```

**Логика:**
1. Определение периода (start_date, end_date)
2. Получение всех карточек пользователя
3. Подсчёт статистики:
   - Общее количество ответов за период
   - Успешные ответы (Good/Easy)
   - Процент успеха
   - Streak (дни подряд с тренировками)
   - Распределение карточек по статусам
   - Статистика по дням
4. Возврат ответа

**Определение статусов карточек:**
- `new`: `is_in_learning_mode=True` и `repetitions=0` и `interval=0`
- `learning`: `is_in_learning_mode=True` и не new
- `review`: `is_in_learning_mode=False` и `next_review <= now`
- `mastered`: `is_in_learning_mode=False` и `next_review > now` и `interval >= 30` дней

**Streak (дни подряд):**
- Подсчитывается по `last_review` карточек
- День считается активным, если была хотя бы одна тренировка
- Streak прерывается, если нет тренировок в течение дня

### 3. Сериализаторы

#### 3.1. TrainingSessionSerializer

```python
class TrainingSessionSerializer(serializers.Serializer):
    """Сериализатор для ответа GET /api/training/session/"""
    session_id = serializers.UUIDField()
    cards = CardListSerializer(many=True)
    estimated_time = serializers.IntegerField()
    new_count = serializers.IntegerField()
    review_count = serializers.IntegerField()
    learning_count = serializers.IntegerField()
    total_count = serializers.IntegerField()
```

#### 3.2. TrainingAnswerRequestSerializer

```python
class TrainingAnswerRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса POST /api/training/answer/"""
    session_id = serializers.UUIDField(required=False)
    card_id = serializers.IntegerField(required=True)
    answer = serializers.IntegerField(min_value=0, max_value=3, required=True)
    time_spent = serializers.FloatField(required=False, min_value=0)
```

#### 3.3. TrainingAnswerResponseSerializer

```python
class TrainingAnswerResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа POST /api/training/answer/"""
    card_id = serializers.IntegerField()
    new_interval = serializers.IntegerField()
    new_ease_factor = serializers.FloatField()
    next_review = serializers.DateTimeField()
    entered_learning_mode = serializers.BooleanField()
    exited_learning_mode = serializers.BooleanField()
    learning_step = serializers.IntegerField()
    calibrated = serializers.BooleanField()
    card = CardSerializer()
```

#### 3.4. CardActionRequestSerializer

```python
class CardActionRequestSerializer(serializers.Serializer):
    """Базовый сериализатор для enter-learning/exit-learning"""
    card_id = serializers.IntegerField(required=True)
```

#### 3.5. CardActionResponseSerializer

```python
class CardActionResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа enter-learning/exit-learning"""
    card_id = serializers.IntegerField()
    message = serializers.CharField()
    card = CardSerializer()
```

#### 3.6. TrainingStatsSerializer

```python
class ReviewDayStatsSerializer(serializers.Serializer):
    """Статистика за день"""
    date = serializers.DateField()
    total = serializers.IntegerField()
    successful = serializers.IntegerField()
    success_rate = serializers.FloatField()

class TrainingStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики"""
    period = serializers.CharField()
    total_reviews = serializers.IntegerField()
    successful_reviews = serializers.IntegerField()
    success_rate = serializers.FloatField()
    streak_days = serializers.IntegerField()
    cards_by_status = serializers.DictField()
    reviews_by_day = ReviewDayStatsSerializer(many=True)
    average_time_per_card = serializers.FloatField()
    total_time_spent = serializers.IntegerField()
```

### 4. Views

#### 4.1. training_session_view

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_session_view(request):
    """
    GET /api/training/session/
    Получить карточки для тренировочной сессии
    """
```

**Логика:**
1. Извлечение query параметров
2. Валидация параметров
3. Получение настроек пользователя
4. Вызов `build_card_queue()`
5. Генерация session_id
6. Сериализация ответа
7. Возврат Response

#### 4.2. training_answer_view

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_answer_view(request):
    """
    POST /api/training/answer/
    Обработать ответ пользователя
    """
```

**Логика:**
1. Валидация данных запроса
2. Получение карточки
3. Получение настроек
4. Вызов `SM2Algorithm.process_answer()`
5. Сериализация результата
6. Возврат Response

#### 4.3. training_enter_learning_view

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_enter_learning_view(request):
    """
    POST /api/training/enter-learning/
    Перевести карточку в режим изучения
    """
```

#### 4.4. training_exit_learning_view

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_exit_learning_view(request):
    """
    POST /api/training/exit-learning/
    Вывести карточку из режима изучения
    """
```

#### 4.5. training_stats_view

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_stats_view(request):
    """
    GET /api/training/stats/
    Получить статистику тренировок
    """
```

**Логика:**
1. Извлечение query параметров
2. Определение периода
3. Подсчёт статистики
4. Сериализация ответа
5. Возврат Response

### 5. Утилиты

#### 5.1. session_utils.py

```python
def build_card_queue(
    user: User,
    deck_id: Optional[int] = None,
    duration_minutes: int = 20,
    include_new_cards: bool = True,
    settings: Optional[UserTrainingSettings] = None
) -> Dict:
    """Формирует очередь карточек для сессии"""

def estimate_session_time(
    learning_count: int,
    review_count: int,
    new_count: int
) -> int:
    """
    Оценивает время сессии в минутах.
    
    Args:
        learning_count: Количество карточек в режиме обучения
        review_count: Количество карточек на повторение
        new_count: Количество новых карточек
    
    Returns:
        int: Оценка времени в минутах
    """
    # learning: 2.5 мин, review: 0.25 мин, new: 2.5 мин
    return int(
        learning_count * 2.5 +
        review_count * 0.25 +
        new_count * 2.5
    )

def limit_cards_by_time(
    cards: List[Card],
    duration_minutes: int,
    learning_count: int,
    review_count: int,
    new_count: int
) -> List[Card]:
    """
    Ограничивает количество карточек по времени.
    
    Возвращает подмножество карточек, которое помещается в указанное время.
    """
```

#### 5.2. stats_utils.py (опционально)

```python
def calculate_training_stats(
    user: User,
    period: str = 'all'
) -> Dict:
    """
    Подсчитывает статистику тренировок за период.
    
    Args:
        user: Пользователь
        period: 'day', 'week', 'month', 'all'
    
    Returns:
        dict с статистикой
    """

def calculate_streak_days(
    user: User
) -> int:
    """
    Подсчитывает количество дней подряд с тренировками.
    
    Returns:
        int: Количество дней streak
    """

def get_cards_by_status(
    user: User
) -> Dict[str, int]:
    """
    Возвращает распределение карточек по статусам.
    
    Returns:
        dict: {'new': int, 'learning': int, 'review': int, 'mastered': int}
    """
```

### 6. URL-маршруты

```python
# backend/apps/training/urls.py

urlpatterns = [
    # ... существующие маршруты ...
    
    # ЭТАП 6: Training API
    path('session/', views.training_session_view, name='training-session'),
    path('answer/', views.training_answer_view, name='training-answer'),
    path('enter-learning/', views.training_enter_learning_view, name='training-enter-learning'),
    path('exit-learning/', views.training_exit_learning_view, name='training-exit-learning'),
    path('stats/', views.training_stats_view, name='training-stats'),
]
```

### 7. Тестирование

#### 7.1. Тесты для session_utils

- [ ] `test_build_card_queue_all_cards` - все карточки пользователя
- [ ] `test_build_card_queue_by_deck` - фильтрация по колоде
- [ ] `test_build_card_queue_prioritization` - правильный порядок (learning → review → new)
- [ ] `test_build_card_queue_time_limit` - ограничение по времени
- [ ] `test_build_card_queue_exclude_new` - исключение новых карточек
- [ ] `test_estimate_session_time` - оценка времени
- [ ] `test_limit_cards_by_time` - ограничение карточек

#### 7.2. Тесты для API эндпоинтов

**GET /api/training/session/:**
- [ ] `test_get_session_all_cards` - получение всех карточек
- [ ] `test_get_session_by_deck` - фильтрация по колоде
- [ ] `test_get_session_custom_duration` - кастомная длительность
- [ ] `test_get_session_exclude_new` - исключение новых карточек
- [ ] `test_get_session_invalid_deck` - невалидная колода
- [ ] `test_get_session_empty_queue` - пустая очередь

**POST /api/training/answer/:**
- [ ] `test_answer_again` - обработка Again
- [ ] `test_answer_hard` - обработка Hard
- [ ] `test_answer_good` - обработка Good
- [ ] `test_answer_easy` - обработка Easy
- [ ] `test_answer_invalid_card` - невалидная карточка
- [ ] `test_answer_invalid_answer` - невалидный ответ (не 0-3)
- [ ] `test_answer_with_time_spent` - с указанием времени
- [ ] `test_answer_calibration_trigger` - срабатывание калибровки

**POST /api/training/enter-learning/:**
- [ ] `test_enter_learning_mode` - перевод в режим изучения
- [ ] `test_enter_learning_already_in` - уже в режиме изучения
- [ ] `test_enter_learning_invalid_card` - невалидная карточка

**POST /api/training/exit-learning/:**
- [ ] `test_exit_learning_mode` - вывод из режима изучения
- [ ] `test_exit_learning_not_in` - не в режиме изучения
- [ ] `test_exit_learning_invalid_card` - невалидная карточка

**GET /api/training/stats/:**
- [ ] `test_stats_all_period` - статистика за весь период
- [ ] `test_stats_day_period` - статистика за день
- [ ] `test_stats_week_period` - статистика за неделю
- [ ] `test_stats_month_period` - статистика за месяц
- [ ] `test_stats_cards_by_status` - распределение по статусам
- [ ] `test_stats_streak_days` - подсчёт streak
- [ ] `test_stats_reviews_by_day` - статистика по дням

**Минимальное количество тестов: 30+**

### 8. Интеграция с существующими компонентами

#### 8.1. CardManager

Используем существующие методы:
- `Card.objects.for_user(user)` - все карточки пользователя
- `Card.objects.due_for_review(user)` - карточки на повторение
- `Card.objects.in_learning(user)` - карточки в режиме обучения
- `Card.objects.by_deck(deck)` - карточки из колоды

#### 8.2. SM2Algorithm

Используем:
- `SM2Algorithm.process_answer(card, answer, settings, time_spent)` - обработка ответа

#### 8.3. UserTrainingSettings

Используем:
- `settings.default_session_duration` - длительность сессии по умолчанию
- `settings.record_review()` - запись статистики (уже в SM2Algorithm)

#### 8.4. Card методы

Используем:
- `card.enter_learning_mode()` - вход в режим изучения
- `card.exit_learning_mode()` - выход из режима изучения

### 9. Задачи реализации

- [ ] Создать файл `backend/apps/training/session_utils.py`
- [ ] Реализовать функцию `build_card_queue()`
- [ ] Реализовать функцию `estimate_session_time()`
- [ ] Реализовать функцию `limit_cards_by_time()`
- [ ] Создать сериализаторы для API
- [ ] Реализовать view `training_session_view`
- [ ] Реализовать view `training_answer_view`
- [ ] Реализовать view `training_enter_learning_view`
- [ ] Реализовать view `training_exit_learning_view`
- [ ] Реализовать view `training_stats_view`
- [ ] Создать функцию `calculate_training_stats()` (или встроить в view)
- [ ] Создать функцию `calculate_streak_days()`
- [ ] Создать функцию `get_cards_by_status()`
- [ ] Добавить URL-маршруты
- [ ] Написать тесты для session_utils (7+ тестов)
- [ ] Написать тесты для API (25+ тестов)
- [ ] Проверить все тесты

### 10. Критерии готовности

✅ Все эндпоинты реализованы  
✅ Формирование очереди работает корректно  
✅ Приоритизация карточек правильная  
✅ Ограничение по времени работает  
✅ Интеграция с SM2Algorithm работает  
✅ Статистика подсчитывается правильно  
✅ Все тесты проходят (30+ тестов)  
✅ Код покрыт комментариями  
✅ Нет захардкоженных значений (кроме констант времени)

### 11. Примечания

- **Session ID**: Генерируется на фронтенде или бэкенде, используется для логирования, но не хранится в БД (сессии stateless)
- **Время на карточку**: Константы (2.5 мин для learning/new, 0.25 мин для review) можно вынести в настройки, но пока захардкожены
- **Streak**: Подсчитывается по `last_review`, может быть неточным если пользователь тренируется несколько раз в день
- **Статистика**: Может быть медленной при большом количестве карточек, возможно потребуется кэширование или оптимизация
- **Новые карточки**: Определяются как карточки с `is_in_learning_mode=True` и `repetitions=0` и `interval=0` (или просто `is_in_learning_mode=True` и `created_at` недавно)

### 12. Связь с другими этапами

- **Этап 5 (SM2Algorithm):** Используется для обработки ответов
- **Этап 3 (Card):** Работает с моделью Card
- **Этап 4 (UserTrainingSettings):** Использует настройки пользователя
- **Этап 7 (AI Generation):** Будет использоваться для генерации контента в режиме изучения

---

## Статус: Готов к реализации
