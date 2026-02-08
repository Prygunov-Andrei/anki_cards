"""
Алгоритм интервального повторения SuperMemo SM-2.

Реализует систему интервального повторения с адаптацией под пользователя,
включая внутрисессионное обучение, калибровку и автоматическое управление
режимом изучения.
"""
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Optional

from apps.cards.models import Card
from .models import UserTrainingSettings


class SM2Algorithm:
    """
    Реализация алгоритма SuperMemo SM-2 с адаптацией.
    
    Все константы берутся из UserTrainingSettings, а не захардкожены.
    """
    
    # Максимальный Ease Factor (можно вынести в настройки, но пока жестко)
    MAX_EASE_FACTOR = 5.0
    
    @classmethod
    def process_answer(
        cls,
        card: Card,
        answer: int,
        settings: UserTrainingSettings,
        time_spent: Optional[float] = None
    ) -> Dict:
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
        if answer not in (0, 1, 2, 3):
            raise ValueError(f"Invalid answer: {answer}. Must be 0, 1, 2, or 3")
        
        # Запоминаем начальное состояние
        was_in_learning_mode = card.is_in_learning_mode
        entered_learning_mode = False
        exited_learning_mode = False
        calibrated = False
        
        # Обновляем last_review
        card.last_review = timezone.now()
        
        # Определяем, был ли ответ успешным (для статистики)
        successful = answer in (2, 3)  # Good или Easy
        
        # Обработка в зависимости от режима
        if card.is_in_learning_mode:
            # Внутрисессионное обучение
            result = cls._process_learning_mode_answer(card, answer, settings)
            exited_learning_mode = result['exited_learning_mode']
        else:
            # Долгосрочные интервалы
            result = cls._process_long_term_answer(card, answer, settings)
            entered_learning_mode = result['entered_learning_mode']
        
        # Обновление статистики
        if answer == 0:  # Again
            card.lapses += 1
            card.consecutive_lapses += 1
            card.repetitions = 0  # Сброс при провале
        else:
            # Успешный ответ
            card.consecutive_lapses = 0  # Сброс счётчика провалов
            if successful:
                card.repetitions += 1
        
        # Запись статистики для калибровки
        settings.record_review(successful=successful)
        
        # Проверка на калибровку
        if settings.should_calibrate():
            calibration_result = settings.calibrate()
            calibrated = calibration_result.get('calibrated', False)
        
        # Сохранение карточки
        card.save()
        
        return {
            'card': card,
            'new_interval': result.get('new_interval', card.interval),
            'new_ease_factor': card.ease_factor,
            'next_review': card.next_review,
            'entered_learning_mode': entered_learning_mode,
            'exited_learning_mode': exited_learning_mode,
            'learning_step': card.learning_step,
            'calibrated': calibrated,
        }
    
    @classmethod
    def _process_learning_mode_answer(
        cls,
        card: Card,
        answer: int,
        settings: UserTrainingSettings
    ) -> Dict:
        """
        Обрабатывает ответ в режиме обучения (внутрисессионное повторение).
        
        Returns:
            dict с результатами обработки
        """
        learning_steps = settings.learning_steps
        if not learning_steps:
            learning_steps = [2, 10]  # Fallback
        
        exited_learning_mode = False
        new_interval = 0  # В режиме обучения интервал в минутах
        
        if answer == 0:  # Again
            # Сброс на первый шаг
            card.learning_step = 0
            card.ease_factor = max(
                settings.min_ease_factor,
                card.ease_factor + settings.again_ef_delta
            )
            # Немедленный повтор через первый шаг
            minutes = learning_steps[0] if learning_steps else 2
            card.next_review = timezone.now() + timedelta(minutes=minutes)
            new_interval = minutes
        
        elif answer == 1:  # Hard
            # Остаёмся на текущем шаге (или промежуточный интервал)
            card.ease_factor = max(
                settings.min_ease_factor,
                card.ease_factor + settings.hard_ef_delta
            )
            # Если не последний шаг, остаёмся на нём
            if card.learning_step < len(learning_steps) - 1:
                minutes = learning_steps[card.learning_step]
                card.next_review = timezone.now() + timedelta(minutes=minutes)
                new_interval = minutes
            else:
                # Последний шаг - можно выпустить (но с меньшим интервалом)
                # Или остаться на шаге - выберем остаться
                minutes = learning_steps[card.learning_step]
                card.next_review = timezone.now() + timedelta(minutes=minutes)
                new_interval = minutes
        
        elif answer == 2:  # Good
            # Переход на следующий шаг
            card.learning_step += 1
            
            if card.learning_step >= len(learning_steps):
                # Прошли все шаги - выпуск из режима обучения
                card.is_in_learning_mode = False
                card.learning_step = -1
                card.interval = settings.graduating_interval
                card.next_review = timezone.now() + timedelta(days=card.interval)
                new_interval = card.interval
                exited_learning_mode = True
            else:
                # Переход на следующий шаг
                minutes = learning_steps[card.learning_step]
                card.next_review = timezone.now() + timedelta(minutes=minutes)
                new_interval = minutes
        
        elif answer == 3:  # Easy
            # Досрочный выпуск из режима обучения
            card.is_in_learning_mode = False
            card.learning_step = -1
            card.ease_factor = min(
                cls.MAX_EASE_FACTOR,
                card.ease_factor + settings.easy_ef_delta
            )
            card.interval = settings.easy_interval
            card.next_review = timezone.now() + timedelta(days=card.interval)
            new_interval = card.interval
            exited_learning_mode = True
        
        return {
            'new_interval': new_interval,
            'exited_learning_mode': exited_learning_mode,
        }
    
    @classmethod
    def _process_long_term_answer(
        cls,
        card: Card,
        answer: int,
        settings: UserTrainingSettings
    ) -> Dict:
        """
        Обрабатывает ответ вне режима обучения (долгосрочные интервалы).
        
        Returns:
            dict с результатами обработки
        """
        entered_learning_mode = False
        new_interval = card.interval
        
        if answer == 0:  # Again
            # Возврат в режим обучения
            card.is_in_learning_mode = True
            card.learning_step = 0
            card.ease_factor = max(
                settings.min_ease_factor,
                card.ease_factor + settings.again_ef_delta
            )
            # Немедленный повтор
            learning_steps = settings.learning_steps or [2, 10]
            minutes = learning_steps[0]
            card.next_review = timezone.now() + timedelta(minutes=minutes)
            new_interval = minutes
            entered_learning_mode = True
        
        elif answer == 1:  # Hard
            # Снижение EF
            card.ease_factor = max(
                settings.min_ease_factor,
                card.ease_factor + settings.hard_ef_delta
            )
            # Интервал с модификатором
            base_interval = card.interval if card.interval > 0 else settings.graduating_interval
            new_interval = cls.apply_interval_modifiers(
                base_interval,
                answer,
                settings
            )
            # Минимум +1 день от предыдущего (или graduating_interval для первой карточки)
            min_interval = settings.graduating_interval if card.interval == 0 else card.interval + 1
            new_interval = max(min_interval, new_interval)
            card.interval = new_interval
            card.next_review = timezone.now() + timedelta(days=new_interval)
        
        elif answer == 2:  # Good
            # EF без изменений (или небольшое изменение)
            card.ease_factor = card.ease_factor + settings.good_ef_delta
            # Ограничение EF (на случай если good_ef_delta отрицательный)
            card.ease_factor = max(settings.min_ease_factor, card.ease_factor)
            # Стандартный расчёт интервала
            base_interval = card.interval if card.interval > 0 else settings.graduating_interval
            new_interval = int(base_interval * card.ease_factor * settings.interval_modifier)
            new_interval = max(1, new_interval)
            # Минимум +1 день от предыдущего (или graduating_interval для первой карточки)
            min_interval = settings.graduating_interval if card.interval == 0 else card.interval + 1
            new_interval = max(min_interval, new_interval)
            card.interval = new_interval
            card.next_review = timezone.now() + timedelta(days=new_interval)
        
        elif answer == 3:  # Easy
            # Увеличение EF
            card.ease_factor = min(
                cls.MAX_EASE_FACTOR,
                card.ease_factor + settings.easy_ef_delta
            )
            # Интервал с бонусом (используем новый EF)
            base_interval = card.interval if card.interval > 0 else settings.graduating_interval
            new_interval = int(
                base_interval * card.ease_factor * settings.easy_bonus * settings.interval_modifier
            )
            new_interval = max(1, new_interval)
            # Минимум +1 день от предыдущего (или graduating_interval для первой карточки)
            min_interval = settings.graduating_interval if card.interval == 0 else card.interval + 1
            new_interval = max(min_interval, new_interval)
            card.interval = new_interval
            card.next_review = timezone.now() + timedelta(days=new_interval)
        
        return {
            'new_interval': new_interval,
            'entered_learning_mode': entered_learning_mode,
        }
    
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
        
        Args:
            card: Карточка
            answer: Оценка ответа (1=Hard, 2=Good, 3=Easy)
            settings: Настройки тренировки
        
        Returns:
            int: Интервал в днях
        """
        if answer == 0:  # Again - возврат в режим обучения
            return 0
        
        base_interval = card.interval if card.interval > 0 else 1
        
        if answer == 1:  # Hard
            new_interval = int(
                base_interval * settings.hard_interval_modifier * settings.interval_modifier
            )
        elif answer == 2:  # Good
            new_interval = int(
                base_interval * card.ease_factor * settings.interval_modifier
            )
        elif answer == 3:  # Easy
            new_interval = int(
                base_interval * card.ease_factor * settings.easy_bonus * settings.interval_modifier
            )
        else:
            raise ValueError(f"Invalid answer: {answer}")
        
        new_interval = max(1, new_interval)
        # Минимум +1 день от предыдущего
        new_interval = max(card.interval + 1, new_interval)
        
        return new_interval
    
    @classmethod
    def should_enter_learning_mode(
        cls,
        card: Card,
        settings: UserTrainingSettings
    ) -> bool:
        """
        Проверяет, нужно ли отправить карточку в режим изучения.
        
        Args:
            card: Карточка
            settings: Настройки тренировки
        
        Returns:
            bool: True если consecutive_lapses >= lapse_threshold
        """
        return card.consecutive_lapses >= settings.lapse_threshold
    
    @classmethod
    def update_ease_factor(
        cls,
        card: Card,
        answer: int,
        settings: UserTrainingSettings
    ) -> float:
        """
        Обновляет Ease Factor карточки на основе ответа.
        
        Args:
            card: Карточка
            answer: Оценка ответа (0=Again, 1=Hard, 2=Good, 3=Easy)
            settings: Настройки тренировки
        
        Returns:
            float: Новое значение ease_factor
        """
        if answer == 0:  # Again
            delta = settings.again_ef_delta
        elif answer == 1:  # Hard
            delta = settings.hard_ef_delta
        elif answer == 2:  # Good
            delta = settings.good_ef_delta
        elif answer == 3:  # Easy
            delta = settings.easy_ef_delta
        else:
            raise ValueError(f"Invalid answer: {answer}")
        
        new_ef = card.ease_factor + delta
        
        # Ограничения
        if answer in (0, 1):  # Again или Hard - снижение
            new_ef = max(settings.min_ease_factor, new_ef)
        elif answer == 3:  # Easy - увеличение
            new_ef = min(cls.MAX_EASE_FACTOR, new_ef)
        
        card.ease_factor = new_ef
        return new_ef
    
    @classmethod
    def apply_interval_modifiers(
        cls,
        base_interval: int,
        answer: int,
        settings: UserTrainingSettings
    ) -> int:
        """
        Применяет модификаторы интервала (hard_interval_modifier, easy_bonus, interval_modifier).
        
        Args:
            base_interval: Базовый интервал в днях
            answer: Оценка ответа (1=Hard, 2=Good, 3=Easy)
            settings: Настройки тренировки
        
        Returns:
            int: Модифицированный интервал в днях
        """
        if answer == 1:  # Hard
            modifier = settings.hard_interval_modifier
        elif answer == 2:  # Good
            modifier = 1.0  # Без дополнительного модификатора
        elif answer == 3:  # Easy
            modifier = settings.easy_bonus
        else:
            raise ValueError(f"Invalid answer for interval modifier: {answer}")
        
        # Применяем модификаторы
        new_interval = int(base_interval * modifier * settings.interval_modifier)
        return max(1, new_interval)
