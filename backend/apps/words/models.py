from django.db import models
from django.db.models import Q
from django.conf import settings


class Category(models.Model):
    """
    Иерархическая категория для организации слов.
    
    Категории создаются пользователем самостоятельно.
    Поддерживается неограниченная вложенность через parent.
    Примеры: "Еда", "Транспорт", "к отпуску", "1"
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name='Пользователь'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Название'
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='Родительская категория'
    )
    icon = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name='Иконка',
        help_text='Эмодзи (например: 🍎, 🚗, 🐕)'
    )
    order = models.IntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )
    is_learning_active = models.BooleanField(
        default=False,
        verbose_name='Активна для тренировки',
        help_text='True = карточки из категории попадают в общую тренировку'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']
        unique_together = [['user', 'name', 'parent']]
        indexes = [
            models.Index(fields=['user', 'parent']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        """Валидация: категория не может быть своим родителем"""
        if self.pk and self.parent_id == self.pk:
            raise ValueError("Категория не может быть родителем самой себя")
        # Проверка на циклическую зависимость
        if self.parent:
            ancestor = self.parent
            while ancestor:
                if ancestor.pk == self.pk:
                    raise ValueError("Обнаружена циклическая зависимость")
                ancestor = ancestor.parent
        super().save(*args, **kwargs)
    
    def get_ancestors(self) -> list['Category']:
        """
        Возвращает список всех родителей вверх по иерархии.
        Порядок: от непосредственного родителя к корню.
        """
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants(self) -> list['Category']:
        """
        Возвращает список всех потомков вниз по иерархии.
        Рекурсивно обходит все дочерние категории.
        """
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_full_path(self) -> str:
        """
        Возвращает полный путь категории.
        Пример: "Еда → Фрукты → Тропические"
        """
        ancestors = self.get_ancestors()
        ancestors.reverse()
        path = [a.name for a in ancestors] + [self.name]
        return ' → '.join(path)
    
    def get_words_count(self) -> int:
        """Возвращает количество слов в категории (без потомков)"""
        return self.words.count()
    
    def get_total_words_count(self) -> int:
        """Возвращает количество слов в категории и всех потомках"""
        count = self.words.count()
        for descendant in self.get_descendants():
            count += descendant.words.count()
        return count


class Word(models.Model):
    """Модель слова для изучения"""
    
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
    
    CARD_TYPE_CHOICES = [
        ('normal', 'Обычная карточка'),
        ('inverted', 'Инвертированная карточка'),
        ('empty', 'Пустая карточка'),
    ]
    
    LEARNING_STATUS_CHOICES = [
        ('new', 'Новое'),
        ('learning', 'В изучении'),
        ('reviewing', 'На повторении'),
        ('mastered', 'Освоено'),
    ]
    
    PART_OF_SPEECH_CHOICES = [
        ('noun', 'Существительное'),
        ('verb', 'Глагол'),
        ('adjective', 'Прилагательное'),
        ('adverb', 'Наречие'),
        ('pronoun', 'Местоимение'),
        ('preposition', 'Предлог'),
        ('conjunction', 'Союз'),
        ('interjection', 'Междометие'),
        ('article', 'Артикль'),
        ('numeral', 'Числительное'),
        ('particle', 'Частица'),
        ('other', 'Другое'),
    ]
    
    # ═══════════════════════════════════════════════════════════════
    # СУЩЕСТВУЮЩИЕ ПОЛЯ
    # ═══════════════════════════════════════════════════════════════
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='words',
        verbose_name='Пользователь'
    )
    original_word = models.CharField(
        max_length=200,
        verbose_name='Исходное слово'
    )
    translation = models.CharField(
        max_length=200,
        verbose_name='Перевод'
    )
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        verbose_name='Язык'
    )
    # DEPRECATED: card_type переедет в модель Card (Этап 3)
    # Пока оставляем для обратной совместимости
    card_type = models.CharField(
        max_length=10,
        choices=CARD_TYPE_CHOICES,
        default='normal',
        verbose_name='Тип карточки (deprecated)',
        help_text='DEPRECATED: Будет удалено после миграции на Card'
    )
    audio_file = models.FileField(
        upload_to='audio/',
        null=True,
        blank=True,
        verbose_name='Аудиофайл'
    )
    image_file = models.ImageField(
        upload_to='images/',
        null=True,
        blank=True,
        verbose_name='Изображение'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    # ═══════════════════════════════════════════════════════════════
    # НОВЫЕ ПОЛЯ (Этап 1)
    # ═══════════════════════════════════════════════════════════════
    
    # --- Контент (генерируется AI) ---
    etymology = models.TextField(
        blank=True,
        default='',
        verbose_name='Этимология',
        help_text='Происхождение слова, генерируется автоматически'
    )
    
    sentences = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Примеры предложений',
        help_text='Формат: [{"text": "...", "source": "ai|user"}]'
    )
    
    # --- Пользовательский контент ---
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='Заметки пользователя'
    )
    
    # --- Подсказки ---
    hint_text = models.TextField(
        blank=True,
        default='',
        verbose_name='Текстовая подсказка',
        help_text='Описание слова без перевода, на изучаемом языке'
    )
    
    hint_audio = models.FileField(
        upload_to='hints/',
        null=True,
        blank=True,
        verbose_name='Аудио подсказка'
    )
    
    # --- Классификация ---
    part_of_speech = models.CharField(
        max_length=20,
        choices=PART_OF_SPEECH_CHOICES,
        blank=True,
        default='',
        verbose_name='Часть речи'
    )
    
    categories = models.ManyToManyField(
        'Category',
        blank=True,
        related_name='words',
        verbose_name='Категории'
    )
    
    # --- Персонализация ---
    stickers = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Стикеры',
        help_text='Эмоции/наклейки: ["❤️", "⭐", "🔥"]'
    )
    
    # --- Статус обучения ---
    learning_status = models.CharField(
        max_length=20,
        choices=LEARNING_STATUS_CHOICES,
        default='new',
        verbose_name='Статус обучения'
    )
    
    class Meta:
        verbose_name = 'Слово'
        verbose_name_plural = 'Слова'
        ordering = ['-created_at']
        # Уникальный индекс для предотвращения дубликатов
        unique_together = [['user', 'original_word', 'language']]
        indexes = [
            models.Index(fields=['user', 'language']),
            models.Index(fields=['user', 'original_word']),
            models.Index(fields=['user', 'learning_status']),
        ]
    
    def __str__(self):
        return f"{self.original_word} ({self.language}) - {self.translation}"

    # ═══════════════════════════════════════════════════════════════
    # МЕТОДЫ
    # ═══════════════════════════════════════════════════════════════
    
    def add_sentence(self, text: str, source: str = 'user') -> None:
        """Добавляет предложение к слову"""
        if not isinstance(self.sentences, list):
            self.sentences = []
        self.sentences.append({
            'text': text,
            'source': source  # 'ai' или 'user'
        })
        self.save(update_fields=['sentences'])
    
    def add_sticker(self, emoji: str) -> None:
        """Добавляет стикер к слову"""
        if not isinstance(self.stickers, list):
            self.stickers = []
        if emoji not in self.stickers:
            self.stickers.append(emoji)
            self.save(update_fields=['stickers'])
    
    def remove_sticker(self, emoji: str) -> None:
        """Удаляет стикер со слова"""
        if isinstance(self.stickers, list) and emoji in self.stickers:
            self.stickers.remove(emoji)
            self.save(update_fields=['stickers'])
    
    # ═══════════════════════════════════════════════════════════════
    # МЕТОДЫ ДЛЯ СВЯЗЕЙ (Этап 1.5)
    # ═══════════════════════════════════════════════════════════════
    
    def get_synonyms(self):
        """Возвращает QuerySet всех синонимов этого слова"""
        return Word.objects.filter(
            relations_to__word_from=self,
            relations_to__relation_type='synonym'
        ).distinct()
    
    def get_antonyms(self):
        """Возвращает QuerySet всех антонимов этого слова"""
        return Word.objects.filter(
            relations_to__word_from=self,
            relations_to__relation_type='antonym'
        ).distinct()
    
    def get_all_relations(self):
        """Возвращает все связи этого слова (исходящие)"""
        return WordRelation.objects.filter(word_from=self)
    
    def add_synonym(self, other_word: 'Word') -> tuple:
        """
        Добавляет синоним (создаёт двустороннюю связь).
        Возвращает кортеж из двух созданных связей.
        """
        return WordRelation.create_bidirectional(self, other_word, 'synonym')
    
    def add_antonym(self, other_word: 'Word') -> tuple:
        """
        Добавляет антоним (создаёт двустороннюю связь).
        Возвращает кортеж из двух созданных связей.
        """
        return WordRelation.create_bidirectional(self, other_word, 'antonym')
    
    def remove_synonym(self, other_word: 'Word') -> int:
        """Удаляет синоним (удаляет двустороннюю связь)"""
        return WordRelation.delete_bidirectional(self, other_word, 'synonym')
    
    def remove_antonym(self, other_word: 'Word') -> int:
        """Удаляет антоним (удаляет двустороннюю связь)"""
        return WordRelation.delete_bidirectional(self, other_word, 'antonym')


class WordRelation(models.Model):
    """
    Связь между двумя словами (синонимы, антонимы).
    
    Каждое слово остаётся самостоятельной сущностью со своими карточками.
    Связи двусторонние: при создании A→B автоматически создаётся B→A.
    """
    
    RELATION_TYPES = [
        ('synonym', 'Синоним'),
        ('antonym', 'Антоним'),
    ]
    
    word_from = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='relations_from',
        verbose_name='Исходное слово'
    )
    word_to = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='relations_to',
        verbose_name='Связанное слово'
    )
    relation_type = models.CharField(
        max_length=20,
        choices=RELATION_TYPES,
        verbose_name='Тип связи'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Связь между словами'
        verbose_name_plural = 'Связи между словами'
        unique_together = [['word_from', 'word_to', 'relation_type']]
        indexes = [
            models.Index(fields=['word_from', 'relation_type']),
            models.Index(fields=['word_to', 'relation_type']),
        ]
    
    def __str__(self):
        return f"{self.word_from.original_word} --[{self.relation_type}]--> {self.word_to.original_word}"
    
    def save(self, *args, **kwargs):
        """При сохранении проверяем, что не создаём связь слова с самим собой"""
        if self.word_from_id == self.word_to_id:
            raise ValueError("Слово не может быть связано само с собой")
        # Проверяем, что оба слова принадлежат одному пользователю
        if self.word_from.user_id != self.word_to.user_id:
            raise ValueError("Связывать можно только слова одного пользователя")
        super().save(*args, **kwargs)
    
    @classmethod
    def create_bidirectional(cls, word1: Word, word2: Word, relation_type: str) -> tuple:
        """
        Создаёт двустороннюю связь между словами.
        Возвращает кортеж из двух созданных связей.
        """
        relation1, created1 = cls.objects.get_or_create(
            word_from=word1,
            word_to=word2,
            relation_type=relation_type
        )
        relation2, created2 = cls.objects.get_or_create(
            word_from=word2,
            word_to=word1,
            relation_type=relation_type
        )
        return relation1, relation2
    
    @classmethod
    def delete_bidirectional(cls, word1: Word, word2: Word, relation_type: str) -> int:
        """
        Удаляет двустороннюю связь между словами.
        Возвращает количество удалённых связей.
        """
        deleted_count, _ = cls.objects.filter(
            Q(word_from=word1, word_to=word2, relation_type=relation_type) |
            Q(word_from=word2, word_to=word1, relation_type=relation_type)
        ).delete()
        return deleted_count