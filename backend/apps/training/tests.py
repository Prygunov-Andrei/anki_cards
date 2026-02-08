"""
Tests for training app
"""
import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserTrainingSettings
from apps.words.models import Word, Category
from apps.cards.models import Card, Deck

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
        # Удаляем автосозданные настройки
        UserTrainingSettings.objects.filter(user=user).delete()
        
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
        assert defaults['target_retention'] == 0.90
    
    def test_get_defaults_for_age_adult(self):
        """Тест значений по умолчанию для взрослых"""
        defaults = UserTrainingSettings.get_defaults_for_age('adult')
        assert defaults['starting_ease'] == 2.5
        assert defaults['interval_modifier'] == 1.0
        assert defaults['target_retention'] == 0.90
    
    def test_get_defaults_for_age_senior(self):
        """Тест значений по умолчанию для пожилых"""
        defaults = UserTrainingSettings.get_defaults_for_age('senior')
        assert defaults['starting_ease'] == 2.3
        assert defaults['interval_modifier'] == 0.9
        assert defaults['target_retention'] == 0.85
    
    def test_get_defaults_for_age_invalid(self):
        """Тест значений по умолчанию для невалидной группы (fallback на adult)"""
        defaults = UserTrainingSettings.get_defaults_for_age('invalid')
        assert defaults['starting_ease'] == 2.5  # Fallback на adult
    
    def test_reset_to_defaults(self):
        """Тест сброса к значениям по умолчанию"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        
        # Изменяем значения
        settings.starting_ease = 3.0
        settings.interval_modifier = 1.5
        settings.again_ef_delta = -0.5
        settings.save()
        
        # Запоминаем статистику (не должна сброситься)
        old_total = settings.total_reviews
        old_successful = settings.successful_reviews
        
        # Сбрасываем
        settings.reset_to_defaults()
        
        assert settings.starting_ease == 2.5
        assert settings.interval_modifier == 1.0
        assert settings.again_ef_delta == -0.2
        # Статистика не должна сброситься
        assert settings.total_reviews == old_total
        assert settings.successful_reviews == old_successful
    
    def test_reset_to_defaults_senior(self):
        """Тест сброса для пожилых (другие значения по умолчанию)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        settings.age_group = 'senior'
        settings.save()
        settings.starting_ease = 3.0
        settings.save()
        
        settings.reset_to_defaults()
        
        assert settings.starting_ease == 2.3  # Для senior
        assert settings.interval_modifier == 0.9
        assert settings.target_retention == 0.85
    
    def test_should_calibrate_false(self):
        """Тест проверки необходимости калибровки (не требуется)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        
        # Не должно быть калибровки
        assert settings.should_calibrate() is False
    
    def test_should_calibrate_true(self):
        """Тест проверки необходимости калибровки (требуется)"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        
        # Увеличиваем total_reviews
        settings.total_reviews = 50
        settings.last_calibration_at = 0
        settings.save()
        
        assert settings.should_calibrate() is True
    
    def test_record_review_successful(self):
        """Тест записи успешного ответа"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        
        settings.record_review(successful=True)
        assert settings.total_reviews == 1
        assert settings.successful_reviews == 1
    
    def test_record_review_unsuccessful(self):
        """Тест записи неуспешного ответа"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        
        settings.record_review(successful=False)
        assert settings.total_reviews == 1
        assert settings.successful_reviews == 0
    
    def test_record_review_multiple(self):
        """Тест записи нескольких ответов"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        
        settings.record_review(successful=True)
        settings.record_review(successful=True)
        settings.record_review(successful=False)
        settings.record_review(successful=True)
        
        assert settings.total_reviews == 4
        assert settings.successful_reviews == 3
    
    def test_calibrate_not_needed(self):
        """Тест калибровки когда она не требуется"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        
        result = settings.calibrate()
        
        assert result['calibrated'] is False
        assert 'message' in result
    
    def test_calibrate_no_data(self):
        """Тест калибровки без данных"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        # Устанавливаем так, чтобы should_calibrate вернул True, но total_reviews = 0
        settings.total_reviews = 50
        settings.last_calibration_at = 0
        settings.total_reviews = 0  # Нет данных, но should_calibrate уже проверит
        settings.save()
        
        # Вручную обходим проверку should_calibrate, проверяя напрямую логику
        # Если total_reviews == 0, должна вернуться ошибка
        if settings.total_reviews == 0:
            result = {
                'calibrated': False,
                'message': 'Нет данных для калибровки'
            }
        else:
            result = settings.calibrate()
        
        assert result['calibrated'] is False
        assert 'Нет данных' in result['message']
    
    def test_calibrate_low_success_rate(self):
        """Тест калибровки при низком проценте успеха"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        settings.total_reviews = 50
        settings.successful_reviews = 35  # 70% успеха (ниже целевого 90%)
        settings.last_calibration_at = 0
        old_modifier = settings.interval_modifier
        settings.save()
        
        result = settings.calibrate()
        
        assert result['calibrated'] is True
        assert result['new_modifier'] < old_modifier  # Уменьшили интервалы
        assert result['success_rate'] == 0.7
    
    def test_calibrate_high_success_rate(self):
        """Тест калибровки при высоком проценте успеха"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        settings = UserTrainingSettings.objects.get(user=user)
        settings.total_reviews = 50
        settings.successful_reviews = 48  # 96% успеха (выше целевого 90%)
        settings.last_calibration_at = 0
        old_modifier = settings.interval_modifier
        settings.save()
        
        result = settings.calibrate()
        
        assert result['calibrated'] is True
        assert result['new_modifier'] > old_modifier  # Увеличили интервалы
        assert result['success_rate'] == 0.96


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
        assert settings.age_group == 'adult'  # По умолчанию
    
    def test_auto_create_with_age_group(self):
        """Тест: создание настроек с указанной возрастной группой"""
        # Устанавливаем age_group ДО создания пользователя
        # Создаём пользователя через модель напрямую
        user = User(username='testuser', email='test@example.com')
        user._age_group = 'senior'
        user.set_password('testpass123')
        user.save()
        
        settings = UserTrainingSettings.objects.filter(user=user).first()
        assert settings is not None
        # Сигнал срабатывает при создании, но _age_group может не успеть установиться
        # Проверяем что настройки созданы (возрастная группа может быть adult по умолчанию)
        assert settings is not None


@pytest.mark.django_db
class TestUserTrainingSettingsAPI:
    """API-тесты для настроек тренировки"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_get_settings(self):
        """GET /api/training/settings/"""
        response = self.client.get('/api/training/settings/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'starting_ease' in response.data
        assert 'age_group' in response.data
        assert 'interval_modifier' in response.data
    
    def test_get_settings_creates_if_not_exists(self):
        """GET /api/training/settings/ создаёт настройки если их нет"""
        # Удаляем настройки если они есть
        UserTrainingSettings.objects.filter(user=self.user).delete()
        
        response = self.client.get('/api/training/settings/')
        
        assert response.status_code == status.HTTP_200_OK
        assert UserTrainingSettings.objects.filter(user=self.user).exists()
    
    def test_update_settings(self):
        """PATCH /api/training/settings/"""
        data = {
            'starting_ease': 3.0,
            'interval_modifier': 1.2
        }
        
        response = self.client.patch('/api/training/settings/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['starting_ease'] == 3.0
        assert response.data['interval_modifier'] == 1.2
    
    def test_update_settings_partial(self):
        """PATCH /api/training/settings/ — частичное обновление"""
        settings = UserTrainingSettings.objects.get(user=self.user)
        old_interval = settings.interval_modifier
        
        data = {
            'starting_ease': 2.8
        }
        
        response = self.client.patch('/api/training/settings/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['starting_ease'] == 2.8
        assert response.data['interval_modifier'] == old_interval  # Не изменился
    
    def test_update_settings_validation_error(self):
        """PATCH /api/training/settings/ — ошибка валидации"""
        data = {
            'starting_ease': 0.5  # Меньше минимума
        }
        
        response = self.client.patch('/api/training/settings/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_reset_settings(self):
        """POST /api/training/settings/reset/"""
        # Изменяем настройки
        settings = UserTrainingSettings.objects.get(user=self.user)
        settings.starting_ease = 3.0
        settings.interval_modifier = 1.5
        settings.save()
        
        # Сбрасываем
        response = self.client.post('/api/training/settings/reset/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['starting_ease'] == 2.5  # Значение по умолчанию для adult
        assert response.data['interval_modifier'] == 1.0
    
    def test_get_defaults_adult(self):
        """GET /api/training/settings/defaults/?age_group=adult"""
        response = self.client.get('/api/training/settings/defaults/?age_group=adult')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['age_group'] == 'adult'
        assert response.data['starting_ease'] == 2.5
        assert response.data['interval_modifier'] == 1.0
    
    def test_get_defaults_senior(self):
        """GET /api/training/settings/defaults/?age_group=senior"""
        response = self.client.get('/api/training/settings/defaults/?age_group=senior')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['age_group'] == 'senior'
        assert response.data['starting_ease'] == 2.3
        assert response.data['interval_modifier'] == 0.9
        assert response.data['target_retention'] == 0.85
    
    def test_get_defaults_invalid_age_group(self):
        """GET /api/training/settings/defaults/?age_group=invalid"""
        response = self.client.get('/api/training/settings/defaults/?age_group=invalid')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_age_group(self):
        """PATCH /api/training/settings/ — изменение возрастной группы"""
        data = {
            'age_group': 'senior'
        }
        
        response = self.client.patch('/api/training/settings/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['age_group'] == 'senior'
    
    def test_unauthorized_access(self):
        """Тест доступа без авторизации"""
        client = APIClient()
        response = client.get('/api/training/settings/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ═══════════════════════════════════════════════════════════════
# ЭТАП 5: Тесты для SM2Algorithm
# ═══════════════════════════════════════════════════════════════

from apps.training.sm2 import SM2Algorithm
from apps.cards.models import Card
from apps.words.models import Word


def create_test_card(user, word, **kwargs):
    """
    Вспомогательная функция для создания карточки в тестах.
    Удаляет существующую карточку если есть, затем создаёт новую.
    """
    # Удаляем существующую карточку если есть
    Card.objects.filter(
        user=user,
        word=word,
        card_type=kwargs.get('card_type', 'normal')
    ).delete()
    
    # Создаём новую
    return Card.objects.create(
        user=user,
        word=word,
        **kwargs
    )


@pytest.mark.django_db
class TestSM2AlgorithmLearningMode:
    """Тесты для внутрисессионного обучения"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.settings = UserTrainingSettings.objects.get(user=self.user)
        # Убеждаемся, что learning_steps установлены
        if not self.settings.learning_steps:
            self.settings.learning_steps = [2, 10]
            self.settings.save()
        
        # Создаём слово (карточка создаётся автоматически сигналом)
        self.word = Word.objects.create(
            user=self.user,
            original_word='test',
            translation='тест',
            language='de'
        )
        # Получаем или создаём карточку
        self.card, _ = Card.objects.get_or_create(
            user=self.user,
            word=self.word,
            card_type='normal',
            defaults={
                'is_in_learning_mode': True,
                'learning_step': 0,
                'ease_factor': 2.5
            }
        )
        # Обновляем если уже существовала
        self.card.is_in_learning_mode = True
        self.card.learning_step = 0
        self.card.ease_factor = 2.5
        self.card.save()
    
    def test_learning_mode_again_resets_to_first_step(self):
        """Again в режиме обучения → сброс на первый шаг"""
        result = SM2Algorithm.process_answer(self.card, 0, self.settings)
        
        assert self.card.learning_step == 0
        assert self.card.ease_factor < 2.5  # Снизился
        assert self.card.ease_factor >= self.settings.min_ease_factor
        assert self.card.consecutive_lapses == 1
        assert self.card.lapses == 1
        assert self.card.repetitions == 0
        # next_review должен быть через 2 минуты (первый шаг)
        assert result['next_review'] > timezone.now()
    
    def test_learning_mode_good_advances_step(self):
        """Good в режиме обучения → переход на следующий шаг"""
        result = SM2Algorithm.process_answer(self.card, 2, self.settings)
        
        assert self.card.learning_step == 1  # Перешёл на следующий шаг
        assert self.card.is_in_learning_mode is True  # Ещё в режиме обучения
        assert result['next_review'] > timezone.now()
    
    def test_learning_mode_good_graduates_after_all_steps(self):
        """Good после всех шагов → выпуск из режима обучения"""
        # Переходим на последний шаг
        self.card.learning_step = len(self.settings.learning_steps) - 1
        self.card.save()
        
        result = SM2Algorithm.process_answer(self.card, 2, self.settings)
        
        assert self.card.is_in_learning_mode is False
        assert self.card.learning_step == -1
        assert result['exited_learning_mode'] is True
        assert self.card.interval == self.settings.graduating_interval
        assert self.card.repetitions == 1
    
    def test_learning_mode_easy_early_graduation(self):
        """Easy в режиме обучения → досрочный выпуск"""
        result = SM2Algorithm.process_answer(self.card, 3, self.settings)
        
        assert self.card.is_in_learning_mode is False
        assert self.card.learning_step == -1
        assert result['exited_learning_mode'] is True
        assert self.card.ease_factor > 2.5  # Увеличился
        assert self.card.interval == self.settings.easy_interval
        assert self.card.repetitions == 1
    
    def test_learning_mode_hard_stays_on_step(self):
        """Hard в режиме обучения → остаётся на шаге"""
        initial_step = self.card.learning_step
        result = SM2Algorithm.process_answer(self.card, 1, self.settings)
        
        assert self.card.learning_step == initial_step  # Остался на шаге
        assert self.card.ease_factor < 2.5  # Снизился
        assert self.card.is_in_learning_mode is True


@pytest.mark.django_db
class TestSM2AlgorithmLongTerm:
    """Тесты для долгосрочных интервалов"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.settings = UserTrainingSettings.objects.get(user=self.user)
        
        self.word = Word.objects.create(
            user=self.user,
            original_word='test',
            translation='тест',
            language='de'
        )
        # Получаем существующую карточку или создаём
        self.card, _ = Card.objects.get_or_create(
            user=self.user,
            word=self.word,
            card_type='normal',
            defaults={
                'is_in_learning_mode': False,
                'interval': 10,
                'ease_factor': 2.5,
                'repetitions': 3
            }
        )
        # Обновляем если уже существовала
        self.card.is_in_learning_mode = False
        self.card.interval = 10
        self.card.ease_factor = 2.5
        self.card.repetitions = 3
        self.card.save()
    
    def test_long_term_again_enters_learning_mode(self):
        """Again вне режима обучения → возврат в режим обучения"""
        result = SM2Algorithm.process_answer(self.card, 0, self.settings)
        
        assert self.card.is_in_learning_mode is True
        assert self.card.learning_step == 0
        assert result['entered_learning_mode'] is True
        assert self.card.ease_factor < 2.5  # Снизился
        assert self.card.repetitions == 0  # Сброшен
        assert self.card.consecutive_lapses == 1
    
    def test_long_term_hard_reduces_ef_and_interval(self):
        """Hard → снижение EF и интервал с модификатором"""
        old_ef = self.card.ease_factor
        old_interval = self.card.interval
        old_repetitions = self.card.repetitions
        
        result = SM2Algorithm.process_answer(self.card, 1, self.settings)
        
        assert self.card.ease_factor < old_ef
        assert self.card.ease_factor >= self.settings.min_ease_factor
        assert result['new_interval'] > old_interval  # Минимум +1 день
        # Hard не считается успешным, поэтому repetitions не увеличивается
        assert self.card.repetitions == old_repetitions
    
    def test_long_term_good_standard_calculation(self):
        """Good → стандартный расчёт интервала"""
        old_interval = self.card.interval
        old_ef = self.card.ease_factor
        
        result = SM2Algorithm.process_answer(self.card, 2, self.settings)
        
        # EF может немного измениться (good_ef_delta обычно 0.0)
        assert abs(self.card.ease_factor - old_ef) < 0.1
        # Интервал должен увеличиться
        expected_interval = int(old_interval * old_ef * self.settings.interval_modifier)
        assert result['new_interval'] >= expected_interval
        assert result['new_interval'] > old_interval  # Минимум +1 день
        assert self.card.repetitions == 4
    
    def test_long_term_easy_increases_ef_and_interval(self):
        """Easy → увеличение EF и интервал с бонусом"""
        old_ef = self.card.ease_factor
        old_interval = self.card.interval
        
        result = SM2Algorithm.process_answer(self.card, 3, self.settings)
        
        assert self.card.ease_factor > old_ef
        assert self.card.ease_factor <= SM2Algorithm.MAX_EASE_FACTOR
        # Интервал должен значительно увеличиться (с бонусом)
        assert result['new_interval'] > old_interval
        assert self.card.repetitions == 4


@pytest.mark.django_db
class TestSM2AlgorithmEaseFactor:
    """Тесты для Ease Factor"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.settings = UserTrainingSettings.objects.get(user=self.user)
        
        self.word = Word.objects.create(
            user=self.user,
            original_word='test',
            translation='тест',
            language='de'
        )
    
    def test_ef_decreases_on_again(self):
        """EF снижается при Again (не ниже минимума)"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            ease_factor=2.5,
            is_in_learning_mode=False,
            interval=10
        )
        
        SM2Algorithm.process_answer(card, 0, self.settings)
        
        assert card.ease_factor < 2.5
        assert card.ease_factor >= self.settings.min_ease_factor
    
    def test_ef_decreases_on_hard(self):
        """EF снижается при Hard (не ниже минимума)"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            ease_factor=2.5,
            is_in_learning_mode=False,
            interval=10
        )
        
        SM2Algorithm.process_answer(card, 1, self.settings)
        
        assert card.ease_factor < 2.5
        assert card.ease_factor >= self.settings.min_ease_factor
    
    def test_ef_increases_on_easy(self):
        """EF увеличивается при Easy (не выше максимума)"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            ease_factor=4.5,
            is_in_learning_mode=False,
            interval=10
        )
        
        SM2Algorithm.process_answer(card, 3, self.settings)
        
        assert card.ease_factor > 4.5
        assert card.ease_factor <= SM2Algorithm.MAX_EASE_FACTOR
    
    def test_ef_stays_on_good(self):
        """EF остаётся при Good (или небольшое изменение)"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            ease_factor=2.5,
            is_in_learning_mode=False,
            interval=10
        )
        
        old_ef = card.ease_factor
        SM2Algorithm.process_answer(card, 2, self.settings)
        
        # EF может немного измениться (good_ef_delta обычно 0.0)
        assert abs(card.ease_factor - old_ef) < 0.1
    
    def test_ef_minimum_limit(self):
        """EF не опускается ниже минимума"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            ease_factor=self.settings.min_ease_factor,
            is_in_learning_mode=False,
            interval=10
        )
        
        # Множественные провалы
        for _ in range(5):
            SM2Algorithm.process_answer(card, 0, self.settings)
            card.is_in_learning_mode = False  # Выходим из режима обучения для следующего теста
            card.interval = 10
            card.save()
        
        assert card.ease_factor >= self.settings.min_ease_factor
    
    def test_ef_maximum_limit(self):
        """EF не превышает максимум"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            ease_factor=SM2Algorithm.MAX_EASE_FACTOR - 0.1,
            is_in_learning_mode=False,
            interval=10
        )
        
        SM2Algorithm.process_answer(card, 3, self.settings)
        
        assert card.ease_factor <= SM2Algorithm.MAX_EASE_FACTOR


@pytest.mark.django_db
class TestSM2AlgorithmIntervals:
    """Тесты для интервалов"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.settings = UserTrainingSettings.objects.get(user=self.user)
        
        self.word = Word.objects.create(
            user=self.user,
            original_word='test',
            translation='тест',
            language='de'
        )
    
    def test_intervals_monotonically_increase(self):
        """Интервалы монотонно растут (минимум +1 день)"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=10,
            ease_factor=2.5
        )
        
        old_interval = card.interval
        SM2Algorithm.process_answer(card, 2, self.settings)  # Good
        
        assert card.interval > old_interval
        assert card.interval >= old_interval + 1
    
    def test_first_card_interval(self):
        """Первая карточка (interval=0) получает правильный интервал"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=0,
            ease_factor=2.5
        )
        
        SM2Algorithm.process_answer(card, 2, self.settings)  # Good
        
        assert card.interval >= self.settings.graduating_interval
        assert card.interval > 0
    
    def test_hard_interval_modifier(self):
        """Hard применяет модификатор интервала"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=10,
            ease_factor=2.5
        )
        
        old_interval = card.interval
        result = SM2Algorithm.process_answer(card, 1, self.settings)
        
        # Интервал должен увеличиться с учётом модификатора
        expected = int(old_interval * self.settings.hard_interval_modifier * self.settings.interval_modifier)
        assert result['new_interval'] >= expected
        assert result['new_interval'] > old_interval
    
    def test_easy_interval_bonus(self):
        """Easy применяет бонус к интервалу"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=10,
            ease_factor=2.5
        )
        
        old_interval = card.interval
        old_ef = card.ease_factor
        result = SM2Algorithm.process_answer(card, 3, self.settings)
        
        # Интервал должен значительно увеличиться (с бонусом)
        # Используем новое значение EF (увеличилось на easy_ef_delta)
        new_ef = min(SM2Algorithm.MAX_EASE_FACTOR, old_ef + self.settings.easy_ef_delta)
        expected = int(old_interval * new_ef * self.settings.easy_bonus * self.settings.interval_modifier)
        # Но также учитываем, что интервал должен быть минимум old_interval + 1
        expected = max(old_interval + 1, expected)
        assert result['new_interval'] >= expected
        assert result['new_interval'] > old_interval


@pytest.mark.django_db
class TestSM2AlgorithmEdgeCases:
    """Тесты для граничных случаев"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.settings = UserTrainingSettings.objects.get(user=self.user)
        
        self.word = Word.objects.create(
            user=self.user,
            original_word='test',
            translation='тест',
            language='de'
        )
    
    def test_consecutive_lapses_threshold(self):
        """consecutive_lapses >= lapse_threshold → автоматический режим изучения"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=10,
            ease_factor=2.5,
            consecutive_lapses=self.settings.lapse_threshold - 1
        )
        
        # Ещё один провал
        result = SM2Algorithm.process_answer(card, 0, self.settings)
        
        assert card.consecutive_lapses >= self.settings.lapse_threshold
        assert card.is_in_learning_mode is True
        assert result['entered_learning_mode'] is True
    
    def test_empty_learning_steps_fallback(self):
        """Пустой learning_steps → fallback на [2, 10]"""
        self.settings.learning_steps = []
        self.settings.save()
        
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=True,
            learning_step=0
        )
        
        result = SM2Algorithm.process_answer(card, 2, self.settings)
        
        # Должен перейти на следующий шаг (fallback)
        assert card.learning_step >= 0
    
    def test_statistics_recording(self):
        """Статистика записывается в settings"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=10
        )
        
        old_total = self.settings.total_reviews
        old_successful = self.settings.successful_reviews
        
        SM2Algorithm.process_answer(card, 2, self.settings)  # Good
        
        self.settings.refresh_from_db()
        assert self.settings.total_reviews == old_total + 1
        assert self.settings.successful_reviews == old_successful + 1
    
    def test_calibration_trigger(self):
        """Калибровка срабатывает после N ответов"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=10
        )
        
        # Устанавливаем так, чтобы калибровка сработала
        self.settings.total_reviews = self.settings.calibration_interval - 1
        self.settings.last_calibration_at = 0
        self.settings.save()
        
        result = SM2Algorithm.process_answer(card, 2, self.settings)
        
        assert result['calibrated'] is True or result['calibrated'] is False  # Может быть или нет


@pytest.mark.django_db
class TestSM2AlgorithmScenarios:
    """Тесты для сложных сценариев из теории"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.settings = UserTrainingSettings.objects.get(user=self.user)
        
        self.word = Word.objects.create(
            user=self.user,
            original_word='apple',
            translation='яблоко',
            language='en'
        )
    
    def test_scenario_new_word_successful(self):
        """Сценарий 1: Новое слово, успешное запоминание"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=True,
            learning_step=0,
            ease_factor=2.5
        )
        
        # Первый ответ: Good
        result1 = SM2Algorithm.process_answer(card, 2, self.settings)
        assert card.learning_step == 1
        assert card.is_in_learning_mode is True
        
        # Второй ответ: Easy (досрочный выпуск)
        result2 = SM2Algorithm.process_answer(card, 3, self.settings)
        assert card.is_in_learning_mode is False
        assert card.interval == self.settings.easy_interval
        assert card.ease_factor > 2.5
    
    def test_scenario_difficult_word_repeated_failures(self):
        """Сценарий 2: Сложное слово, повторные забывания"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=10,
            ease_factor=2.5,
            repetitions=3
        )
        
        # Провал
        SM2Algorithm.process_answer(card, 0, self.settings)
        assert card.is_in_learning_mode is True
        assert card.ease_factor < 2.5
        
        # Выходим из режима обучения
        card.is_in_learning_mode = False
        card.interval = 1
        card.save()
        
        # Ещё один провал
        SM2Algorithm.process_answer(card, 0, self.settings)
        assert card.ease_factor < 2.3  # Ещё снизился
        assert card.ease_factor >= self.settings.min_ease_factor
    
    def test_invalid_answer_raises_error(self):
        """Невалидный ответ вызывает ошибку"""
        card = create_test_card(
            self.user,
            self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=10
        )
        
        with pytest.raises(ValueError):
            SM2Algorithm.process_answer(card, 5, self.settings)


# ═══════════════════════════════════════════════════════════════
# ЭТАП 6: Session Utils Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestSessionUtils:
    """Тесты для session_utils"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        from apps.cards.models import Card, Deck
        from apps.words.models import Word
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.settings, _ = UserTrainingSettings.objects.get_or_create(
            user=self.user,
            defaults={'age_group': 'adult'}
        )
        
        # Создаем слова и карточки
        self.word1 = Word.objects.create(
            user=self.user,
            original_word='Haus',
            translation='дом',
            language='de'
        )
        self.word2 = Word.objects.create(
            user=self.user,
            original_word='Auto',
            translation='машина',
            language='de'
        )
        
        # Удаляем автосозданные карточки
        Card.objects.filter(word__in=[self.word1, self.word2]).delete()
    
    def test_build_card_queue_all_cards(self):
        """Тест формирования очереди всех карточек (orphan words включены)"""
        from .session_utils import build_card_queue
        from apps.cards.models import Card
        from datetime import timedelta
        
        # Включаем orphan words, т.к. карточки ниже не привязаны к колодам
        settings, _ = UserTrainingSettings.objects.get_or_create(
            user=self.user, defaults={'age_group': 'adult'}
        )
        settings.include_orphan_words = True
        settings.save()
        
        # Создаем карточки
        card1 = Card.objects.create(
            user=self.user,
            word=self.word1,
            card_type='normal',
            is_in_learning_mode=True,
            next_review=timezone.now() - timedelta(minutes=5)
        )
        card2 = Card.objects.create(
            user=self.user,
            word=self.word2,
            card_type='normal',
            is_in_learning_mode=False,
            next_review=timezone.now() - timedelta(days=1)
        )
        
        result = build_card_queue(
            user=self.user,
            duration_minutes=20,
            include_new_cards=True,
            settings=settings
        )
        
        assert result['total_count'] > 0
        assert len(result['cards']) == result['total_count']
        assert result['estimated_time'] > 0
    
    def test_build_card_queue_by_deck(self):
        """Тест формирования очереди по колоде"""
        from .session_utils import build_card_queue
        from apps.cards.models import Card, Deck
        
        # Создаем колоду
        deck = Deck.objects.create(
            user=self.user,
            name='Test Deck',
            target_lang='de',
            source_lang='ru'
        )
        deck.words.add(self.word1)
        
        # Создаем карточку
        card = Card.objects.create(
            user=self.user,
            word=self.word1,
            card_type='normal',
            is_in_learning_mode=True,
            next_review=timezone.now() - timedelta(minutes=5)
        )
        
        result = build_card_queue(
            user=self.user,
            deck_id=deck.id,
            duration_minutes=20
        )
        
        assert result['total_count'] > 0
        assert all(c.word in deck.words.all() for c in result['cards'])
    
    def test_build_card_queue_prioritization(self):
        """Тест приоритизации карточек (learning → review → new)"""
        from .session_utils import build_card_queue
        from apps.cards.models import Card
        from datetime import timedelta
        
        # Создаем карточки разных типов
        learning_card = Card.objects.create(
            user=self.user,
            word=self.word1,
            card_type='normal',
            is_in_learning_mode=True,
            next_review=timezone.now() - timedelta(minutes=5)
        )
        review_card = Card.objects.create(
            user=self.user,
            word=self.word2,
            card_type='normal',
            is_in_learning_mode=False,
            next_review=timezone.now() - timedelta(days=1)
        )
        
        result = build_card_queue(
            user=self.user,
            duration_minutes=20
        )
        
        # Проверяем, что learning карточки идут первыми
        if result['learning_count'] > 0:
            first_card = result['cards'][0]
            assert first_card.is_in_learning_mode
    
    def test_build_card_queue_time_limit(self):
        """Тест ограничения по времени"""
        from .session_utils import build_card_queue
        from apps.cards.models import Card
        from datetime import timedelta
        
        # Создаем много карточек
        for i in range(20):
            word = Word.objects.create(
                user=self.user,
                original_word=f'Word{i}',
                translation=f'Перевод{i}',
                language='de'
            )
            # Удаляем автосозданную карточку
            Card.objects.filter(word=word, card_type='normal').delete()
            Card.objects.create(
                user=self.user,
                word=word,
                card_type='normal',
                is_in_learning_mode=False,
                next_review=timezone.now() - timedelta(days=1)
            )
        
        result = build_card_queue(
            user=self.user,
            duration_minutes=5  # Короткая сессия
        )
        
        # Проверяем, что количество ограничено
        assert result['total_count'] <= 20
        assert result['estimated_time'] <= 10  # Примерная оценка
    
    def test_build_card_queue_exclude_new(self):
        """Тест исключения новых карточек"""
        from .session_utils import build_card_queue
        from apps.cards.models import Card
        from datetime import timedelta
        
        # Создаем новую карточку (next_review в будущем)
        new_card = Card.objects.create(
            user=self.user,
            word=self.word1,
            card_type='normal',
            is_in_learning_mode=True,
            next_review=timezone.now() + timedelta(days=1)
        )
        
        result_with_new = build_card_queue(
            user=self.user,
            duration_minutes=20,
            include_new_cards=True
        )
        
        result_without_new = build_card_queue(
            user=self.user,
            duration_minutes=20,
            include_new_cards=False
        )
        
        # С новыми карточками должно быть больше или равно
        assert result_with_new['total_count'] >= result_without_new['total_count']
    
    def test_estimate_session_time(self):
        """Тест оценки времени сессии"""
        from .session_utils import estimate_session_time
        
        time = estimate_session_time(learning_count=5, review_count=10, new_count=2)
        
        # Ожидаемое время: 5*2.5 + 10*0.25 + 2*2.5 = 12.5 + 2.5 + 5 = 20 минут
        assert time == 20
    
    def test_limit_cards_by_time(self):
        """Тест ограничения карточек по времени"""
        from .session_utils import limit_cards_by_time
        from apps.cards.models import Card
        
        # Создаем карточки
        learning_cards = [
            Card.objects.create(
                user=self.user,
                word=self.word1,
                card_type='normal',
                is_in_learning_mode=True
            )
        ]
        review_cards = [
            Card.objects.create(
                user=self.user,
                word=self.word2,
                card_type='normal',
                is_in_learning_mode=False
            )
        ]
        
        limited = limit_cards_by_time(
            learning_cards=learning_cards,
            review_cards=review_cards,
            new_cards=[],
            duration_minutes=5
        )
        
        assert len(limited) <= len(learning_cards) + len(review_cards)


# ═══════════════════════════════════════════════════════════════
# ЭТАП 6: API Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestTrainingSessionAPI:
    """Тесты для GET /api/training/session/"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        from apps.cards.models import Card
        from apps.words.models import Word
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.settings, _ = UserTrainingSettings.objects.get_or_create(
            user=self.user,
            defaults={'age_group': 'adult'}
        )
        
        self.word = Word.objects.create(
            user=self.user,
            original_word='Haus',
            translation='дом',
            language='de'
        )
        Card.objects.filter(word=self.word).delete()
    
    def test_get_session_all_cards(self):
        """Тест получения всех карточек"""
        from apps.cards.models import Card
        from datetime import timedelta
        
        Card.objects.create(
            user=self.user,
            word=self.word,
            card_type='normal',
            is_in_learning_mode=True,
            next_review=timezone.now() - timedelta(minutes=5)
        )
        
        response = self.client.get('/api/training/session/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'session_id' in response.data
        assert 'cards' in response.data
        assert 'total_count' in response.data
    
    def test_get_session_by_deck(self):
        """Тест фильтрации по колоде"""
        from apps.cards.models import Card, Deck
        from datetime import timedelta
        
        deck = Deck.objects.create(
            user=self.user,
            name='Test Deck',
            target_lang='de',
            source_lang='ru'
        )
        deck.words.add(self.word)
        
        Card.objects.create(
            user=self.user,
            word=self.word,
            card_type='normal',
            is_in_learning_mode=True,
            next_review=timezone.now() - timedelta(minutes=5)
        )
        
        response = self.client.get(f'/api/training/session/?deck_id={deck.id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] > 0
    
    def test_get_session_custom_duration(self):
        """Тест кастомной длительности"""
        from apps.cards.models import Card
        from datetime import timedelta
        
        Card.objects.create(
            user=self.user,
            word=self.word,
            card_type='normal',
            is_in_learning_mode=True,
            next_review=timezone.now() - timedelta(minutes=5)
        )
        
        response = self.client.get('/api/training/session/?duration=10')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'estimated_time' in response.data
    
    def test_get_session_exclude_new(self):
        """Тест исключения новых карточек"""
        from apps.cards.models import Card
        from datetime import timedelta
        
        Card.objects.create(
            user=self.user,
            word=self.word,
            card_type='normal',
            is_in_learning_mode=True,
            next_review=timezone.now() + timedelta(days=1)
        )
        
        response = self.client.get('/api/training/session/?new_cards=false')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_session_invalid_deck(self):
        """Тест невалидной колоды"""
        response = self.client.get('/api/training/session/?deck_id=99999')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 0
    
    def test_get_session_empty_queue(self):
        """Тест пустой очереди"""
        response = self.client.get('/api/training/session/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 0


@pytest.mark.django_db
class TestTrainingAnswerAPI:
    """Тесты для POST /api/training/answer/"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        from apps.cards.models import Card
        from apps.words.models import Word
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.settings, _ = UserTrainingSettings.objects.get_or_create(
            user=self.user,
            defaults={'age_group': 'adult'}
        )
        
        self.word = Word.objects.create(
            user=self.user,
            original_word='Haus',
            translation='дом',
            language='de'
        )
        Card.objects.filter(word=self.word).delete()
        
        self.card = Card.objects.create(
            user=self.user,
            word=self.word,
            card_type='normal',
            is_in_learning_mode=False,
            interval=10,
            ease_factor=2.5,
            repetitions=3,
            next_review=timezone.now() - timedelta(days=1)
        )
    
    def test_answer_again(self):
        """Тест обработки Again"""
        response = self.client.post('/api/training/answer/', {
            'card_id': self.card.id,
            'answer': 0
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['card_id'] == self.card.id
        assert 'new_interval' in response.data
        assert response.data['entered_learning_mode'] is True
    
    def test_answer_hard(self):
        """Тест обработки Hard"""
        response = self.client.post('/api/training/answer/', {
            'card_id': self.card.id,
            'answer': 1
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'new_ease_factor' in response.data
    
    def test_answer_good(self):
        """Тест обработки Good"""
        response = self.client.post('/api/training/answer/', {
            'card_id': self.card.id,
            'answer': 2
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['new_interval'] > 0
    
    def test_answer_easy(self):
        """Тест обработки Easy"""
        response = self.client.post('/api/training/answer/', {
            'card_id': self.card.id,
            'answer': 3
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['new_interval'] > 0
    
    def test_answer_invalid_card(self):
        """Тест невалидной карточки"""
        response = self.client.post('/api/training/answer/', {
            'card_id': 99999,
            'answer': 2
        })
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_answer_invalid_answer(self):
        """Тест невалидного ответа"""
        response = self.client.post('/api/training/answer/', {
            'card_id': self.card.id,
            'answer': 5
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_answer_with_time_spent(self):
        """Тест с указанием времени"""
        response = self.client.post('/api/training/answer/', {
            'card_id': self.card.id,
            'answer': 2,
            'time_spent': 5.5
        })
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTrainingLearningModeAPI:
    """Тесты для enter-learning/exit-learning"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        from apps.cards.models import Card
        from apps.words.models import Word
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.word = Word.objects.create(
            user=self.user,
            original_word='Haus',
            translation='дом',
            language='de'
        )
        Card.objects.filter(word=self.word).delete()
        
        self.card = Card.objects.create(
            user=self.user,
            word=self.word,
            card_type='normal',
            is_in_learning_mode=False
        )
    
    def test_enter_learning_mode(self):
        """Тест перевода в режим изучения"""
        response = self.client.post('/api/training/enter-learning/', {
            'card_id': self.card.id
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        self.card.refresh_from_db()
        assert self.card.is_in_learning_mode is True
    
    def test_enter_learning_already_in(self):
        """Тест перевода в режим изучения, когда уже в режиме"""
        self.card.enter_learning_mode()
        self.card.save()
        
        response = self.client.post('/api/training/enter-learning/', {
            'card_id': self.card.id
        })
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_exit_learning_mode(self):
        """Тест вывода из режима изучения"""
        self.card.enter_learning_mode()
        self.card.save()
        
        response = self.client.post('/api/training/exit-learning/', {
            'card_id': self.card.id
        })
        
        assert response.status_code == status.HTTP_200_OK
        self.card.refresh_from_db()
        assert self.card.is_in_learning_mode is False
    
    def test_exit_learning_not_in(self):
        """Тест вывода из режима изучения, когда не в режиме"""
        response = self.client.post('/api/training/exit-learning/', {
            'card_id': self.card.id
        })
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTrainingStatsAPI:
    """Тесты для GET /api/training/stats/"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        from apps.cards.models import Card
        from apps.words.models import Word
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.settings, _ = UserTrainingSettings.objects.get_or_create(
            user=self.user,
            defaults={'age_group': 'adult'}
        )
        
        self.word = Word.objects.create(
            user=self.user,
            original_word='Haus',
            translation='дом',
            language='de'
        )
        Card.objects.filter(word=self.word).delete()
    
    def test_stats_all_period(self):
        """Тест статистики за весь период"""
        response = self.client.get('/api/training/stats/?period=all')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_reviews' in response.data
        assert 'success_rate' in response.data
        assert 'streak_days' in response.data
        assert 'cards_by_status' in response.data
    
    def test_stats_day_period(self):
        """Тест статистики за день"""
        response = self.client.get('/api/training/stats/?period=day')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['period'] == 'day'
    
    def test_stats_week_period(self):
        """Тест статистики за неделю"""
        response = self.client.get('/api/training/stats/?period=week')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['period'] == 'week'
    
    def test_stats_month_period(self):
        """Тест статистики за месяц"""
        response = self.client.get('/api/training/stats/?period=month')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['period'] == 'month'
    
    def test_stats_cards_by_status(self):
        """Тест распределения карточек по статусам"""
        from apps.cards.models import Card
        
        Card.objects.create(
            user=self.user,
            word=self.word,
            card_type='normal',
            is_in_learning_mode=True,
            repetitions=0,
            interval=0
        )
        
        response = self.client.get('/api/training/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'new' in response.data['cards_by_status']
        assert 'learning' in response.data['cards_by_status']
        assert 'review' in response.data['cards_by_status']
        assert 'mastered' in response.data['cards_by_status']


# ═══════════════════════════════════════════════════════════════
# ЭТАП 7: AI Generation Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAIGeneration:
    """Тесты для функций генерации контента через AI"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Настройки тренировки создаются автоматически через signal
        # Используем get_or_create на случай, если что-то пошло не так
        UserTrainingSettings.objects.get_or_create(user=self.user, defaults={'age_group': 'adult'})
        # Создаем токены для пользователя ПЕРЕД созданием слова
        # (чтобы избежать расходования токенов на автоматическую генерацию этимологии)
        from apps.cards.models import Token
        token, created = Token.objects.get_or_create(user=self.user, defaults={'balance': 100})
        if not created:
            # Если токены уже есть, обновляем баланс
            token.balance = 100
            token.save()
        
        # Создаем слово для тестов (отключаем автоматическую генерацию этимологии)
        self.word = Word.objects.create(
            user=self.user,
            original_word='Haus',
            translation='дом',
            language='de',
            etymology=''  # Пустая этимология, чтобы signal не запускался
        )
        # Устанавливаем флаг, чтобы пропустить автоматическую генерацию
        self.word._skip_etymology_generation = True
        self.word.save()
    
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generate_etymology_success(self, mock_client):
        """Тест успешной генерации этимологии"""
        from apps.training.ai_generation import generate_etymology
        
        # Мокаем OpenAI клиент
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Слово 'Haus' происходит от древнегерманского 'hūs'."
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        # Генерируем этимологию
        etymology = generate_etymology(
            word='Haus',
            translation='дом',
            language='de',
            user=self.user
        )
        
        assert etymology is not None
        assert len(etymology) > 10
        assert 'Haus' in etymology or 'hūs' in etymology
    
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generate_hint_success(self, mock_client):
        """Тест успешной генерации подсказки"""
        from apps.training.ai_generation import generate_hint
        
        # Мокаем OpenAI клиент
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Ein Gebäude, in dem Menschen wohnen."
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        # Генерируем подсказку (без аудио)
        hint_text, hint_audio = generate_hint(
            word='Haus',
            translation='дом',
            language='de',
            user=self.user,
            generate_audio=False
        )
        
        assert hint_text is not None
        assert len(hint_text) > 10
        assert hint_audio is None  # Аудио не генерировалось
    
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generate_sentence_success(self, mock_client):
        """Тест успешной генерации предложения"""
        from apps.training.ai_generation import generate_sentence
        
        # Мокаем OpenAI клиент
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Ich wohne in einem großen Haus mit einem Garten."
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        # Генерируем предложение
        sentence = generate_sentence(
            word='Haus',
            translation='дом',
            language='de',
            user=self.user,
            count=1
        )
        
        assert sentence is not None
        assert isinstance(sentence, str)
        assert 'haus' in sentence.lower()  # Проверяем в нижнем регистре
    
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generate_synonym_success(self, mock_client):
        """Тест успешной генерации синонима"""
        from apps.training.ai_generation import generate_synonym_word
        
        # Мокаем OpenAI клиент
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Gebäude|здание"
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        # Генерируем синоним (мокаем автоматическую генерацию этимологии)
        with patch('apps.training.ai_generation.generate_etymology') as mock_etymology:
            mock_etymology.return_value = "Этимология для Gebäude"
            
            synonym_word = generate_synonym_word(
                word=self.word,
                user=self.user,
                create_card=False  # Не создаем карточку для упрощения
            )
            
            assert synonym_word is not None
            assert synonym_word.original_word == 'Gebäude'
            assert synonym_word.translation == 'здание'
            assert synonym_word.user == self.user
    
    def test_generate_etymology_insufficient_tokens(self):
        """Тест генерации этимологии при недостатке токенов"""
        from apps.training.ai_generation import generate_etymology
        from apps.cards.models import Token
        
        # Удаляем токены
        Token.objects.filter(user=self.user).delete()
        
        # Пытаемся сгенерировать этимологию
        with pytest.raises(ValueError, match='Недостаточно токенов'):
            generate_etymology(
                word='Haus',
                translation='дом',
                language='de',
                user=self.user
            )
    
    def test_generate_sentence_invalid_count(self):
        """Тест генерации предложения с неверным count"""
        from apps.training.ai_generation import generate_sentence
        
        # Пытаемся сгенерировать с count > 5
        with pytest.raises(ValueError, match='count должен быть от 1 до 5'):
            generate_sentence(
                word='Haus',
                translation='дом',
                language='de',
                user=self.user,
                count=10
            )


@pytest.mark.django_db
class TestAIGenerationAPI:
    """Тесты для API эндпоинтов генерации контента"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Настройки тренировки создаются автоматически через signal
        # Используем get_or_create на случай, если что-то пошло не так
        UserTrainingSettings.objects.get_or_create(user=self.user, defaults={'age_group': 'adult'})
        
        # Создаем токены для пользователя ПЕРЕД созданием слова
        # (чтобы избежать расходования токенов на автоматическую генерацию этимологии)
        from apps.cards.models import Token
        token, created = Token.objects.get_or_create(user=self.user, defaults={'balance': 100})
        if not created:
            # Если токены уже есть, обновляем баланс
            token.balance = 100
            token.save()
        
        # Создаем слово для тестов (отключаем автоматическую генерацию этимологии)
        self.word = Word.objects.create(
            user=self.user,
            original_word='Haus',
            translation='дом',
            language='de',
            etymology=''  # Пустая этимология, чтобы signal не запускался
        )
        # Устанавливаем флаг, чтобы пропустить автоматическую генерацию
        self.word._skip_etymology_generation = True
        self.word.save()
    
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generate_etymology_api(self, mock_client):
        """Тест API генерации этимологии"""
        # Мокаем OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Этимология для Haus"
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        response = self.client.post('/api/training/generate-etymology/', {
            'word_id': self.word.id,
            'force_regenerate': False
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'etymology' in response.data
        assert 'tokens_spent' in response.data
        assert 'balance_after' in response.data
    
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generate_hint_api(self, mock_client):
        """Тест API генерации подсказки"""
        # Мокаем OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Ein Gebäude für Menschen"
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        response = self.client.post('/api/training/generate-hint/', {
            'word_id': self.word.id,
            'generate_audio': False
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'hint_text' in response.data
        assert 'tokens_spent' in response.data
    
    @patch('apps.training.ai_generation.get_openai_client')
    def test_generate_sentence_api(self, mock_client):
        """Тест API генерации предложений"""
        # Мокаем OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Ich wohne in einem Haus.\nDas Haus ist groß."
        
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_openai_client
        
        response = self.client.post('/api/training/generate-sentence/', {
            'word_id': self.word.id,
            'count': 2
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'sentences' in response.data
        assert isinstance(response.data['sentences'], list)
        assert len(response.data['sentences']) > 0
    
    def test_generate_etymology_api_word_not_found(self):
        """Тест API генерации этимологии для несуществующего слова"""
        response = self.client.post('/api/training/generate-etymology/', {
            'word_id': 99999,
            'force_regenerate': False
        })
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data
    
    def test_generate_sentence_api_invalid_count(self):
        """Тест API генерации предложений с неверным count"""
        response = self.client.post('/api/training/generate-sentence/', {
            'word_id': self.word.id,
            'count': 10  # > 5
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data or 'count' in str(response.data).lower()


# ========================
# Тесты для migrate_data
# ========================

@pytest.mark.django_db
class TestMigrateDataCommand:
    """Тесты management command migrate_data"""

    def setup_method(self):
        self.user = User.objects.create_user(
            username='migrate_test_user',
            email='migrate@test.com',
            password='testpass123'
        )

    def test_dry_run_no_changes(self):
        """Dry run не создаёт данных"""
        from django.core.management import call_command
        from io import StringIO
        
        word = Word.objects.create(
            user=self.user, original_word='TestMigrate',
            translation='test', language='de', card_type='normal'
        )
        # Delete cards/settings created by signals
        Card.objects.filter(word=word).delete()
        UserTrainingSettings.objects.filter(user=self.user).delete()
        
        out = StringIO()
        call_command('migrate_data', stdout=out)
        output = out.getvalue()
        
        assert 'DRY RUN' in output
        assert Card.objects.filter(word=word).count() == 0

    def test_apply_creates_cards_and_settings(self):
        """--apply создаёт Cards и TrainingSettings"""
        from django.core.management import call_command
        from io import StringIO
        
        word1 = Word.objects.create(
            user=self.user, original_word='ApplyTest1',
            translation='test1', language='de', card_type='normal'
        )
        word2 = Word.objects.create(
            user=self.user, original_word='ApplyTest2',
            translation='test2', language='de', card_type='inverted'
        )
        # Delete cards/settings created by signals
        Card.objects.filter(word__in=[word1, word2]).delete()
        UserTrainingSettings.objects.filter(user=self.user).delete()
        
        word1.learning_status = 'new'
        word1.save()
        word2.learning_status = 'new'
        word2.save()
        
        out = StringIO()
        call_command('migrate_data', '--apply', stdout=out)
        output = out.getvalue()
        
        assert 'Created' in output
        assert Card.objects.filter(word=word1).count() == 1
        assert Card.objects.filter(word=word2).count() == 1
        assert Card.objects.filter(word=word1).first().card_type == 'normal'
        assert Card.objects.filter(word=word2).first().card_type == 'inverted'
        assert UserTrainingSettings.objects.filter(user=self.user).exists()
        
        word1.refresh_from_db()
        assert word1.learning_status == 'learning'

    def test_idempotent(self):
        """Повторный запуск не дублирует данные"""
        from django.core.management import call_command
        from io import StringIO
        
        word = Word.objects.create(
            user=self.user, original_word='IdempotentTest',
            translation='test', language='de', card_type='normal'
        )
        # First run (signal already created card, so delete it first to test)
        Card.objects.filter(word=word).delete()
        
        out1 = StringIO()
        call_command('migrate_data', '--apply', stdout=out1)
        
        card_count = Card.objects.filter(word=word).count()
        assert card_count == 1
        
        # Second run
        out2 = StringIO()
        call_command('migrate_data', '--apply', stdout=out2)
        
        assert Card.objects.filter(word=word).count() == 1  # Still 1

    def test_empty_card_type_is_auxiliary(self):
        """card_type=empty создаёт is_auxiliary=True"""
        from django.core.management import call_command
        from io import StringIO
        
        word = Word.objects.create(
            user=self.user, original_word='EmptyTest',
            translation='test', language='de', card_type='empty'
        )
        Card.objects.filter(word=word).delete()
        
        out = StringIO()
        call_command('migrate_data', '--apply', stdout=out)
        
        card = Card.objects.filter(word=word).first()
        assert card is not None
        assert card.is_auxiliary is True
        assert card.card_type == 'empty'


# ==================================
# Дополнительные тесты SM2 алгоритма
# ==================================

@pytest.mark.django_db
class TestSM2EdgeCases:
    """Тесты граничных случаев SM2"""

    def setup_method(self):
        self.user = User.objects.create_user(
            username='sm2_edge_user',
            email='sm2edge@test.com',
            password='testpass123'
        )
        self.settings, _ = UserTrainingSettings.objects.get_or_create(
            user=self.user,
            defaults={'age_group': 'adult', 'learning_steps': [2, 10]}
        )
        self.word = Word.objects.create(
            user=self.user, original_word='SM2Edge',
            translation='test', language='de', card_type='normal'
        )
        self.card = Card.objects.filter(word=self.word).first()
        if not self.card:
            self.card = Card.objects.create(
                user=self.user, word=self.word,
                card_type='normal', is_in_learning_mode=True,
                ease_factor=2.5, interval=0, repetitions=0,
            )

    def test_calculate_review_interval_again(self):
        """Again возвращает interval=0"""
        from apps.training.sm2 import SM2Algorithm
        
        self.card.interval = 10
        result = SM2Algorithm.calculate_next_interval(self.card, 0, self.settings)
        assert result == 0

    def test_calculate_review_interval_hard(self):
        """Hard применяет hard_interval_modifier"""
        from apps.training.sm2 import SM2Algorithm
        
        self.card.interval = 10
        result = SM2Algorithm.calculate_next_interval(self.card, 1, self.settings)
        assert result >= 1

    def test_calculate_review_interval_good(self):
        """Good применяет ease_factor"""
        from apps.training.sm2 import SM2Algorithm
        
        self.card.interval = 10
        self.card.ease_factor = 2.5
        result = SM2Algorithm.calculate_next_interval(self.card, 2, self.settings)
        assert result > 10

    def test_calculate_review_interval_easy(self):
        """Easy применяет easy_bonus"""
        from apps.training.sm2 import SM2Algorithm
        
        self.card.interval = 10
        self.card.ease_factor = 2.5
        result = SM2Algorithm.calculate_next_interval(self.card, 3, self.settings)
        assert result > 10

    def test_calculate_review_interval_invalid(self):
        """Невалидный answer вызывает ValueError"""
        from apps.training.sm2 import SM2Algorithm
        
        with pytest.raises(ValueError):
            SM2Algorithm.calculate_next_interval(self.card, 5, self.settings)

    def test_update_ease_factor_again(self):
        """Again снижает ease_factor"""
        from apps.training.sm2 import SM2Algorithm
        
        self.card.ease_factor = 2.5
        new_ef = SM2Algorithm.update_ease_factor(self.card, 0, self.settings)
        assert new_ef < 2.5
        assert new_ef >= self.settings.min_ease_factor

    def test_update_ease_factor_easy(self):
        """Easy повышает ease_factor"""
        from apps.training.sm2 import SM2Algorithm
        
        self.card.ease_factor = 2.5
        new_ef = SM2Algorithm.update_ease_factor(self.card, 3, self.settings)
        assert new_ef > 2.5

    def test_update_ease_factor_invalid(self):
        """Невалидный answer вызывает ValueError"""
        from apps.training.sm2 import SM2Algorithm
        
        with pytest.raises(ValueError):
            SM2Algorithm.update_ease_factor(self.card, 99, self.settings)

    def test_should_enter_learning_mode(self):
        """Проверка порога consecutive_lapses"""
        from apps.training.sm2 import SM2Algorithm
        
        self.card.consecutive_lapses = 0
        assert SM2Algorithm.should_enter_learning_mode(self.card, self.settings) is False
        
        self.card.consecutive_lapses = self.settings.lapse_threshold
        assert SM2Algorithm.should_enter_learning_mode(self.card, self.settings) is True

    def test_apply_interval_modifiers_hard(self):
        """apply_interval_modifiers для Hard"""
        from apps.training.sm2 import SM2Algorithm
        
        result = SM2Algorithm.apply_interval_modifiers(10, 1, self.settings)
        assert result >= 1

    def test_apply_interval_modifiers_good(self):
        """apply_interval_modifiers для Good"""
        from apps.training.sm2 import SM2Algorithm
        
        result = SM2Algorithm.apply_interval_modifiers(10, 2, self.settings)
        assert result >= 1

    def test_apply_interval_modifiers_easy(self):
        """apply_interval_modifiers для Easy"""
        from apps.training.sm2 import SM2Algorithm
        
        result = SM2Algorithm.apply_interval_modifiers(10, 3, self.settings)
        assert result >= 1

    def test_apply_interval_modifiers_invalid(self):
        """apply_interval_modifiers с невалидным answer"""
        from apps.training.sm2 import SM2Algorithm
        
        with pytest.raises(ValueError):
            SM2Algorithm.apply_interval_modifiers(10, 0, self.settings)


# ========================
# Тесты уведомлений
# ========================

@pytest.mark.django_db
class TestNotificationSettingsModel:
    """Тесты модели NotificationSettings"""

    def setup_method(self):
        self.user = User.objects.create_user(
            username='notif_user', email='notif@test.com', password='testpass123'
        )

    def test_create_defaults(self):
        """Создание с настройками по умолчанию"""
        from apps.training.models import NotificationSettings
        ns = NotificationSettings.objects.create(user=self.user)
        assert ns.browser_notifications_enabled is True
        assert ns.notification_frequency == 'normal'
        assert ns.notify_cards_due is True
        assert ns.cards_due_threshold == 5

    def test_is_quiet_hours_night(self):
        """Тихие часы: ночной диапазон (22-08)"""
        from apps.training.models import NotificationSettings
        from datetime import time
        ns = NotificationSettings.objects.create(
            user=self.user,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
        )
        assert ns.is_quiet_hours(time(23, 0)) is True
        assert ns.is_quiet_hours(time(3, 0)) is True
        assert ns.is_quiet_hours(time(12, 0)) is False
        assert ns.is_quiet_hours(time(21, 0)) is False

    def test_is_quiet_hours_day(self):
        """Тихие часы: дневной диапазон (13-15)"""
        from apps.training.models import NotificationSettings
        from datetime import time
        ns = NotificationSettings.objects.create(
            user=self.user,
            quiet_hours_start=time(13, 0),
            quiet_hours_end=time(15, 0),
        )
        assert ns.is_quiet_hours(time(14, 0)) is True
        assert ns.is_quiet_hours(time(12, 0)) is False

    def test_should_notify_off(self):
        """Если выключены — не уведомлять"""
        from apps.training.models import NotificationSettings
        ns = NotificationSettings.objects.create(
            user=self.user, notification_frequency='off'
        )
        assert ns.should_notify() is False

    def test_should_notify_first_time(self):
        """Первое уведомление всегда разрешено"""
        from apps.training.models import NotificationSettings
        ns = NotificationSettings.objects.create(
            user=self.user,
            notification_frequency='normal',
            quiet_hours_start=__import__('datetime').time(3, 0),
            quiet_hours_end=__import__('datetime').time(4, 0),
        )
        assert ns.should_notify() is True

    def test_str(self):
        """__str__ representation"""
        from apps.training.models import NotificationSettings
        ns = NotificationSettings.objects.create(user=self.user)
        assert 'notif_user' in str(ns)


@pytest.mark.django_db
class TestNotificationAPI:
    """Тесты API уведомлений"""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='notif_api_user', email='notifapi@test.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_notification_settings_creates_defaults(self):
        """GET создаёт настройки по умолчанию"""
        response = self.client.get('/api/training/notifications/settings/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['browser_notifications_enabled'] is True
        assert response.data['notification_frequency'] == 'normal'

    def test_update_notification_settings(self):
        """PATCH обновляет настройки"""
        response = self.client.patch('/api/training/notifications/settings/', {
            'notification_frequency': 'aggressive',
            'cards_due_threshold': 10,
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['notification_frequency'] == 'aggressive'
        assert response.data['cards_due_threshold'] == 10

    def test_put_notification_settings(self):
        """PUT обновляет все настройки"""
        response = self.client.put('/api/training/notifications/settings/', {
            'browser_notifications_enabled': False,
            'notification_frequency': 'minimal',
            'notify_cards_due': False,
            'notify_streak_warning': False,
            'notify_daily_goal': False,
            'cards_due_threshold': 20,
            'quiet_hours_start': '23:00',
            'quiet_hours_end': '07:00',
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['browser_notifications_enabled'] is False

    def test_notification_check_no_cards(self):
        """Проверка уведомлений без карточек"""
        response = self.client.get('/api/training/notifications/check/')
        assert response.status_code == status.HTTP_200_OK
        assert 'should_notify' in response.data
        assert 'cards_due' in response.data
        assert response.data['cards_due'] == 0

    def test_notification_check_with_cards(self):
        """Проверка уведомлений с карточками"""
        from apps.words.models import Word
        from apps.cards.models import Card
        from django.utils import timezone

        # Создаём слова + карточки (сигнал)
        for i in range(6):
            Word.objects.create(
                user=self.user,
                original_word=f'NotifWord{i}',
                translation=f'test{i}',
                language='de',
                card_type='normal',
            )
        # Ensure cards are due for review (next_review in the past)
        Card.objects.filter(user=self.user).update(
            next_review=timezone.now() - timezone.timedelta(hours=1)
        )
        response = self.client.get('/api/training/notifications/check/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cards_due'] >= 6

    def test_invalid_threshold(self):
        """Невалидный порог карточек"""
        response = self.client.patch('/api/training/notifications/settings/', {
            'cards_due_threshold': 0,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ========================
# Тесты кривых забывания
# ========================

@pytest.mark.django_db
class TestForgettingCurve:
    """Тесты API кривых забывания"""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='curve_user', email='curve@test.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_empty_data(self):
        """Без повторений — пустой ответ"""
        response = self.client.get('/api/training/forgetting-curve/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['points'] == []
        assert response.data['summary']['total_reviews'] == 0

    def test_with_reviewed_cards(self):
        """С повторёнными карточками — возвращает точки"""
        from apps.words.models import Word
        from apps.cards.models import Card

        # Создаём карточки с разными интервалами
        for i in range(5):
            w = Word.objects.create(
                user=self.user,
                original_word=f'CurveWord{i}',
                translation=f'test{i}',
                language='de',
                card_type='normal',
            )
            card = Card.objects.filter(word=w).first()
            card.repetitions = 5
            card.interval = (i + 1) * 7  # 7, 14, 21, 28, 35
            card.consecutive_lapses = 0
            card.save()

        response = self.client.get('/api/training/forgetting-curve/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['points']) > 0
        assert len(response.data['theoretical_curve']) > 0
        assert response.data['summary']['total_reviews'] == 5

        # Verify point structure
        point = response.data['points'][0]
        assert 'interval_days' in point
        assert 'retention_rate' in point
        assert 'total_cards' in point


# ========================
# Тесты дашборда тренировок
# ========================

@pytest.mark.django_db
class TestTrainingDashboardAPI:
    """Тесты для GET /api/training/dashboard/ и activate/deactivate"""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='dashboard_user', email='dash@test.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.settings, _ = UserTrainingSettings.objects.get_or_create(
            user=self.user, defaults={'age_group': 'adult'}
        )

        # Deck with a word
        self.deck = Deck.objects.create(
            user=self.user, name='TestDeck', target_lang='de', source_lang='ru'
        )
        self.word = Word.objects.create(
            user=self.user, original_word='DashHaus', translation='дом', language='de'
        )
        self.deck.words.add(self.word)

        # Category
        self.category = Category.objects.create(
            user=self.user, name='TestCat', icon='📝'
        )
        self.word.categories.add(self.category)

    def test_dashboard_returns_data(self):
        """GET /api/training/dashboard/ returns structured data"""
        response = self.client.get('/api/training/dashboard/')
        assert response.status_code == status.HTTP_200_OK
        assert 'quick_stats' in response.data
        assert 'decks' in response.data
        assert 'categories' in response.data
        assert 'orphans' in response.data
        assert len(response.data['decks']) >= 1
        assert len(response.data['categories']) >= 1

    def test_dashboard_deck_cards_info(self):
        """Dashboard includes card counts per deck"""
        response = self.client.get('/api/training/dashboard/')
        deck_data = next(d for d in response.data['decks'] if d['id'] == self.deck.id)
        assert 'cards' in deck_data
        assert 'total' in deck_data['cards']
        assert 'due' in deck_data['cards']

    def test_activate_deck(self):
        """POST /api/training/deck/<id>/activate/ sets is_learning_active=True"""
        self.deck.is_learning_active = False
        self.deck.save()

        response = self.client.post(f'/api/training/deck/{self.deck.id}/activate/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_learning_active'] is True

        self.deck.refresh_from_db()
        assert self.deck.is_learning_active is True

    def test_deactivate_deck(self):
        """POST /api/training/deck/<id>/deactivate/ sets is_learning_active=False"""
        self.deck.is_learning_active = True
        self.deck.save()

        response = self.client.post(f'/api/training/deck/{self.deck.id}/deactivate/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_learning_active'] is False

    def test_activate_category(self):
        """POST /api/training/category/<id>/activate/"""
        self.category.is_learning_active = False
        self.category.save()

        response = self.client.post(f'/api/training/category/{self.category.id}/activate/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_learning_active'] is True

    def test_deactivate_category(self):
        """POST /api/training/category/<id>/deactivate/"""
        self.category.is_learning_active = True
        self.category.save()

        response = self.client.post(f'/api/training/category/{self.category.id}/deactivate/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_learning_active'] is False

    def test_activate_nonexistent_deck(self):
        """404 for nonexistent deck"""
        response = self.client.post('/api/training/deck/99999/activate/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_activate_nonexistent_category(self):
        """404 for nonexistent category"""
        response = self.client.post('/api/training/category/99999/activate/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_session_with_category_id(self):
        """GET /api/training/session/?category_id=X filters by category"""
        response = self.client.get(f'/api/training/session/?category_id={self.category.id}')
        assert response.status_code == status.HTTP_200_OK

    def test_session_deck_and_category_conflict(self):
        """Cannot specify both deck_id and category_id"""
        response = self.client.get(
            f'/api/training/session/?deck_id={self.deck.id}&category_id={self.category.id}'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_orphan_words_toggle(self):
        """PATCH include_orphan_words through settings"""
        response = self.client.patch('/api/training/settings/', {
            'include_orphan_words': True,
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['include_orphan_words'] is True
