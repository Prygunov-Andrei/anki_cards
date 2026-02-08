# Этап 5: Алгоритм SM-2

## Цель
Реализация алгоритма интервального повторения SuperMemo SM-2 с адаптацией под пользователя, включая внутрисессионное обучение, калибровку и автоматическое управление режимом изучения.

## Обзор

Этап 5 реализует ядро системы тренировки - алгоритм SM-2, который:
- Обрабатывает ответы пользователя (0=Again, 1=Hard, 2=Good, 3=Easy)
- Рассчитывает интервалы повторения
- Управляет Ease Factor (коэффициентом лёгкости)
- Реализует внутрисессионное обучение (learning steps: 2м, 10м)
- Автоматически отправляет карточки в режим изучения при провалах
- Интегрируется с калибровкой из UserTrainingSettings

## Структура файлов

```
backend/apps/training/
├── sm2.py              # Основной класс SM2Algorithm
├── utils.py            # Вспомогательные функции (если нужны)
└── tests.py            # Тесты для алгоритма (расширение существующего)
```

## Детальная спецификация

### 1. Класс SM2Algorithm

#### 1.1. Основной метод: `process_answer`

```python
@classmethod
def process_answer(
    cls,
    card: Card,
    answer: int,
    settings: UserTrainingSettings,
    time_spent: float = None
) -> dict:
    """
    Обрабатывает ответ пользователя на карточку.
    
    Args:
        card: Карточка для обработки
        answer: Оценка ответа (0=Again, 1=Hard, 2=Good, 3=Easy)
        settings: Настройки тренировки пользователя
        time_spent: Время, потраченное на ответ (секунды, опционально)
    
    Returns:
        dict с результатами обработки:
        {
            'card': Card (обновлённая карточка),
            'new_interval': int (дни),
            'new_ease_factor': float,
            'next_review': datetime,
            'entered_learning_mode': bool,
            'exited_learning_mode': bool,
            'learning_step': int (текущий шаг обучения),
            'calibrated': bool (была ли выполнена калибровка)
        }
    """
```

**Логика обработки:**

1. **Если карточка в режиме обучения (`is_in_learning_mode=True`):**
   - Обработка внутрисессионных шагов (см. раздел 1.2)
   
2. **Если карточка НЕ в режиме обучения:**
   - Обработка долгосрочных интервалов (см. раздел 1.3)

3. **Обновление статистики:**
   - `last_review = timezone.now()`
   - `repetitions` увеличивается при успешных ответах (Good/Easy)
   - `lapses` увеличивается при провалах (Again)
   - `consecutive_lapses` обновляется
   - Запись в `settings.record_review(successful=True/False)`

4. **Проверка на калибровку:**
   - Если `settings.should_calibrate()` → вызываем `settings.calibrate()`

5. **Сохранение карточки:**
   - `card.save()`

#### 1.2. Внутрисессионное обучение (Learning Steps)

**Шаги обучения** берутся из `settings.learning_steps` (по умолчанию `[2, 10]` - минуты).

**Логика для режима обучения:**

1. **Again (0):**
   - Сброс на первый шаг: `learning_step = 0`
   - `consecutive_lapses += 1`
   - `lapses += 1`
   - `ease_factor = max(min_ease_factor, ease_factor + again_ef_delta)`
   - `next_review = timezone.now() + timedelta(minutes=learning_steps[0])`
   - `repetitions = 0` (сброс счётчика)

2. **Hard (1):**
   - Остаёмся на текущем шаге (или промежуточный интервал)
   - `ease_factor = max(min_ease_factor, ease_factor + hard_ef_delta)`
   - Если `learning_step < len(learning_steps) - 1`:
     - `next_review = timezone.now() + timedelta(minutes=learning_steps[learning_step])`
   - Иначе (последний шаг):
     - Переход к долгосрочному интервалу (см. ниже)

3. **Good (2):**
   - Переход на следующий шаг: `learning_step += 1`
   - Если `learning_step >= len(learning_steps)`:
     - **Выпуск из режима обучения:**
       - `is_in_learning_mode = False`
       - `learning_step = -1`
       - `interval = settings.graduating_interval` (обычно 1 день)
       - `next_review = timezone.now() + timedelta(days=interval)`
       - `repetitions = 1`
   - Иначе:
     - `next_review = timezone.now() + timedelta(minutes=learning_steps[learning_step])`

4. **Easy (3):**
   - **Досрочный выпуск из режима обучения:**
   - `is_in_learning_mode = False`
   - `learning_step = -1`
   - `ease_factor = min(5.0, ease_factor + easy_ef_delta)`
   - `interval = settings.easy_interval` (обычно 4 дня)
   - `next_review = timezone.now() + timedelta(days=interval)`
   - `repetitions = 1`

#### 1.3. Долгосрочные интервалы (не в режиме обучения)

**Логика для карточек вне режима обучения:**

1. **Again (0):**
   - **Возврат в режим обучения:**
     - `is_in_learning_mode = True`
     - `learning_step = 0`
     - `consecutive_lapses += 1`
     - `lapses += 1`
     - `repetitions = 0` (сброс)
   - Снижение EF:
     - `ease_factor = max(min_ease_factor, ease_factor + again_ef_delta)`
   - Немедленный повтор:
     - `next_review = timezone.now() + timedelta(minutes=learning_steps[0])`
   - **Проверка на автоматическую отправку в режим изучения:**
     - Если `consecutive_lapses >= settings.lapse_threshold`:
       - Карточка уже в режиме обучения (выше)
       - Можно добавить флаг `force_learning_mode` для явного указания

2. **Hard (1):**
   - Снижение EF:
     - `ease_factor = max(min_ease_factor, ease_factor + hard_ef_delta)`
   - Интервал с модификатором:
     - `new_interval = max(1, int(interval * hard_interval_modifier * interval_modifier))`
     - `new_interval = max(interval + 1, new_interval)` (минимум +1 день)
   - Обновление:
     - `interval = new_interval`
     - `next_review = timezone.now() + timedelta(days=interval)`
     - `repetitions += 1`

3. **Good (2):**
   - EF без изменений (или небольшое изменение по настройкам):
     - `ease_factor = ease_factor + good_ef_delta` (обычно 0.0)
   - Стандартный расчёт интервала:
     - `new_interval = max(1, int(interval * ease_factor * interval_modifier))`
     - `new_interval = max(interval + 1, new_interval)` (минимум +1 день)
   - Обновление:
     - `interval = new_interval`
     - `next_review = timezone.now() + timedelta(days=interval)`
     - `repetitions += 1`

4. **Easy (3):**
   - Увеличение EF:
     - `ease_factor = min(5.0, ease_factor + easy_ef_delta)`
   - Интервал с бонусом:
     - `new_interval = max(1, int(interval * ease_factor * easy_bonus * interval_modifier))`
     - `new_interval = max(interval + 1, new_interval)` (минимум +1 день)
   - Обновление:
     - `interval = new_interval`
     - `next_review = timezone.now() + timedelta(days=interval)`
     - `repetitions += 1`

#### 1.4. Вспомогательные методы

```python
@classmethod
def calculate_next_interval(
    cls,
    card: Card,
    answer: int,
    settings: UserTrainingSettings
) -> int:
    """
    Рассчитывает следующий интервал в днях (только для долгосрочных интервалов).
    Не используется для режима обучения.
    
    Returns:
        int: Интервал в днях
    """

@classmethod
def should_enter_learning_mode(
    cls,
    card: Card,
    settings: UserTrainingSettings
) -> bool:
    """
    Проверяет, нужно ли отправить карточку в режим изучения.
    
    Returns:
        bool: True если consecutive_lapses >= lapse_threshold
    """

@classmethod
def update_ease_factor(
    cls,
    card: Card,
    answer: int,
    settings: UserTrainingSettings
) -> float:
    """
    Обновляет Ease Factor карточки на основе ответа.
    
    Returns:
        float: Новое значение ease_factor
    """

@classmethod
def apply_interval_modifiers(
    cls,
    base_interval: int,
    answer: int,
    settings: UserTrainingSettings
) -> int:
    """
    Применяет модификаторы интервала (hard_interval_modifier, easy_bonus, interval_modifier).
    
    Returns:
        int: Модифицированный интервал в днях
    """
```

### 2. Обработка граничных случаев

#### 2.1. Первая карточка (repetitions=0, interval=0)

- При первом ответе "Good" или "Easy":
  - Если в режиме обучения → стандартная логика
  - Если не в режиме обучения → `interval = 1` день (или `graduating_interval`)

#### 2.2. Минимальные/максимальные значения

- **Ease Factor:**
  - Минимум: `settings.min_ease_factor` (обычно 1.3)
  - Максимум: 5.0 (жестко закодировано, можно вынести в настройки)
  
- **Интервал:**
  - Минимум: 1 день
  - Максимум: не ограничен (или можно установить, например, 3650 дней = 10 лет)

#### 2.3. Округление интервалов

- Интервалы округляются до целых дней
- Всегда минимум +1 день от предыдущего интервала (для монотонного роста)

### 3. Интеграция с UserTrainingSettings

#### 3.1. Использование настроек

Все константы берутся из `UserTrainingSettings`:
- `starting_ease` - начальный EF (используется при создании карточки)
- `min_ease_factor` - минимальный EF
- `again_ef_delta`, `hard_ef_delta`, `good_ef_delta`, `easy_ef_delta` - изменения EF
- `interval_modifier` - глобальный модификатор интервалов
- `hard_interval_modifier` - модификатор для "Hard"
- `easy_bonus` - бонус для "Easy"
- `learning_steps` - шаги обучения (минуты)
- `graduating_interval` - интервал выпуска (дни)
- `easy_interval` - интервал для "Easy" в режиме обучения (дни)
- `lapse_threshold` - порог провалов для режима изучения

#### 3.2. Калибровка

- После каждого ответа вызывается `settings.record_review(successful=True/False)`
- Если `settings.should_calibrate()` → вызывается `settings.calibrate()`
- Результат калибровки влияет на `interval_modifier` для будущих расчётов

### 4. Тестирование

#### 4.1. Юнит-тесты для SM2Algorithm

**Тест-кейсы:**

1. **Внутрисессионное обучение:**
   - [ ] Again в режиме обучения → сброс на первый шаг
   - [ ] Good в режиме обучения → переход на следующий шаг
   - [ ] Easy в режиме обучения → досрочный выпуск
   - [ ] Hard в режиме обучения → остаётся на шаге
   - [ ] Прохождение всех шагов → выпуск из режима обучения

2. **Долгосрочные интервалы:**
   - [ ] Again вне режима обучения → возврат в режим обучения
   - [ ] Hard → интервал с модификатором, снижение EF
   - [ ] Good → стандартный расчёт интервала
   - [ ] Easy → интервал с бонусом, увеличение EF

3. **Ease Factor:**
   - [ ] Снижение EF при Again (не ниже минимума)
   - [ ] Снижение EF при Hard (не ниже минимума)
   - [ ] Увеличение EF при Easy (не выше максимума)
   - [ ] EF остаётся при Good

4. **Интервалы:**
   - [ ] Интервалы монотонно растут (минимум +1 день)
   - [ ] Применение модификаторов (hard_interval_modifier, easy_bonus, interval_modifier)
   - [ ] Округление до целых дней

5. **Граничные случаи:**
   - [ ] Первая карточка (repetitions=0, interval=0)
   - [ ] EF на минимуме (1.3)
   - [ ] EF на максимуме (5.0)
   - [ ] consecutive_lapses >= lapse_threshold

6. **Интеграция с настройками:**
   - [ ] Использование всех параметров из UserTrainingSettings
   - [ ] Калибровка после N ответов
   - [ ] Запись статистики в settings

7. **Сложные сценарии:**
   - [ ] Сценарий 1 из теории: новое слово, успешное запоминание
   - [ ] Сценарий 2 из теории: сложное слово, повторные забывания
   - [ ] Множественные провалы → снижение EF до минимума
   - [ ] Множественные успехи → рост интервалов

**Минимальное количество тестов: 25+**

#### 4.2. Интеграционные тесты

- [ ] Полный цикл: новая карточка → обучение → долгосрочные интервалы
- [ ] Калибровка влияет на будущие интервалы
- [ ] Статистика корректно обновляется

### 5. Примеры использования

#### 5.1. Пример 1: Новое слово

```python
# Создаём карточку (автоматически в режиме обучения)
card = Card.create_from_word(word, 'normal')
# card.is_in_learning_mode = True
# card.learning_step = 0
# card.ease_factor = 2.5

# Первый ответ: Good
result = SM2Algorithm.process_answer(card, 2, settings)
# card.learning_step = 1
# card.next_review = now + 2 minutes

# Второй ответ: Easy (досрочный выпуск)
result = SM2Algorithm.process_answer(card, 3, settings)
# card.is_in_learning_mode = False
# card.interval = 4 (easy_interval)
# card.next_review = now + 4 days
```

#### 5.2. Пример 2: Провал на повторении

```python
# Карточка вне режима обучения
# card.interval = 10 дней
# card.ease_factor = 2.5

# Пользователь забыл: Again
result = SM2Algorithm.process_answer(card, 0, settings)
# card.is_in_learning_mode = True
# card.learning_step = 0
# card.ease_factor = 2.3 (снизился на 0.2)
# card.next_review = now + 2 minutes
```

### 6. Задачи реализации

- [ ] Создать файл `backend/apps/training/sm2.py`
- [ ] Реализовать класс `SM2Algorithm`
- [ ] Реализовать метод `process_answer` с полной логикой
- [ ] Реализовать вспомогательные методы
- [ ] Добавить обработку граничных случаев
- [ ] Интегрировать с `UserTrainingSettings`
- [ ] Добавить калибровку
- [ ] Написать юнит-тесты (25+ тестов)
- [ ] Написать интеграционные тесты
- [ ] Проверить соответствие теории SuperMemo
- [ ] Проверить все сценарии из документации

### 7. Критерии готовности

✅ Все методы реализованы  
✅ Все тесты проходят (25+ тестов)  
✅ Логика соответствует теории SuperMemo  
✅ Интеграция с UserTrainingSettings работает  
✅ Калибровка интегрирована  
✅ Граничные случаи обработаны  
✅ Код покрыт комментариями  
✅ Нет захардкоженных констант (всё из settings)

### 8. Примечания

- Все константы должны браться из `UserTrainingSettings`, а не быть захардкоженными
- Интервалы всегда в днях для долгосрочных, в минутах для режима обучения
- `next_review` всегда должен быть в будущем
- При сбросе в режим обучения `repetitions` обнуляется
- `consecutive_lapses` увеличивается при провалах, обнуляется при успехе
- Калибровка выполняется автоматически, но не блокирует обработку ответа

### 9. Связь с другими этапами

- **Этап 4 (UserTrainingSettings):** Использует все настройки из этой модели
- **Этап 6 (API для тренировки):** Будет вызывать `SM2Algorithm.process_answer()` для обработки ответов
- **Этап 3 (Card):** Работает с моделью Card, обновляет её поля

---

## Статус: Готов к реализации
