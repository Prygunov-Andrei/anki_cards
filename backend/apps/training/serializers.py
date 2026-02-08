import uuid
from rest_framework import serializers
from .models import UserTrainingSettings, NotificationSettings


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
            'include_orphan_words',
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
        # Проверяем относительно starting_ease, если он уже валидирован
        if hasattr(self, 'initial_data'):
            starting_ease = self.initial_data.get('starting_ease')
            if starting_ease and value > starting_ease:
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
            'include_orphan_words',
            'lapse_threshold',
            'stability_threshold',
            'calibration_interval',
            'target_retention',
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
        # Проверяем относительно starting_ease из instance или initial_data
        if self.instance:
            starting_ease = self.initial_data.get('starting_ease', self.instance.starting_ease)
            if starting_ease and value > starting_ease:
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


# ═══════════════════════════════════════════════════════════════
# ЭТАП 6: Training API Serializers
# ═══════════════════════════════════════════════════════════════

class TrainingSessionSerializer(serializers.Serializer):
    """Сериализатор для ответа GET /api/training/session/"""
    
    session_id = serializers.UUIDField()
    cards = serializers.ListField(child=serializers.DictField())
    estimated_time = serializers.IntegerField()
    new_count = serializers.IntegerField()
    review_count = serializers.IntegerField()
    learning_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


class TrainingAnswerRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса POST /api/training/answer/"""
    
    session_id = serializers.UUIDField(required=False)
    card_id = serializers.IntegerField(required=True)
    answer = serializers.IntegerField(min_value=0, max_value=3, required=True)
    time_spent = serializers.FloatField(required=False, min_value=0)
    
    def validate_answer(self, value):
        """Валидация ответа"""
        if value not in [0, 1, 2, 3]:
            raise serializers.ValidationError(
                "answer должен быть 0 (Again), 1 (Hard), 2 (Good) или 3 (Easy)"
            )
        return value


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
    card = serializers.DictField()


class CardActionRequestSerializer(serializers.Serializer):
    """Базовый сериализатор для enter-learning/exit-learning"""
    
    card_id = serializers.IntegerField(required=True)


class CardActionResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа enter-learning/exit-learning"""
    
    card_id = serializers.IntegerField()
    message = serializers.CharField()
    card = serializers.DictField()


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


# ═══════════════════════════════════════════════════════════════
# ЭТАП 7: AI Generation API Serializers
# ═══════════════════════════════════════════════════════════════

class GenerateEtymologyRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса POST /api/training/generate-etymology/"""
    
    word_id = serializers.IntegerField(required=True)
    force_regenerate = serializers.BooleanField(default=False, required=False)


class GenerateEtymologyResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа POST /api/training/generate-etymology/"""
    
    word_id = serializers.IntegerField()
    etymology = serializers.CharField()
    tokens_spent = serializers.IntegerField()
    balance_after = serializers.FloatField()


class GenerateHintRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса POST /api/training/generate-hint/"""
    
    word_id = serializers.IntegerField(required=True)
    force_regenerate = serializers.BooleanField(default=False, required=False)
    generate_audio = serializers.BooleanField(default=True, required=False)


class GenerateHintResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа POST /api/training/generate-hint/"""
    
    word_id = serializers.IntegerField()
    hint_text = serializers.CharField()
    hint_audio_url = serializers.CharField(required=False, allow_null=True)
    tokens_spent = serializers.IntegerField()
    balance_after = serializers.FloatField()


class GenerateSentenceRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса POST /api/training/generate-sentence/"""
    
    word_id = serializers.IntegerField(required=True)
    count = serializers.IntegerField(default=1, min_value=1, max_value=5, required=False)
    context = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate_count(self, value):
        """Валидация count"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("count должен быть от 1 до 5")
        return value


class GenerateSentenceResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа POST /api/training/generate-sentence/"""
    
    word_id = serializers.IntegerField()
    sentences = serializers.ListField(child=serializers.CharField())
    tokens_spent = serializers.IntegerField()
    balance_after = serializers.FloatField()


class GenerateSynonymRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса POST /api/training/generate-synonym/"""
    
    word_id = serializers.IntegerField(required=True)
    create_card = serializers.BooleanField(default=True, required=False)


class GenerateSynonymResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа POST /api/training/generate-synonym/"""
    
    original_word_id = serializers.IntegerField()
    synonym_word = serializers.DictField()
    relation_created = serializers.BooleanField()
    tokens_spent = serializers.IntegerField()
    balance_after = serializers.FloatField()


# ═══════════════════════════════════════════════════════════════
# Этап 13: Уведомления
# ═══════════════════════════════════════════════════════════════

class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор настроек уведомлений"""

    frequency_display = serializers.CharField(
        source='get_notification_frequency_display',
        read_only=True
    )

    class Meta:
        model = NotificationSettings
        fields = [
            'browser_notifications_enabled',
            'notification_frequency',
            'frequency_display',
            'notify_cards_due',
            'notify_streak_warning',
            'notify_daily_goal',
            'cards_due_threshold',
            'quiet_hours_start',
            'quiet_hours_end',
        ]

    def validate_cards_due_threshold(self, value):
        if value < 1:
            raise serializers.ValidationError("Минимум 1 карточка")
        if value > 500:
            raise serializers.ValidationError("Максимум 500 карточек")
        return value


class NotificationCheckResponseSerializer(serializers.Serializer):
    """Ответ на проверку уведомлений"""
    should_notify = serializers.BooleanField()
    cards_due = serializers.IntegerField()
    streak_at_risk = serializers.BooleanField()
    message = serializers.CharField(allow_blank=True)
    notification_type = serializers.CharField()
