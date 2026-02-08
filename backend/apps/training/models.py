from datetime import time as dt_time

from django.db import models
from django.conf import settings
from django.utils import timezone


class NotificationSettings(models.Model):
    """
    Настройки уведомлений пользователя.
    Управляет типами и частотой уведомлений о тренировках.
    """

    FREQUENCY_CHOICES = [
        ('aggressive', 'Агрессивный (каждые 4 часа)'),
        ('normal', 'Обычный (2 раза в день)'),
        ('minimal', 'Минимальный (1 раз в день)'),
        ('off', 'Выключены'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name='Пользователь'
    )

    # Браузерные уведомления
    browser_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name='Уведомления в браузере',
        help_text='Показывать уведомления, когда приложение открыто'
    )
    notification_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='normal',
        verbose_name='Частота уведомлений'
    )

    # Триггеры
    notify_cards_due = models.BooleanField(
        default=True,
        verbose_name='Карточки готовы к повторению',
        help_text='Уведомлять когда есть карточки для повторения'
    )
    notify_streak_warning = models.BooleanField(
        default=True,
        verbose_name='Стрик в опасности',
        help_text='Предупреждать о потере стрика'
    )
    notify_daily_goal = models.BooleanField(
        default=True,
        verbose_name='Дневная цель',
        help_text='Напоминать о дневной цели'
    )

    # Порог карточек (минимум для уведомления)
    cards_due_threshold = models.IntegerField(
        default=5,
        verbose_name='Минимум карточек для уведомления',
        help_text='Уведомлять только если карточек >= этого числа'
    )

    # Тихие часы
    quiet_hours_start = models.TimeField(
        default=dt_time(22, 0),
        verbose_name='Начало тихих часов'
    )
    quiet_hours_end = models.TimeField(
        default=dt_time(8, 0),
        verbose_name='Конец тихих часов'
    )

    # Последнее уведомление
    last_notified_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Последнее уведомление'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Настройки уведомлений'
        verbose_name_plural = 'Настройки уведомлений'

    def __str__(self):
        return f"Уведомления: {self.user.username} ({self.notification_frequency})"

    def is_quiet_hours(self, current_time=None) -> bool:
        """Проверяет, сейчас ли тихие часы"""
        if current_time is None:
            current_time = timezone.localtime().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        if start <= end:
            return start <= current_time <= end
        else:
            # Ночной диапазон (22:00 - 08:00)
            return current_time >= start or current_time <= end

    def should_notify(self) -> bool:
        """Проверяет, нужно ли отправлять уведомление"""
        if self.notification_frequency == 'off':
            return False
        if self.is_quiet_hours():
            return False
        if not self.last_notified_at:
            return True

        now = timezone.now()
        hours_map = {
            'aggressive': 4,
            'normal': 12,
            'minimal': 24,
        }
        min_hours = hours_map.get(self.notification_frequency, 12)
        elapsed = (now - self.last_notified_at).total_seconds() / 3600
        return elapsed >= min_hours


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
    
    include_orphan_words = models.BooleanField(
        default=False,
        verbose_name='Включать слова без колоды в тренировку',
        help_text='Слова, не привязанные ни к одной колоде, попадают в общую тренировку'
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
        
        settings, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'age_group': age_group,
                **defaults
            }
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
        
        # Вычисляем процент успеха
        if self.total_reviews == 0:
            return {
                'calibrated': False,
                'message': 'Нет данных для калибровки'
            }
        
        success_rate = self.successful_reviews / self.total_reviews
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
