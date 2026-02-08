# ⚙️ Этап 4: Настройки пользователя для тренировки (UserTrainingSettings)

> **Статус**: 🚧 В разработке  
> **Тип**: Backend + Frontend (частично)  
> **Зависимости**: Этап 3 (Card)  
> **Следующий этап**: 5 (SM-2 Algorithm)

---

## 🎯 Цель этапа

Создать модель `UserTrainingSettings` для хранения всех настраиваемых констант алгоритма SM-2:

- **Все константы SM-2 настраиваемые** пользователем
- **Инициализация по возрасту** при регистрации
- **API для управления** настройками
- **Автоматическая калибровка** (структура, реализация в этапе 5)

---

## 📋 Ключевые концепции

### Настраиваемые параметры SM-2

```
┌─────────────────────────────────────────────────────────────┐
│              UserTrainingSettings                            │
├─────────────────────────────────────────────────────────────┤
│ Ease Factor:                                                │
│   starting_ease = 2.5      # Начальный EF                   │
│   min_ease_factor = 1.3     # Минимум EF                    │
│                                                              │
│ Дельты EF (при ответах):                                    │
│   again_ef_delta = -0.2    # "Снова"                        │
│   hard_ef_delta = -0.15    # "Трудно"                       │
│   good_ef_delta = 0.0      # "Хорошо"                       │
│   easy_ef_delta = +0.15    # "Легко"                        │
├─────────────────────────────────────────────────────────────┤
│ Модификаторы интервалов:                                     │
│   interval_modifier = 1.0   # Глобальный                     │
│   hard_interval_modifier = 1.2  # Для "Трудно"              │
│   easy_bonus = 1.3         # Для "Легко"                    │
├─────────────────────────────────────────────────────────────┤
│ Шаги обучения:                                             │
│   learning_steps = [2, 10]  # Минуты (внутрисессионное)     │
│   graduating_interval = 1   # Дни (после шагов)             │
│   easy_interval = 4        # Дни (при "Легко" сразу)        │
├─────────────────────────────────────────────────────────────┤
│ Пороги:                                                     │
│   lapse_threshold = 4       # Провалов → Learning Mode      │
│   stability_threshold = 60  # Дни → burn auxiliary          │
│   calibration_interval = 50 # Каждые N ответов              │
│   target_retention = 0.90   # 90% успеха                    │
├─────────────────────────────────────────────────────────────┤
│ Калибровка (автоматическая):                                │
│   total_reviews = 0         # Всего ответов                  │
│   successful_reviews = 0    # Успешных ответов              │
│   last_calibration_at = 0  # Последняя калибровка          │
└─────────────────────────────────────────────────────────────┘
```

### Инициализация по возрасту

| Возрастная группа | starting_ease | interval_modifier | target_retention |
|-------------------|---------------|-------------------|------------------|
| До 18 лет         | 2.5           | 1.0               | 0.90             |
| 18-50 лет         | 2.5           | 1.0               | 0.90             |
| 50+ лет           | 2.3           | 0.9               | 0.85             |

---

## 📋 Задачи

### 1. Создание приложения training

- [ ] **1.1** Создать Django приложение `apps/training`
- [ ] **1.2** Добавить в `INSTALLED_APPS`
- [ ] **1.3** Создать структуру приложения

### 2. Создание модели UserTrainingSettings

- [ ] **2.1** Создать модель `UserTrainingSettings`
- [ ] **2.2** Добавить все поля SM-2 констант
- [ ] **2.3** Добавить методы инициализации по возрасту
- [ ] **2.4** Добавить метод `reset_to_defaults()`
- [ ] **2.5** Создать миграцию

### 3. Сигнал автосоздания настроек

- [ ] **3.1** Создать сигнал при регистрации пользователя
- [ ] **3.2** Инициализировать настройки по `age_group`
- [ ] **3.3** Подключить сигнал в `apps.py`

### 4. Обновление регистрации

- [ ] **4.1** Добавить поле `age_group` в `UserRegistrationSerializer`
- [ ] **4.2** Обновить форму регистрации (frontend)
- [ ] **4.3** Передать `age_group` при создании настроек

### 5. Сериализаторы

- [ ] **5.1** `UserTrainingSettingsSerializer` — полное представление
- [ ] **5.2** `UserTrainingSettingsUpdateSerializer` — для обновления
- [ ] **5.3** `UserTrainingSettingsResetSerializer` — для сброса

### 6. API эндпоинты

- [ ] **6.1** GET `/api/training/settings/` — получить настройки
- [ ] **6.2** PATCH `/api/training/settings/` — обновить настройки
- [ ] **6.3** POST `/api/training/settings/reset/` — сбросить к умолчанию
- [ ] **6.4** GET `/api/training/settings/defaults/` — получить значения по умолчанию

### 7. Метод калибровки (структура)

- [ ] **7.1** Создать метод `calibrate()` в модели
- [ ] **7.2** Логика калибровки (будет использоваться в этапе 5)
- [ ] **7.3** Обновление `interval_modifier` на основе статистики

### 8. Тесты

- [ ] **8.1** Unit-тесты модели (10+ тестов)
- [ ] **8.2** Тесты сигналов автосоздания (3+ теста)
- [ ] **8.3** API-тесты (8+ тестов)
- [ ] **8.4** Тесты калибровки (5+ тестов)

### 9. TypeScript типы

- [ ] **9.1** Интерфейс `UserTrainingSettings`
- [ ] **9.2** Интерфейс `AgeGroup`
- [ ] **9.3** Типы для запросов/ответов API

---

## 📁 Файлы для изменения/создания

| Файл | Действие |
|------|----------|
| `backend/apps/training/` | ✨ Создать новое приложение |
| `backend/apps/training/models.py` | ✨ Создать модель UserTrainingSettings |
| `backend/apps/training/signals.py` | ✨ Сигнал автосоздания |
| `backend/apps/training/serializers.py` | ✨ Сериализаторы |
| `backend/apps/training/views.py` | ✨ Views для API |
| `backend/apps/training/urls.py` | ✨ URL-маршруты |
| `backend/apps/training/admin.py` | Зарегистрировать модель |
| `backend/apps/training/tests.py` | ✨ Тесты |
| `backend/apps/users/serializers.py` | Добавить age_group |
| `backend/apps/users/views.py` | Обновить регистрацию |
| `backend/config/settings.py` | Добавить training в INSTALLED_APPS |
| `frontend/src/types/index.ts` | Добавить TypeScript типы |

---

## 💻 Код

### 1. Создание приложения

```bash
cd backend
python3 manage.py startapp training apps/training
```

### 2.1 Модель UserTrainingSettings

**Файл**: `backend/apps/training/models.py`

```python
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserTrainingSettings(models.Model):
    """
    Настройки тренировки пользователя.
    
    ВСЕ константы алгоритма SM-2 настраиваемые пользователем.
    Значения по умолчанию инициализируются на основе возраста.
    """
    
    AGE_GROUPS = [
        ('young', 'До 18 лет'),
        ('adult', '18-50 лет'),
        ('senior', '50+ лет'),
    ]
    
    # ═══════════════════════════════════════════════════════════════
    # СВЯЗЬ С ПОЛЬЗОВАТЕЛЕМ
    # ═══════════════════════════════════════════════════════════════
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='training_settings',
        verbose_name='Пользователь'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ВОЗРАСТНАЯ ГРУППА
    # ═══════════════════════════════════════════════════════════════
    
    age_group = models.CharField(
        max_length=20,
        choices=AGE_GROUPS,
        default='adult',
        verbose_name='Возрастная группа',
        help_text='Влияет на начальные параметры'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # EASE FACTOR (коэффициент лёгкости)
    # ═══════════════════════════════════════════════════════════════
    
    starting_ease = models.FloatField(
        default=2.5,
        verbose_name='Начальный Ease Factor',
        help_text='EF для новых карточек'
    )
    min_ease_factor = models.FloatField(
        default=1.3,
        verbose_name='Минимальный Ease Factor',
        help_text='Нижний предел EF (не может быть меньше)'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ИЗМЕНЕНИЯ EF ПРИ РАЗНЫХ ОТВЕТАХ
    # ═══════════════════════════════════════════════════════════════
    
    again_ef_delta = models.FloatField(
        default=-0.2,
        verbose_name='Дельта EF при "Снова"',
        help_text='Изменение EF при нажатии "Снова"'
    )
    hard_ef_delta = models.FloatField(
        default=-0.15,
        verbose_name='Дельта EF при "Трудно"',
        help_text='Изменение EF при нажатии "Трудно"'
    )
    good_ef_delta = models.FloatField(
        default=0.0,
        verbose_name='Дельта EF при "Хорошо"',
        help_text='Изменение EF при нажатии "Хорошо"'
    )
    easy_ef_delta = models.FloatField(
        default=0.15,
        verbose_name='Дельта EF при "Легко"',
        help_text='Изменение EF при нажатии "Легко"'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # МОДИФИКАТОРЫ ИНТЕРВАЛОВ
    # ═══════════════════════════════════════════════════════════════
    
    interval_modifier = models.FloatField(
        default=1.0,
        verbose_name='Глобальный модификатор интервалов',
        help_text='Умножается на все интервалы (для калибровки)'
    )
    hard_interval_modifier = models.FloatField(
        default=1.2,
        verbose_name='Модификатор для "Трудно"',
        help_text='Умножается на интервал при "Трудно"'
    )
    easy_bonus = models.FloatField(
        default=1.3,
        verbose_name='Бонус для "Легко"',
        help_text='Умножается на интервал при "Легко"'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ШАГИ ОБУЧЕНИЯ (внутрисессионное повторение)
    # ═══════════════════════════════════════════════════════════════
    
    learning_steps = models.JSONField(
        default=list,
        verbose_name='Шаги обучения (минуты)',
        help_text='Интервалы внутри сессии: [2, 10] означает 2 мин, затем 10 мин'
    )
    graduating_interval = models.IntegerField(
        default=1,
        verbose_name='Интервал выпуска (дни)',
        help_text='Интервал после прохождения всех шагов обучения'
    )
    easy_interval = models.IntegerField(
        default=4,
        verbose_name='Интервал при "Легко" (дни)',
        help_text='Интервал если сразу нажали "Легко" в режиме изучения'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # НАСТРОЙКИ СЕССИИ
    # ═══════════════════════════════════════════════════════════════
    
    default_session_duration = models.IntegerField(
        default=20,
        verbose_name='Длительность сессии по умолчанию (минуты)',
        help_text='Стандартное время тренировки'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ПОРОГИ И ЛИМИТЫ
    # ═══════════════════════════════════════════════════════════════
    
    lapse_threshold = models.IntegerField(
        default=4,
        verbose_name='Порог провалов',
        help_text='Количество провалов подряд → режим Изучения'
    )
    stability_threshold = models.IntegerField(
        default=60,
        verbose_name='Порог стабильности (дни)',
        help_text='Интервал карточки >= этого значения → удаление вспомогательных'
    )
    calibration_interval = models.IntegerField(
        default=50,
        verbose_name='Интервал калибровки',
        help_text='Калибровка каждые N ответов'
    )
    target_retention = models.FloatField(
        default=0.90,
        verbose_name='Целевой процент успеха',
        help_text='Целевой процент успешных ответов для калибровки (0.90 = 90%)'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # КАЛИБРОВКА (автоматическая)
    # ═══════════════════════════════════════════════════════════════
    
    total_reviews = models.IntegerField(
        default=0,
        verbose_name='Всего ответов',
        help_text='Общее количество ответов пользователя'
    )
    successful_reviews = models.IntegerField(
        default=0,
        verbose_name='Успешных ответов',
        help_text='Количество успешных ответов (Good/Easy)'
    )
    last_calibration_at = models.IntegerField(
        default=0,
        verbose_name='Последняя калибровка',
        help_text='Номер ответа, на котором была последняя калибровка'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # МЕТАДАННЫЕ
    # ═══════════════════════════════════════════════════════════════
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Настройки тренировки'
        verbose_name_plural = 'Настройки тренировки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Настройки тренировки: {self.user.username}"
    
    # ═══════════════════════════════════════════════════════════════
    # МЕТОДЫ ИНИЦИАЛИЗАЦИИ
    # ═══════════════════════════════════════════════════════════════
    
    @classmethod
    def get_defaults_for_age(cls, age_group: str) -> dict:
        """
        Возвращает значения по умолчанию для возрастной группы.
        
        Args:
            age_group: 'young', 'adult', или 'senior'
        
        Returns:
            dict с значениями по умолчанию
        """
        defaults = {
            'young': {
                'starting_ease': 2.5,
                'interval_modifier': 1.0,
                'min_ease_factor': 1.3,
                'target_retention': 0.90,
            },
            'adult': {
                'starting_ease': 2.5,
                'interval_modifier': 1.0,
                'min_ease_factor': 1.3,
                'target_retention': 0.90,
            },
            'senior': {
                'starting_ease': 2.3,
                'interval_modifier': 0.9,
                'min_ease_factor': 1.3,
                'target_retention': 0.85,
            },
        }
        return defaults.get(age_group, defaults['adult'])
    
    @classmethod
    def create_for_user(cls, user, age_group: str = 'adult') -> 'UserTrainingSettings':
        """
        Создаёт настройки для пользователя с инициализацией по возрасту.
        
        Args:
            user: Пользователь
            age_group: Возрастная группа
        
        Returns:
            Созданный объект настроек
        """
        defaults = cls.get_defaults_for_age(age_group)
        
        settings = cls.objects.create(
            user=user,
            age_group=age_group,
            **defaults
        )
        return settings
    
    def reset_to_defaults(self) -> None:
        """
        Сбрасывает настройки к значениям по умолчанию для текущей возрастной группы.
        Сохраняет изменения.
        """
        defaults = self.get_defaults_for_age(self.age_group)
        
        # Обновляем только настраиваемые поля
        self.starting_ease = defaults['starting_ease']
        self.interval_modifier = defaults['interval_modifier']
        self.min_ease_factor = defaults['min_ease_factor']
        self.target_retention = defaults['target_retention']
        
        # Остальные поля сбрасываем к стандартным значениям
        self.again_ef_delta = -0.2
        self.hard_ef_delta = -0.15
        self.good_ef_delta = 0.0
        self.easy_ef_delta = 0.15
        self.hard_interval_modifier = 1.2
        self.easy_bonus = 1.3
        self.learning_steps = [2, 10]
        self.graduating_interval = 1
        self.easy_interval = 4
        self.default_session_duration = 20
        self.lapse_threshold = 4
        self.stability_threshold = 60
        self.calibration_interval = 50
        
        # Калибровку не сбрасываем
        # total_reviews, successful_reviews, last_calibration_at остаются
        
        self.save()
    
    # ═══════════════════════════════════════════════════════════════
    # МЕТОДЫ КАЛИБРОВКИ
    # ═══════════════════════════════════════════════════════════════
    
    def should_calibrate(self) -> bool:
        """
        Проверяет, нужно ли выполнить калибровку.
        
        Returns:
            True если прошло достаточно ответов с последней калибровки
        """
        return (self.total_reviews - self.last_calibration_at) >= self.calibration_interval
    
    def calibrate(self) -> dict:
        """
        Выполняет калибровку параметров на основе статистики.
        
        Анализирует последние N ответов и корректирует interval_modifier
        для достижения target_retention.
        
        Returns:
            dict с информацией о калибровке:
            {
                'calibrated': bool,
                'old_modifier': float,
                'new_modifier': float,
                'success_rate': float,
                'target_rate': float,
            }
        """
        if not self.should_calibrate():
            return {
                'calibrated': False,
                'message': 'Калибровка не требуется'
            }
        
        # Вычисляем процент успеха за последние N ответов
        recent_reviews = self.total_reviews - self.last_calibration_at
        if recent_reviews == 0:
            return {
                'calibrated': False,
                'message': 'Нет данных для калибровки'
            }
        
        recent_successful = self.successful_reviews - (
            self.last_calibration_at - (self.total_reviews - recent_reviews)
        )
        # Упрощённый расчёт: берём общий процент успеха
        success_rate = self.successful_reviews / self.total_reviews if self.total_reviews > 0 else 0.0
        
        old_modifier = self.interval_modifier
        target_rate = self.target_retention
        
        # Корректируем interval_modifier
        if success_rate < (target_rate - 0.05):  # Ниже целевого на 5%
            # Уменьшаем интервалы (делаем повторения чаще)
            self.interval_modifier = max(0.5, self.interval_modifier * 0.95)
        elif success_rate > (target_rate + 0.05):  # Выше целевого на 5%
            # Увеличиваем интервалы (делаем повторения реже)
            self.interval_modifier = min(2.0, self.interval_modifier * 1.05)
        
        self.last_calibration_at = self.total_reviews
        self.save()
        
        return {
            'calibrated': True,
            'old_modifier': old_modifier,
            'new_modifier': self.interval_modifier,
            'success_rate': success_rate,
            'target_rate': target_rate,
        }
    
    def record_review(self, successful: bool) -> None:
        """
        Записывает ответ пользователя для статистики.
        
        Args:
            successful: True если ответ был успешным (Good/Easy)
        """
        self.total_reviews += 1
        if successful:
            self.successful_reviews += 1
        self.save(update_fields=['total_reviews', 'successful_reviews', 'updated_at'])
```

---

### 2.2 Сигнал автосоздания

**Файл**: `backend/apps/training/signals.py`

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserTrainingSettings

User = get_user_model()


@receiver(post_save, sender=User)
def create_training_settings_for_new_user(sender, instance, created, **kwargs):
    """
    При создании нового пользователя автоматически создаём настройки тренировки.
    
    Использует age_group из атрибутов пользователя, если он был передан
    при создании (например, через сигнал регистрации).
    """
    if created:
        # Пытаемся получить age_group из атрибутов пользователя
        # (устанавливается в процессе регистрации)
        age_group = getattr(instance, '_age_group', 'adult')
        UserTrainingSettings.create_for_user(instance, age_group)
```

---

### 2.3 Подключение сигналов

**Файл**: `backend/apps/training/apps.py`

```python
from django.apps import AppConfig


class TrainingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.training'
    verbose_name = 'Тренировка'

    def ready(self):
        # Импортируем сигналы при запуске приложения
        import apps.training.signals  # noqa: F401
```

---

### 3. Обновление регистрации

**Файл**: `backend/apps/users/serializers.py` (добавить)

```python
# В UserRegistrationSerializer добавить:

age_group = serializers.ChoiceField(
    choices=UserTrainingSettings.AGE_GROUPS,
    required=False,
    default='adult',
    help_text='Возрастная группа (влияет на начальные параметры тренировки)'
)
```

**Файл**: `backend/apps/users/views.py` (обновить register_view)

```python
# В функции register_view после serializer.save():

user = serializer.save()

# Устанавливаем age_group для сигнала
age_group = serializer.validated_data.get('age_group', 'adult')
user._age_group = age_group

# Сигнал создаст UserTrainingSettings автоматически
```

---

### 4. Сериализаторы

**Файл**: `backend/apps/training/serializers.py`

```python
from rest_framework import serializers
from .models import UserTrainingSettings


class UserTrainingSettingsSerializer(serializers.ModelSerializer):
    """Полное представление настроек тренировки"""
    
    age_group_display = serializers.CharField(
        source='get_age_group_display',
        read_only=True
    )
    
    class Meta:
        model = UserTrainingSettings
        fields = [
            # Основное
            'age_group',
            'age_group_display',
            # Ease Factor
            'starting_ease',
            'min_ease_factor',
            # Дельты EF
            'again_ef_delta',
            'hard_ef_delta',
            'good_ef_delta',
            'easy_ef_delta',
            # Модификаторы интервалов
            'interval_modifier',
            'hard_interval_modifier',
            'easy_bonus',
            # Шаги обучения
            'learning_steps',
            'graduating_interval',
            'easy_interval',
            # Настройки сессии
            'default_session_duration',
            # Пороги
            'lapse_threshold',
            'stability_threshold',
            'calibration_interval',
            'target_retention',
            # Калибровка (read-only)
            'total_reviews',
            'successful_reviews',
            'last_calibration_at',
            # Мета
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'total_reviews',
            'successful_reviews',
            'last_calibration_at',
            'created_at',
            'updated_at',
        ]
    
    def validate_starting_ease(self, value):
        """Валидация starting_ease"""
        if value < 1.3:
            raise serializers.ValidationError("starting_ease не может быть меньше 1.3")
        if value > 5.0:
            raise serializers.ValidationError("starting_ease не может быть больше 5.0")
        return value
    
    def validate_min_ease_factor(self, value):
        """Валидация min_ease_factor"""
        if value < 1.0:
            raise serializers.ValidationError("min_ease_factor не может быть меньше 1.0")
        if value > self.validated_data.get('starting_ease', 2.5):
            raise serializers.ValidationError("min_ease_factor не может быть больше starting_ease")
        return value
    
    def validate_learning_steps(self, value):
        """Валидация learning_steps"""
        if not isinstance(value, list):
            raise serializers.ValidationError("learning_steps должен быть списком")
        if len(value) == 0:
            raise serializers.ValidationError("learning_steps не может быть пустым")
        if not all(isinstance(x, int) and x > 0 for x in value):
            raise serializers.ValidationError("Все элементы learning_steps должны быть положительными целыми числами")
        return value
    
    def validate_target_retention(self, value):
        """Валидация target_retention"""
        if value < 0.5 or value > 1.0:
            raise serializers.ValidationError("target_retention должен быть от 0.5 до 1.0")
        return value


class UserTrainingSettingsUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для частичного обновления настроек"""
    
    class Meta:
        model = UserTrainingSettings
        fields = [
            'age_group',
            'starting_ease',
            'min_ease_factor',
            'again_ef_delta',
            'hard_ef_delta',
            'good_ef_delta',
            'easy_ef_delta',
            'interval_modifier',
            'hard_interval_modifier',
            'easy_bonus',
            'learning_steps',
            'graduating_interval',
            'easy_interval',
            'default_session_duration',
            'lapse_threshold',
            'stability_threshold',
            'calibration_interval',
            'target_retention',
        ]
    
    # Те же валидаторы, что и в UserTrainingSettingsSerializer


class UserTrainingSettingsDefaultsSerializer(serializers.Serializer):
    """Сериализатор для получения значений по умолчанию"""
    
    age_group = serializers.ChoiceField(
        choices=UserTrainingSettings.AGE_GROUPS,
        required=True
    )
    
    def to_representation(self, instance):
        """Возвращает значения по умолчанию для указанной возрастной группы"""
        age_group = self.validated_data['age_group']
        defaults = UserTrainingSettings.get_defaults_for_age(age_group)
        
        # Добавляем стандартные значения для всех полей
        return {
            'age_group': age_group,
            **defaults,
            'again_ef_delta': -0.2,
            'hard_ef_delta': -0.15,
            'good_ef_delta': 0.0,
            'easy_ef_delta': 0.15,
            'hard_interval_modifier': 1.2,
            'easy_bonus': 1.3,
            'learning_steps': [2, 10],
            'graduating_interval': 1,
            'easy_interval': 4,
            'default_session_duration': 20,
            'lapse_threshold': 4,
            'stability_threshold': 60,
            'calibration_interval': 50,
        }
```

---

### 5. Views

**Файл**: `backend/apps/training/views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import UserTrainingSettings
from .serializers import (
    UserTrainingSettingsSerializer,
    UserTrainingSettingsUpdateSerializer,
    UserTrainingSettingsDefaultsSerializer,
)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def training_settings_view(request):
    """
    GET /api/training/settings/ — Получить настройки тренировки
    PATCH /api/training/settings/ — Обновить настройки тренировки
    """
    settings, created = UserTrainingSettings.objects.get_or_create(
        user=request.user,
        defaults={'age_group': 'adult'}
    )
    
    if request.method == 'GET':
        serializer = UserTrainingSettingsSerializer(settings)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = UserTrainingSettingsUpdateSerializer(
            settings,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            # Возвращаем полное представление
            full_serializer = UserTrainingSettingsSerializer(settings)
            return Response(full_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_settings_reset_view(request):
    """
    POST /api/training/settings/reset/ — Сбросить настройки к значениям по умолчанию
    """
    settings = get_object_or_404(UserTrainingSettings, user=request.user)
    settings.reset_to_defaults()
    
    serializer = UserTrainingSettingsSerializer(settings)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_settings_defaults_view(request):
    """
    GET /api/training/settings/defaults/?age_group=adult — Получить значения по умолчанию
    """
    age_group = request.query_params.get('age_group', 'adult')
    
    serializer = UserTrainingSettingsDefaultsSerializer(data={'age_group': age_group})
    if serializer.is_valid():
        return Response(serializer.to_representation(None))
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

---

### 6. URL-маршруты

**Файл**: `backend/apps/training/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('settings/', views.training_settings_view, name='training-settings'),
    path('settings/reset/', views.training_settings_reset_view, name='training-settings-reset'),
    path('settings/defaults/', views.training_settings_defaults_view, name='training-settings-defaults'),
]
```

**Файл**: `backend/config/urls.py` (добавить)

```python
path('api/training/', include('apps.training.urls')),
```

---

### 7. Регистрация в Admin

**Файл**: `backend/apps/training/admin.py`

```python
from django.contrib import admin
from .models import UserTrainingSettings


@admin.register(UserTrainingSettings)
class UserTrainingSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'age_group', 'starting_ease', 'interval_modifier',
        'total_reviews', 'successful_reviews', 'target_retention'
    ]
    list_filter = ['age_group', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'total_reviews', 'successful_reviews', 'last_calibration_at']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user', 'age_group')
        }),
        ('Ease Factor', {
            'fields': ('starting_ease', 'min_ease_factor')
        }),
        ('Дельты EF', {
            'fields': ('again_ef_delta', 'hard_ef_delta', 'good_ef_delta', 'easy_ef_delta')
        }),
        ('Модификаторы интервалов', {
            'fields': ('interval_modifier', 'hard_interval_modifier', 'easy_bonus')
        }),
        ('Шаги обучения', {
            'fields': ('learning_steps', 'graduating_interval', 'easy_interval')
        }),
        ('Настройки сессии', {
            'fields': ('default_session_duration',)
        }),
        ('Пороги', {
            'fields': ('lapse_threshold', 'stability_threshold', 'calibration_interval', 'target_retention')
        }),
        ('Калибровка', {
            'fields': ('total_reviews', 'successful_reviews', 'last_calibration_at'),
            'classes': ('collapse',),
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
```

---

### 8. TypeScript типы

**Файл**: `frontend/src/types/index.ts` (добавить)

```typescript
// ═══════════════════════════════════════════════════════════════
// TRAINING SETTINGS TYPES (Этап 4)
// ═══════════════════════════════════════════════════════════════

export type AgeGroup = 'young' | 'adult' | 'senior';

export interface UserTrainingSettings {
  // Основное
  age_group: AgeGroup;
  age_group_display: string;
  
  // Ease Factor
  starting_ease: number;
  min_ease_factor: number;
  
  // Дельты EF
  again_ef_delta: number;
  hard_ef_delta: number;
  good_ef_delta: number;
  easy_ef_delta: number;
  
  // Модификаторы интервалов
  interval_modifier: number;
  hard_interval_modifier: number;
  easy_bonus: number;
  
  // Шаги обучения
  learning_steps: number[];
  graduating_interval: number;
  easy_interval: number;
  
  // Настройки сессии
  default_session_duration: number;
  
  // Пороги
  lapse_threshold: number;
  stability_threshold: number;
  calibration_interval: number;
  target_retention: number;
  
  // Калибровка (read-only)
  total_reviews: number;
  successful_reviews: number;
  last_calibration_at: number;
  
  // Мета
  created_at: string;
  updated_at: string;
}

export interface UserTrainingSettingsUpdate {
  age_group?: AgeGroup;
  starting_ease?: number;
  min_ease_factor?: number;
  again_ef_delta?: number;
  hard_ef_delta?: number;
  good_ef_delta?: number;
  easy_ef_delta?: number;
  interval_modifier?: number;
  hard_interval_modifier?: number;
  easy_bonus?: number;
  learning_steps?: number[];
  graduating_interval?: number;
  easy_interval?: number;
  default_session_duration?: number;
  lapse_threshold?: number;
  stability_threshold?: number;
  calibration_interval?: number;
  target_retention?: number;
}

export interface TrainingSettingsDefaults {
  age_group: AgeGroup;
  starting_ease: number;
  min_ease_factor: number;
  again_ef_delta: number;
  hard_ef_delta: number;
  good_ef_delta: number;
  easy_ef_delta: number;
  interval_modifier: number;
  hard_interval_modifier: number;
  easy_bonus: number;
  learning_steps: number[];
  graduating_interval: number;
  easy_interval: number;
  default_session_duration: number;
  lapse_threshold: number;
  stability_threshold: number;
  calibration_interval: number;
}
```

---

## 🧪 Тесты

### Unit-тесты модели

**Файл**: `backend/apps/training/tests.py`

```python
import pytest
from django.contrib.auth import get_user_model
from .models import UserTrainingSettings

User = get_user_model()


@pytest.mark.django_db
class TestUserTrainingSettingsModel:
    """Unit-тесты модели UserTrainingSettings"""
    
    def test_create_for_user(self):
        """Тест создания настроек для пользователя"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        settings = UserTrainingSettings.create_for_user(user, 'adult')
        
        assert settings.user == user
        assert settings.age_group == 'adult'
        assert settings.starting_ease == 2.5
        assert settings.interval_modifier == 1.0
    
    def test_get_defaults_for_age_young(self):
        """Тест значений по умолчанию для молодых"""
        defaults = UserTrainingSettings.get_defaults_for_age('young')
        assert defaults['starting_ease'] == 2.5
        assert defaults['interval_modifier'] == 1.0
    
    def test_get_defaults_for_age_senior(self):
        """Тест значений по умолчанию для пожилых"""
        defaults = UserTrainingSettings.get_defaults_for_age('senior')
        assert defaults['starting_ease'] == 2.3
        assert defaults['interval_modifier'] == 0.9
        assert defaults['target_retention'] == 0.85
    
    def test_reset_to_defaults(self):
        """Тест сброса к значениям по умолчанию"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.create_for_user(user, 'adult')
        
        # Изменяем значения
        settings.starting_ease = 3.0
        settings.interval_modifier = 1.5
        settings.save()
        
        # Сбрасываем
        settings.reset_to_defaults()
        
        assert settings.starting_ease == 2.5
        assert settings.interval_modifier == 1.0
    
    def test_should_calibrate(self):
        """Тест проверки необходимости калибровки"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.create_for_user(user)
        
        # Не должно быть калибровки
        assert settings.should_calibrate() is False
        
        # Увеличиваем total_reviews
        settings.total_reviews = 50
        settings.last_calibration_at = 0
        settings.save()
        
        assert settings.should_calibrate() is True
    
    def test_record_review(self):
        """Тест записи ответа"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.create_for_user(user)
        
        settings.record_review(successful=True)
        assert settings.total_reviews == 1
        assert settings.successful_reviews == 1
        
        settings.record_review(successful=False)
        assert settings.total_reviews == 2
        assert settings.successful_reviews == 1


@pytest.mark.django_db
class TestUserTrainingSettingsSignals:
    """Тесты сигналов автосоздания"""
    
    def test_auto_create_on_user_creation(self):
        """Тест: при создании пользователя автоматически создаются настройки"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        settings = UserTrainingSettings.objects.filter(user=user).first()
        assert settings is not None
        assert settings.age_group == 'adult'


@pytest.mark.django_db
class TestUserTrainingSettingsAPI:
    """API-тесты для настроек тренировки"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.status = status
    
    def test_get_settings(self):
        """GET /api/training/settings/"""
        response = self.client.get('/api/training/settings/')
        
        assert response.status_code == self.status.HTTP_200_OK
        assert 'starting_ease' in response.data
        assert 'age_group' in response.data
    
    def test_update_settings(self):
        """PATCH /api/training/settings/"""
        data = {
            'starting_ease': 3.0,
            'interval_modifier': 1.2
        }
        
        response = self.client.patch('/api/training/settings/', data)
        
        assert response.status_code == self.status.HTTP_200_OK
        assert response.data['starting_ease'] == 3.0
        assert response.data['interval_modifier'] == 1.2
    
    def test_reset_settings(self):
        """POST /api/training/settings/reset/"""
        # Изменяем настройки
        settings = UserTrainingSettings.objects.get(user=self.user)
        settings.starting_ease = 3.0
        settings.save()
        
        # Сбрасываем
        response = self.client.post('/api/training/settings/reset/')
        
        assert response.status_code == self.status.HTTP_200_OK
        assert response.data['starting_ease'] == 2.5  # Значение по умолчанию
    
    def test_get_defaults(self):
        """GET /api/training/settings/defaults/?age_group=senior"""
        response = self.client.get('/api/training/settings/defaults/?age_group=senior')
        
        assert response.status_code == self.status.HTTP_200_OK
        assert response.data['age_group'] == 'senior'
        assert response.data['starting_ease'] == 2.3
```

---

## ✅ Definition of Done

- [ ] Приложение `training` создано и добавлено в `INSTALLED_APPS`
- [ ] Модель `UserTrainingSettings` создана с всеми полями
- [ ] Миграция успешно применена
- [ ] Сигнал автосоздания настроек работает
- [ ] Поле `age_group` добавлено в регистрацию
- [ ] Все API эндпоинты работают
- [ ] Сериализаторы возвращают корректные данные
- [ ] Метод `reset_to_defaults()` работает
- [ ] Метод `calibrate()` реализован (структура)
- [ ] Модель зарегистрирована в Django Admin
- [ ] TypeScript типы добавлены
- [ ] Все тесты проходят (25+ тестов)
- [ ] `python manage.py check` без ошибок

---

## 🔧 Команды

```bash
# Создание приложения
cd backend
python3 manage.py startapp training apps/training

# Создание миграции
python3 manage.py makemigrations training

# Применение миграции  
python3 manage.py migrate

# Проверка моделей
python3 manage.py check

# Запуск тестов
python3 -m pytest apps/training/tests.py -v

# Проверка покрытия
python3 -m pytest apps/training/tests.py -v --cov=apps.training --cov-report=term-missing
```

---

## 📝 Примечания

### Почему отдельное приложение?

1. **Разделение ответственности**: Настройки тренировки — отдельная функциональность
2. **Масштабируемость**: В будущем здесь будут алгоритмы SM-2, сессии, статистика
3. **Чистота архитектуры**: Не смешиваем с users или cards

### Инициализация по возрасту

При регистрации пользователь выбирает возрастную группу, которая влияет на начальные параметры. Это позволяет адаптировать алгоритм под возрастные особенности памяти.

### Калибровка

Метод `calibrate()` будет вызываться автоматически в этапе 5 (SM-2 Algorithm) после каждых N ответов. Сейчас реализована только структура метода.

### Сброс к умолчанию

Пользователь может сбросить все настройки к значениям по умолчанию для своей возрастной группы одной кнопкой. Это полезно, если пользователь экспериментировал с настройками.
