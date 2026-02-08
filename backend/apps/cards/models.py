from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class GeneratedDeck(models.Model):
    """Модель для хранения информации о сгенерированных колодах"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_decks',
        verbose_name='Пользователь'
    )
    deck_name = models.CharField(
        max_length=200,
        verbose_name='Название колоды'
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name='Путь к файлу'
    )
    cards_count = models.IntegerField(
        verbose_name='Количество карточек'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Сгенерированная колода'
        verbose_name_plural = 'Сгенерированные колоды'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.deck_name} ({self.user.username})"


class UserPrompt(models.Model):
    """Модель для хранения пользовательских промптов"""
    
    PROMPT_TYPE_CHOICES = [
        ('image', 'Генерация изображений'),
        ('audio', 'Генерация аудио'),
        ('word_analysis', 'Анализ смешанных языков'),
        ('translation', 'Перевод слов'),
        ('deck_name', 'Генерация названия колоды'),
        ('part_of_speech', 'Определение части речи'),
        ('category', 'Определение категории'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_prompts',
        verbose_name='Пользователь'
    )
    prompt_type = models.CharField(
        max_length=50,
        choices=PROMPT_TYPE_CHOICES,
        verbose_name='Тип промпта'
    )
    custom_prompt = models.TextField(
        verbose_name='Пользовательский промпт'
    )
    is_custom = models.BooleanField(
        default=False,
        verbose_name='Пользовательский промпт'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Промпт пользователя'
        verbose_name_plural = 'Промпты пользователей'
        unique_together = [['user', 'prompt_type']]
        ordering = ['prompt_type']
        indexes = [
            models.Index(fields=['user', 'prompt_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_prompt_type_display()}"
    
    def clean(self):
        """Валидация промпта"""
        if self.custom_prompt:
            # Проверяем наличие обязательных плейсхолдеров в зависимости от типа
            required_placeholders = {
                'image': ['{word}', '{translation}'],
                'audio': ['{word}'],
                'word_analysis': ['{learning_language}', '{native_language}'],
                'translation': ['{learning_language}', '{native_language}'],
                'deck_name': ['{learning_language}', '{native_language}'],
                'part_of_speech': ['{word}', '{language}'],
                'category': ['{word}', '{language}'],
            }
            
            placeholders = required_placeholders.get(self.prompt_type, [])
            for placeholder in placeholders:
                if placeholder not in self.custom_prompt:
                    raise ValidationError(
                        f'Промпт должен содержать плейсхолдер {placeholder}'
                    )


class PartOfSpeechCache(models.Model):
    """Модель для кэширования результатов определения части речи"""
    
    word = models.CharField(
        max_length=200,
        verbose_name='Слово'
    )
    language = models.CharField(
        max_length=2,
        verbose_name='Язык'
    )
    part_of_speech = models.CharField(
        max_length=50,
        verbose_name='Часть речи'
    )
    article = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name='Артикль (для немецкого)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Кэш части речи'
        verbose_name_plural = 'Кэш частей речи'
        unique_together = [['word', 'language']]
        indexes = [
            models.Index(fields=['word', 'language']),
        ]
    
    def __str__(self):
        article_str = f" ({self.article})" if self.article else ""
        return f"{self.word} ({self.language}): {self.part_of_speech}{article_str}"


class Deck(models.Model):
    """Модель колоды карточек"""
    
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('pt', 'Португальский'),
        ('de', 'Немецкий'),
        ('es', 'Испанский'),
        ('fr', 'Французский'),
        ('it', 'Итальянский'),
        ('tr', 'Турецкий'),
    ]
    
    NATIVE_LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('pt', 'Português'),
        ('de', 'Deutsch'),
        ('es', 'Español'),
        ('fr', 'Français'),
        ('it', 'Italiano'),
        ('tr', 'Türkçe'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='decks',
        verbose_name='Пользователь'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название колоды'
    )
    cover = models.ImageField(
        upload_to='deck_covers/',
        null=True,
        blank=True,
        verbose_name='Обложка колоды'
    )
    target_lang = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        verbose_name='Язык изучения'
    )
    source_lang = models.CharField(
        max_length=2,
        choices=NATIVE_LANGUAGE_CHOICES,
        default='ru',
        verbose_name='Родной язык'
    )
    words = models.ManyToManyField(
        'words.Word',
        related_name='decks',
        blank=True,
        verbose_name='Слова'
    )
    is_learning_active = models.BooleanField(
        default=False,
        verbose_name='Активна для тренировки',
        help_text='True = карточки из колоды попадают в общую тренировку'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Колода'
        verbose_name_plural = 'Колоды'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'updated_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    @property
    def words_count(self):
        """Количество слов в колоде"""
        return self.words.count()


class Token(models.Model):
    """Модель токенов пользователя (баланс)"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token',
        verbose_name='Пользователь'
    )
    balance = models.IntegerField(
        default=0,
        verbose_name='Баланс токенов'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Токен'
        verbose_name_plural = 'Токены'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.balance} токенов"


class TokenTransaction(models.Model):
    """Модель транзакций токенов (история операций)"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('earned', 'Начислено'),
        ('spent', 'Потрачено'),
        ('refund', 'Возвращено'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token_transactions',
        verbose_name='Пользователь'
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='Тип транзакции'
    )
    amount = models.IntegerField(
        verbose_name='Сумма'
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата транзакции'
    )
    
    class Meta:
        verbose_name = 'Транзакция токенов'
        verbose_name_plural = 'Транзакции токенов'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        type_display = dict(self.TRANSACTION_TYPE_CHOICES).get(self.transaction_type, self.transaction_type)
        return f"{self.user.username}: {type_display} {self.amount} токенов"


class CardManager(models.Manager):
    """Менеджер для работы с карточками"""
    
    def for_user(self, user):
        """Все карточки пользователя"""
        return self.filter(user=user, is_suspended=False)
    
    def due_for_review(self, user):
        """
        Карточки, которые нужно повторить.
        - Не приостановлены
        - Не в режиме изучения (уже прошли Learning Mode)
        - next_review <= now
        """
        return self.filter(
            user=user,
            is_suspended=False,
            is_in_learning_mode=False,
            next_review__lte=timezone.now()
        ).order_by('next_review')
    
    def in_learning(self, user):
        """Карточки в режиме изучения"""
        return self.filter(
            user=user,
            is_suspended=False,
            is_in_learning_mode=True
        )
    
    def by_word(self, word):
        """Все карточки слова"""
        return self.filter(word=word)
    
    def by_deck(self, deck):
        """Карточки слов из колоды"""
        return self.filter(word__decks=deck, is_suspended=False)


class Card(models.Model):
    """
    Карточка — единица тренировки.
    
    Хранит:
    - Связь со словом (Word)
    - Тип карточки (normal, inverted, empty, cloze)
    - Параметры алгоритма SM-2
    - Состояние (is_in_learning_mode, is_suspended, is_auxiliary)
    
    Одно слово может иметь несколько карточек разных типов.
    Каждая карточка живёт в SM-2 независимо.
    """
    
    CARD_TYPES = [
        ('normal', 'Обычная'),
        ('inverted', 'Инвертированная'),
        ('empty', 'Пустая'),
        ('cloze', 'С пропуском'),
    ]
    
    # ═══════════════════════════════════════════════════════════════
    # СВЯЗИ
    # ═══════════════════════════════════════════════════════════════
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cards',
        verbose_name='Пользователь'
    )
    word = models.ForeignKey(
        'words.Word',
        on_delete=models.CASCADE,
        related_name='cards',
        verbose_name='Слово'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ТИП КАРТОЧКИ
    # ═══════════════════════════════════════════════════════════════
    
    card_type = models.CharField(
        max_length=20,
        choices=CARD_TYPES,
        default='normal',
        verbose_name='Тип карточки'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # CLOZE-КАРТОЧКИ (специфичные поля)
    # ═══════════════════════════════════════════════════════════════
    
    cloze_sentence = models.TextField(
        blank=True,
        default='',
        verbose_name='Предложение для cloze',
        help_text='Полное предложение без пропуска'
    )
    cloze_word_index = models.IntegerField(
        default=0,
        verbose_name='Индекс пропущенного слова',
        help_text='Позиция слова в предложении (0-based)'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # SM-2 ПАРАМЕТРЫ
    # ═══════════════════════════════════════════════════════════════
    
    ease_factor = models.FloatField(
        default=2.5,
        verbose_name='Ease Factor',
        help_text='Коэффициент лёгкости (минимум 1.3)'
    )
    interval = models.IntegerField(
        default=0,
        verbose_name='Интервал (дни)',
        help_text='Текущий интервал повторения'
    )
    repetitions = models.IntegerField(
        default=0,
        verbose_name='Успешные повторения',
        help_text='Количество успешных повторений подряд'
    )
    lapses = models.IntegerField(
        default=0,
        verbose_name='Общие провалы',
        help_text='Общее количество нажатий "Снова"'
    )
    consecutive_lapses = models.IntegerField(
        default=0,
        verbose_name='Провалы подряд',
        help_text='Провалы подряд (4 → режим Изучения)'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ПЛАНИРОВАНИЕ
    # ═══════════════════════════════════════════════════════════════
    
    next_review = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Следующий показ',
        db_index=True
    )
    last_review = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Последний показ'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ВНУТРИСЕССИОННОЕ ОБУЧЕНИЕ
    # ═══════════════════════════════════════════════════════════════
    
    learning_step = models.IntegerField(
        default=0,
        verbose_name='Шаг обучения',
        help_text='Текущий шаг: 0=2мин, 1=10мин (настраивается в UserTrainingSettings)'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # СТАТУСЫ
    # ═══════════════════════════════════════════════════════════════
    
    is_in_learning_mode = models.BooleanField(
        default=True,
        verbose_name='В режиме изучения',
        help_text='True = ещё не прошёл Learning Mode'
    )
    is_auxiliary = models.BooleanField(
        default=False,
        verbose_name='Вспомогательная',
        help_text='True = empty/cloze, может "сгореть"'
    )
    is_suspended = models.BooleanField(
        default=False,
        verbose_name='Приостановлена',
        db_index=True
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
    
    objects = CardManager()
    
    class Meta:
        verbose_name = 'Карточка'
        verbose_name_plural = 'Карточки'
        ordering = ['next_review', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_suspended', 'next_review']),
            models.Index(fields=['user', 'is_in_learning_mode']),
            models.Index(fields=['word', 'card_type']),
        ]
        # Одно слово может иметь только одну карточку каждого типа
        # Для cloze разрешаем несколько с разными предложениями
        unique_together = [['word', 'card_type', 'cloze_sentence']]
    
    def __str__(self):
        return f"[{self.card_type}] {self.word.original_word}"
    
    def save(self, *args, **kwargs):
        """Валидация при сохранении"""
        # Проверяем, что пользователь карточки = пользователю слова
        if self.word_id and self.word.user_id != self.user_id:
            raise ValueError("Карточка должна принадлежать тому же пользователю, что и слово")
        
        # Вспомогательные типы автоматически помечаются
        if self.card_type in ('empty', 'cloze'):
            self.is_auxiliary = True
        
        # Для cloze обязательно нужно предложение
        if self.card_type == 'cloze' and not self.cloze_sentence:
            raise ValueError("Cloze-карточка должна иметь предложение")
        
        super().save(*args, **kwargs)
    
    # ═══════════════════════════════════════════════════════════════
    # ФАБРИЧНЫЕ МЕТОДЫ
    # ═══════════════════════════════════════════════════════════════
    
    @classmethod
    def create_from_word(cls, word, card_type='normal'):
        """
        Создаёт карточку из слова.
        
        Args:
            word: Слово-источник
            card_type: Тип карточки ('normal' или 'inverted')
        
        Returns:
            Созданная карточка
        """
        if card_type not in ('normal', 'inverted'):
            raise ValueError(f"Для create_from_word допустимы только 'normal' и 'inverted', получен: {card_type}")
        
        card, created = cls.objects.get_or_create(
            user=word.user,
            word=word,
            card_type=card_type,
            defaults={
                'ease_factor': 2.5,
                'is_in_learning_mode': True,
                'is_auxiliary': False,
            }
        )
        return card
    
    @classmethod
    def create_inverted(cls, word):
        """Создаёт инвертированную карточку"""
        return cls.create_from_word(word, 'inverted')
    
    @classmethod
    def create_empty(cls, word):
        """
        Создаёт пустую карточку (только медиа → слово).
        Требуется наличие изображения или аудио у слова.
        """
        if not word.image_file and not word.audio_file:
            raise ValueError("Для empty-карточки у слова должно быть изображение или аудио")
        
        card, created = cls.objects.get_or_create(
            user=word.user,
            word=word,
            card_type='empty',
            defaults={
                'ease_factor': 2.5,
                'is_in_learning_mode': True,
                'is_auxiliary': True,
            }
        )
        return card
    
    @classmethod
    def create_cloze(cls, word, sentence, word_index=0):
        """
        Создаёт cloze-карточку из предложения.
        
        Args:
            word: Слово-источник
            sentence: Полное предложение
            word_index: Индекс слова для пропуска (0-based)
        
        Returns:
            Созданная карточка
        """
        if not sentence:
            raise ValueError("Предложение не может быть пустым")
        
        card, created = cls.objects.get_or_create(
            user=word.user,
            word=word,
            card_type='cloze',
            cloze_sentence=sentence,
            defaults={
                'cloze_word_index': word_index,
                'ease_factor': 2.5,
                'is_in_learning_mode': True,
                'is_auxiliary': True,
            }
        )
        return card
    
    # ═══════════════════════════════════════════════════════════════
    # МЕТОДЫ СОСТОЯНИЯ
    # ═══════════════════════════════════════════════════════════════
    
    def suspend(self):
        """Приостановить карточку"""
        self.is_suspended = True
        self.save(update_fields=['is_suspended', 'updated_at'])
    
    def unsuspend(self):
        """Возобновить карточку"""
        self.is_suspended = False
        self.save(update_fields=['is_suspended', 'updated_at'])
    
    def burn(self):
        """
        "Сжечь" вспомогательную карточку.
        Помечает как suspended и is_auxiliary=True.
        Не удаляет — можно восстановить.
        """
        if not self.is_auxiliary:
            raise ValueError("Только вспомогательные карточки могут быть сожжены")
        self.is_suspended = True
        self.save(update_fields=['is_suspended', 'updated_at'])
    
    def restore(self):
        """
        Восстановить сожжённую карточку.
        Сбрасывает в режим изучения.
        """
        self.is_suspended = False
        self.is_in_learning_mode = True
        self.learning_step = 0
        self.consecutive_lapses = 0
        self.save(update_fields=[
            'is_suspended', 'is_in_learning_mode', 
            'learning_step', 'consecutive_lapses', 'updated_at'
        ])
    
    def enter_learning_mode(self):
        """Отправить карточку в режим Изучения"""
        self.is_in_learning_mode = True
        self.learning_step = 0
        self.consecutive_lapses = 0
        self.save(update_fields=[
            'is_in_learning_mode', 'learning_step', 
            'consecutive_lapses', 'updated_at'
        ])
    
    def exit_learning_mode(self):
        """Вывести карточку из режима Изучения"""
        self.is_in_learning_mode = False
        self.save(update_fields=['is_in_learning_mode', 'updated_at'])
    
    # ═══════════════════════════════════════════════════════════════
    # МЕТОДЫ КОНТЕНТА
    # ═══════════════════════════════════════════════════════════════
    
    def get_front_content(self):
        """
        Получить контент лицевой стороны карточки.
        
        Returns:
            dict с ключами: text, image_url, audio_url
        """
        word = self.word
        
        if self.card_type == 'normal':
            return {
                'text': word.original_word,
                'image_url': word.image_file.url if word.image_file else None,
                'audio_url': word.audio_file.url if word.audio_file else None,
            }
        
        elif self.card_type == 'inverted':
            return {
                'text': word.translation,
                'image_url': None,
                'audio_url': None,
            }
        
        elif self.card_type == 'empty':
            return {
                'text': None,
                'image_url': word.image_file.url if word.image_file else None,
                'audio_url': word.audio_file.url if word.audio_file else None,
            }
        
        elif self.card_type == 'cloze':
            # Заменяем слово на [...]
            sentence_with_gap = self._create_cloze_text()
            return {
                'text': sentence_with_gap,
                'image_url': word.image_file.url if word.image_file else None,
                'audio_url': None,
            }
        
        return {'text': None, 'image_url': None, 'audio_url': None}
    
    def get_back_content(self):
        """
        Получить контент оборотной стороны карточки.
        
        Returns:
            dict с ключами: text, translation, image_url, audio_url
        """
        word = self.word
        
        if self.card_type == 'normal':
            return {
                'text': word.translation,
                'translation': None,
                'image_url': None,
                'audio_url': None,
            }
        
        elif self.card_type == 'inverted':
            return {
                'text': word.original_word,
                'translation': word.translation,
                'image_url': word.image_file.url if word.image_file else None,
                'audio_url': word.audio_file.url if word.audio_file else None,
            }
        
        elif self.card_type == 'empty':
            return {
                'text': word.original_word,
                'translation': word.translation,
                'image_url': None,
                'audio_url': word.audio_file.url if word.audio_file else None,
            }
        
        elif self.card_type == 'cloze':
            return {
                'text': word.original_word,
                'translation': word.translation,
                'image_url': None,
                'audio_url': word.audio_file.url if word.audio_file else None,
            }
        
        return {'text': None, 'translation': None, 'image_url': None, 'audio_url': None}
    
    def _create_cloze_text(self):
        """
        Создаёт текст с пропуском для cloze-карточки.
        
        Заменяет слово на позиции cloze_word_index на [...]
        """
        if not self.cloze_sentence:
            return "[...]"
        
        words = self.cloze_sentence.split()
        if 0 <= self.cloze_word_index < len(words):
            words[self.cloze_word_index] = "[...]"
        return " ".join(words)
    
    # ═══════════════════════════════════════════════════════════════
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ═══════════════════════════════════════════════════════════════
    
    def is_due(self):
        """Карточка готова для повторения?"""
        if self.is_suspended:
            return False
        if self.is_in_learning_mode:
            return True  # Новые карточки всегда готовы
        if self.next_review is None:
            return True
        return self.next_review <= timezone.now()
    
    def get_siblings(self):
        """Получить все карточки того же слова"""
        return Card.objects.filter(word=self.word).exclude(pk=self.pk)
    
    def can_be_burned(self, stability_threshold=60):
        """
        Можно ли сжечь эту карточку?
        
        Вспомогательные карточки сгорают когда:
        - Основная карточка (normal) достигла стабильности
        """
        if not self.is_auxiliary:
            return False
        
        # Ищем основную карточку этого слова
        normal_card = Card.objects.filter(
            word=self.word,
            card_type='normal',
            is_suspended=False
        ).first()
        
        if not normal_card:
            return False
        
        return normal_card.interval >= stability_threshold
