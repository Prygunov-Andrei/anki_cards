# 🃏 Этап 3: Модель Card (единица тренировки)

> **Статус**: 🚧 В разработке  
> **Тип**: Backend  
> **Зависимости**: Этап 1 (Word), Этап 2 (Category)  
> **Следующий этап**: 4 (UserTrainingSettings)

---

## 🎯 Цель этапа

Создать модель `Card` — единицу тренировки, отделённую от слова (`Word`):

- **Word** — знание (контент: перевод, этимология, медиа, примеры)
- **Card** — тренировка (прогресс SM-2, планирование, типы)

Одно слово может иметь несколько карточек разных типов, каждая живёт независимо в системе SM-2.

---

## 📋 Ключевые концепции

### Типы карточек

| Тип | Описание | Лицевая сторона | Оборотная сторона | Вспомогательная |
|-----|----------|-----------------|-------------------|-----------------|
| `normal` | Слово → Перевод | Иностранное слово + медиа | Перевод | ❌ Нет |
| `inverted` | Перевод → Слово | Перевод | Иностранное слово + медиа | ❌ Нет |
| `empty` | Медиа → Слово | Только картинка/аудио | Слово + перевод | ✅ Да |
| `cloze` | Предложение с пропуском | Предложение с `[...]` | Пропущенное слово | ✅ Да |

### SM-2 параметры в карточке

```
┌─────────────────────────────────────────────────────────────┐
│                        CARD                                 │
├─────────────────────────────────────────────────────────────┤
│ ease_factor      = 2.5   # Коэффициент лёгкости (min 1.3)  │
│ interval         = 0     # Текущий интервал (дни)          │
│ repetitions      = 0     # Успешных повторений подряд      │
│ lapses           = 0     # Общее количество провалов       │
│ consecutive_lapses = 0   # Провалов подряд (→ Learning)    │
│ learning_step    = 0     # Шаг обучения (0=2мин, 1=10мин)  │
├─────────────────────────────────────────────────────────────┤
│ next_review      = None  # Когда показать                  │
│ last_review      = None  # Когда показывали                │
├─────────────────────────────────────────────────────────────┤
│ is_in_learning_mode = True   # В режиме изучения           │
│ is_auxiliary        = False  # Вспомогательная (сгорает)   │
│ is_suspended        = False  # Приостановлена              │
└─────────────────────────────────────────────────────────────┘
```

### Жизненный цикл карточки

```
┌─────────────┐     Создание      ┌───────────────────┐
│    Word     │ ────────────────► │ Card (normal)     │
│             │   (автоматически) │ is_in_learning=T  │
└─────────────┘                   └───────────────────┘
                                          │
                                          │ Первый показ
                                          ▼
                                  ┌───────────────────┐
                                  │   Learning Mode   │
                                  │ (глубокое изуч.)  │
                                  └───────────────────┘
                                          │
                                          │ После изучения
                                          ▼
                                  ┌───────────────────┐
                                  │   SM-2 Review     │
                                  │ (интервальное)    │
                                  └───────────────────┘
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         │                                │                                │
         ▼                                ▼                                ▼
┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
│ Если 4× "Снова" │              │  interval > 60  │              │  Пользователь   │
│ → Learning Mode │              │ → burn auxiliary│              │ → Suspend/Unsup │
└─────────────────┘              └─────────────────┘              └─────────────────┘
```

---

## 📋 Задачи

### 1. Создание модели Card

- [ ] **1.1** Создать модель `Card` с полями SM-2
- [ ] **1.2** Добавить связь `ForeignKey` к `Word`
- [ ] **1.3** Добавить поля для cloze-карточек
- [ ] **1.4** Добавить методы для создания карточек разных типов
- [ ] **1.5** Создать миграцию

### 2. Методы модели Card

- [ ] **2.1** `create_from_word()` — создание карточки из слова
- [ ] **2.2** `create_inverted()` — создание инвертированной
- [ ] **2.3** `create_empty()` — создание пустой
- [ ] **2.4** `create_cloze()` — создание cloze из предложения
- [ ] **2.5** `mark_as_burned()` — "сжигание" вспомогательной карточки
- [ ] **2.6** `get_front_content()` — получить лицевую сторону
- [ ] **2.7** `get_back_content()` — получить оборотную сторону

### 3. Менеджер модели Card

- [ ] **3.1** `CardManager.for_user(user)` — карточки пользователя
- [ ] **3.2** `CardManager.due_for_review(user)` — карточки для повторения
- [ ] **3.3** `CardManager.in_learning(user)` — карточки в режиме изучения
- [ ] **3.4** `CardManager.by_deck(deck)` — карточки по колоде

### 4. Сигналы и автоматизация

- [ ] **4.1** Сигнал при создании Word → автосоздание Card (normal)
- [ ] **4.2** Сигнал при создании inverted/empty/cloze → установка `is_auxiliary`

### 5. Сериализаторы

- [ ] **5.1** `CardSerializer` — полное представление
- [ ] **5.2** `CardListSerializer` — для списков
- [ ] **5.3** `CardCreateSerializer` — для создания доп. карточек
- [ ] **5.4** `CardReviewSerializer` — для отображения на тренировке

### 6. API эндпоинты

- [ ] **6.1** GET `/api/cards/` — список карточек пользователя
- [ ] **6.2** GET `/api/cards/{id}/` — детали карточки
- [ ] **6.3** POST `/api/words/{id}/cards/inverted/` — создать инвертированную
- [ ] **6.4** POST `/api/words/{id}/cards/empty/` — создать пустую
- [ ] **6.5** POST `/api/words/{id}/cards/cloze/` — создать cloze
- [ ] **6.6** DELETE `/api/cards/{id}/` — удалить карточку
- [ ] **6.7** POST `/api/cards/{id}/suspend/` — приостановить
- [ ] **6.8** POST `/api/cards/{id}/unsuspend/` — возобновить

### 7. Тесты

- [ ] **7.1** Unit-тесты модели Card (15+ тестов)
- [ ] **7.2** Unit-тесты CardManager (6+ тестов)
- [ ] **7.3** API-тесты эндпоинтов (10+ тестов)
- [ ] **7.4** Тесты сигналов автосоздания

---

## 📁 Файлы для изменения/создания

| Файл | Действие |
|------|----------|
| `backend/apps/cards/models.py` | ✨ Создать модель `Card` |
| `backend/apps/cards/managers.py` | ✨ Создать `CardManager` |
| `backend/apps/cards/signals.py` | ✨ Сигнал автосоздания |
| `backend/apps/cards/apps.py` | Подключить сигналы |
| `backend/apps/cards/serializers.py` | ✨ Добавить сериализаторы Card |
| `backend/apps/cards/views.py` | ✨ Добавить views для Card |
| `backend/apps/cards/urls.py` | Добавить URL-маршруты |
| `backend/apps/cards/admin.py` | Зарегистрировать Card |
| `backend/apps/cards/tests.py` | ✨ Добавить тесты |
| `frontend/src/types/index.ts` | Добавить TypeScript типы |

---

## 💻 Код

### 1.1 Модель Card

**Файл**: `backend/apps/cards/models.py`

```python
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.words.models import Word


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
        Word,
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
    def create_from_word(cls, word: Word, card_type: str = 'normal') -> 'Card':
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
    def create_inverted(cls, word: Word) -> 'Card':
        """Создаёт инвертированную карточку"""
        return cls.create_from_word(word, 'inverted')
    
    @classmethod
    def create_empty(cls, word: Word) -> 'Card':
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
    def create_cloze(cls, word: Word, sentence: str, word_index: int = 0) -> 'Card':
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
    
    def suspend(self) -> None:
        """Приостановить карточку"""
        self.is_suspended = True
        self.save(update_fields=['is_suspended', 'updated_at'])
    
    def unsuspend(self) -> None:
        """Возобновить карточку"""
        self.is_suspended = False
        self.save(update_fields=['is_suspended', 'updated_at'])
    
    def burn(self) -> None:
        """
        "Сжечь" вспомогательную карточку.
        Помечает как suspended и is_auxiliary=True.
        Не удаляет — можно восстановить.
        """
        if not self.is_auxiliary:
            raise ValueError("Только вспомогательные карточки могут быть сожжены")
        self.is_suspended = True
        self.save(update_fields=['is_suspended', 'updated_at'])
    
    def restore(self) -> None:
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
    
    def enter_learning_mode(self) -> None:
        """Отправить карточку в режим Изучения"""
        self.is_in_learning_mode = True
        self.learning_step = 0
        self.consecutive_lapses = 0
        self.save(update_fields=[
            'is_in_learning_mode', 'learning_step', 
            'consecutive_lapses', 'updated_at'
        ])
    
    def exit_learning_mode(self) -> None:
        """Вывести карточку из режима Изучения"""
        self.is_in_learning_mode = False
        self.save(update_fields=['is_in_learning_mode', 'updated_at'])
    
    # ═══════════════════════════════════════════════════════════════
    # МЕТОДЫ КОНТЕНТА
    # ═══════════════════════════════════════════════════════════════
    
    def get_front_content(self) -> dict:
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
    
    def get_back_content(self) -> dict:
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
    
    def _create_cloze_text(self) -> str:
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
    
    def is_due(self) -> bool:
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
    
    def can_be_burned(self, stability_threshold: int = 60) -> bool:
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
```

---

### 2. Сигнал автосоздания карточки

**Файл**: `backend/apps/cards/signals.py`

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.words.models import Word
from .models import Card


@receiver(post_save, sender=Word)
def create_card_for_new_word(sender, instance, created, **kwargs):
    """
    При создании нового слова автоматически создаём normal-карточку.
    
    Это гарантирует, что каждое слово имеет хотя бы одну карточку
    для тренировки сразу после добавления.
    """
    if created:
        Card.create_from_word(instance, 'normal')
```

---

### 3. Подключение сигналов

**Файл**: `backend/apps/cards/apps.py`

```python
from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cards'
    verbose_name = 'Карточки'

    def ready(self):
        # Импортируем сигналы при запуске приложения
        import apps.cards.signals  # noqa: F401
```

---

### 4. Сериализаторы

**Файл**: `backend/apps/cards/serializers.py`

```python
from rest_framework import serializers
from .models import Card
from apps.words.serializers import WordListSerializer


class CardSerializer(serializers.ModelSerializer):
    """Полное представление карточки"""
    
    word = WordListSerializer(read_only=True)
    front_content = serializers.SerializerMethodField()
    back_content = serializers.SerializerMethodField()
    is_due = serializers.SerializerMethodField()
    
    class Meta:
        model = Card
        fields = [
            'id',
            'word',
            'card_type',
            'cloze_sentence',
            'cloze_word_index',
            # SM-2
            'ease_factor',
            'interval',
            'repetitions',
            'lapses',
            'consecutive_lapses',
            'learning_step',
            # Планирование
            'next_review',
            'last_review',
            # Статусы
            'is_in_learning_mode',
            'is_auxiliary',
            'is_suspended',
            # Контент
            'front_content',
            'back_content',
            'is_due',
            # Мета
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'word', 'ease_factor', 'interval', 'repetitions',
            'lapses', 'consecutive_lapses', 'learning_step',
            'next_review', 'last_review', 'is_auxiliary',
            'created_at', 'updated_at',
        ]
    
    def get_front_content(self, obj) -> dict:
        return obj.get_front_content()
    
    def get_back_content(self, obj) -> dict:
        return obj.get_back_content()
    
    def get_is_due(self, obj) -> bool:
        return obj.is_due()


class CardListSerializer(serializers.ModelSerializer):
    """Сокращённое представление для списков"""
    
    word_text = serializers.CharField(source='word.original_word', read_only=True)
    word_translation = serializers.CharField(source='word.translation', read_only=True)
    is_due = serializers.SerializerMethodField()
    
    class Meta:
        model = Card
        fields = [
            'id',
            'card_type',
            'word_text',
            'word_translation',
            'interval',
            'ease_factor',
            'next_review',
            'is_in_learning_mode',
            'is_auxiliary',
            'is_suspended',
            'is_due',
        ]
    
    def get_is_due(self, obj) -> bool:
        return obj.is_due()


class CardCreateInvertedSerializer(serializers.Serializer):
    """Сериализатор для создания инвертированной карточки"""
    
    word_id = serializers.IntegerField(required=False, help_text="ID слова (опционально, если указан в URL)")
    
    def validate_word_id(self, value):
        from apps.words.models import Word
        
        user = self.context['request'].user
        try:
            Word.objects.get(id=value, user=user)
        except Word.DoesNotExist:
            raise serializers.ValidationError("Слово не найдено")
        return value


class CardCreateEmptySerializer(serializers.Serializer):
    """Сериализатор для создания пустой карточки"""
    pass  # Валидация в view


class CardCreateClozeSerializer(serializers.Serializer):
    """Сериализатор для создания cloze-карточки"""
    
    sentence = serializers.CharField(
        required=True,
        help_text="Предложение с целевым словом"
    )
    word_index = serializers.IntegerField(
        required=False,
        default=0,
        help_text="Индекс слова для пропуска (0-based)"
    )
    
    def validate_sentence(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Предложение не может быть пустым")
        return value.strip()
    
    def validate(self, data):
        sentence = data.get('sentence', '')
        word_index = data.get('word_index', 0)
        
        words = sentence.split()
        if word_index < 0 or word_index >= len(words):
            raise serializers.ValidationError({
                'word_index': f"Индекс должен быть от 0 до {len(words) - 1}"
            })
        
        return data


class CardReviewSerializer(serializers.ModelSerializer):
    """
    Сериализатор для показа карточки на тренировке.
    Содержит только данные, необходимые для отображения.
    """
    
    front_content = serializers.SerializerMethodField()
    
    class Meta:
        model = Card
        fields = [
            'id',
            'card_type',
            'front_content',
            'is_in_learning_mode',
        ]
    
    def get_front_content(self, obj) -> dict:
        return obj.get_front_content()


class CardAnswerSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ответа — показывает оборотную сторону.
    """
    
    front_content = serializers.SerializerMethodField()
    back_content = serializers.SerializerMethodField()
    word_etymology = serializers.CharField(source='word.etymology', read_only=True)
    word_notes = serializers.CharField(source='word.notes', read_only=True)
    word_hint_text = serializers.CharField(source='word.hint_text', read_only=True)
    word_sentences = serializers.JSONField(source='word.sentences', read_only=True)
    
    class Meta:
        model = Card
        fields = [
            'id',
            'card_type',
            'front_content',
            'back_content',
            'is_in_learning_mode',
            'word_etymology',
            'word_notes',
            'word_hint_text',
            'word_sentences',
        ]
    
    def get_front_content(self, obj) -> dict:
        return obj.get_front_content()
    
    def get_back_content(self, obj) -> dict:
        return obj.get_back_content()
```

---

### 5. Views

**Файл**: `backend/apps/cards/views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Card
from .serializers import (
    CardSerializer,
    CardListSerializer,
    CardCreateClozeSerializer,
)
from apps.words.models import Word


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def card_list_view(request):
    """
    GET /api/cards/ — Список карточек пользователя
    
    Query params:
        - type: фильтр по типу (normal, inverted, empty, cloze)
        - learning: true/false — только в режиме изучения
        - suspended: true/false — включая приостановленные
        - word_id: фильтр по слову
    """
    user = request.user
    cards = Card.objects.filter(user=user)
    
    # Фильтры
    card_type = request.query_params.get('type')
    if card_type:
        cards = cards.filter(card_type=card_type)
    
    learning = request.query_params.get('learning')
    if learning == 'true':
        cards = cards.filter(is_in_learning_mode=True)
    elif learning == 'false':
        cards = cards.filter(is_in_learning_mode=False)
    
    suspended = request.query_params.get('suspended')
    if suspended != 'true':
        cards = cards.filter(is_suspended=False)
    
    word_id = request.query_params.get('word_id')
    if word_id:
        cards = cards.filter(word_id=word_id)
    
    serializer = CardListSerializer(cards, many=True)
    return Response(serializer.data)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def card_detail_view(request, card_id):
    """
    GET /api/cards/{id}/ — Детали карточки
    DELETE /api/cards/{id}/ — Удалить карточку
    """
    card = get_object_or_404(Card, id=card_id, user=request.user)
    
    if request.method == 'GET':
        serializer = CardSerializer(card)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        # Нельзя удалить основную карточку, если это единственная
        if card.card_type == 'normal':
            other_cards = Card.objects.filter(word=card.word).exclude(id=card.id).count()
            if other_cards == 0:
                return Response(
                    {'error': 'Нельзя удалить единственную карточку слова'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        card.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_inverted_view(request, word_id):
    """
    POST /api/words/{word_id}/cards/inverted/ — Создать инвертированную карточку
    """
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    # Проверяем, нет ли уже инвертированной
    if Card.objects.filter(word=word, card_type='inverted').exists():
        return Response(
            {'error': 'Инвертированная карточка уже существует'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    card = Card.create_inverted(word)
    serializer = CardSerializer(card)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_empty_view(request, word_id):
    """
    POST /api/words/{word_id}/cards/empty/ — Создать пустую карточку
    """
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    # Проверяем наличие медиа
    if not word.image_file and not word.audio_file:
        return Response(
            {'error': 'Для empty-карточки нужно изображение или аудио'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем, нет ли уже пустой
    if Card.objects.filter(word=word, card_type='empty').exists():
        return Response(
            {'error': 'Пустая карточка уже существует'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    card = Card.create_empty(word)
    serializer = CardSerializer(card)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_cloze_view(request, word_id):
    """
    POST /api/words/{word_id}/cards/cloze/ — Создать cloze-карточку
    
    Body:
        - sentence: str — Предложение с целевым словом
        - word_index: int — Индекс слова для пропуска (0-based)
    """
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    serializer = CardCreateClozeSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    sentence = serializer.validated_data['sentence']
    word_index = serializer.validated_data.get('word_index', 0)
    
    # Проверяем, нет ли уже такой cloze
    if Card.objects.filter(word=word, card_type='cloze', cloze_sentence=sentence).exists():
        return Response(
            {'error': 'Cloze-карточка с этим предложением уже существует'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    card = Card.create_cloze(word, sentence, word_index)
    serializer = CardSerializer(card)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_suspend_view(request, card_id):
    """
    POST /api/cards/{id}/suspend/ — Приостановить карточку
    """
    card = get_object_or_404(Card, id=card_id, user=request.user)
    card.suspend()
    return Response({'status': 'suspended'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_unsuspend_view(request, card_id):
    """
    POST /api/cards/{id}/unsuspend/ — Возобновить карточку
    """
    card = get_object_or_404(Card, id=card_id, user=request.user)
    card.unsuspend()
    return Response({'status': 'unsuspended'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_enter_learning_view(request, card_id):
    """
    POST /api/cards/{id}/enter-learning/ — Отправить в режим Изучения
    """
    card = get_object_or_404(Card, id=card_id, user=request.user)
    card.enter_learning_mode()
    return Response({'status': 'in_learning_mode'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_cards_list_view(request, word_id):
    """
    GET /api/words/{word_id}/cards/ — Все карточки слова
    """
    word = get_object_or_404(Word, id=word_id, user=request.user)
    cards = Card.objects.filter(word=word)
    serializer = CardListSerializer(cards, many=True)
    return Response(serializer.data)
```

---

### 6. URL-маршруты

**Файл**: `backend/apps/cards/urls.py` (обновить)

```python
from django.urls import path
from . import views

urlpatterns = [
    # Существующие маршруты колод...
    # (оставляем как есть)
    
    # ═══════════════════════════════════════════════════════════════
    # КАРТОЧКИ (новые маршруты)
    # ═══════════════════════════════════════════════════════════════
    
    # Список и детали карточек
    path('cards/', views.card_list_view, name='card-list'),
    path('cards/<int:card_id>/', views.card_detail_view, name='card-detail'),
    
    # Состояние карточки
    path('cards/<int:card_id>/suspend/', views.card_suspend_view, name='card-suspend'),
    path('cards/<int:card_id>/unsuspend/', views.card_unsuspend_view, name='card-unsuspend'),
    path('cards/<int:card_id>/enter-learning/', views.card_enter_learning_view, name='card-enter-learning'),
]

# Отдельные маршруты для создания карточек (через words app)
# Добавить в apps/words/urls.py:
# path('words/<int:word_id>/cards/', views.word_cards_list_view, name='word-cards-list'),
# path('words/<int:word_id>/cards/inverted/', views.card_create_inverted_view, name='card-create-inverted'),
# path('words/<int:word_id>/cards/empty/', views.card_create_empty_view, name='card-create-empty'),
# path('words/<int:word_id>/cards/cloze/', views.card_create_cloze_view, name='card-create-cloze'),
```

---

### 7. Регистрация в Admin

**Файл**: `backend/apps/cards/admin.py`

```python
from django.contrib import admin
from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'word', 'card_type', 'user',
        'ease_factor', 'interval', 'next_review',
        'is_in_learning_mode', 'is_auxiliary', 'is_suspended',
    ]
    list_filter = [
        'card_type', 'is_in_learning_mode', 
        'is_auxiliary', 'is_suspended',
    ]
    search_fields = ['word__original_word', 'word__translation']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'word']
    
    fieldsets = (
        ('Основное', {
            'fields': ('user', 'word', 'card_type')
        }),
        ('Cloze', {
            'fields': ('cloze_sentence', 'cloze_word_index'),
            'classes': ('collapse',),
        }),
        ('SM-2 Параметры', {
            'fields': (
                'ease_factor', 'interval', 'repetitions',
                'lapses', 'consecutive_lapses', 'learning_step',
            )
        }),
        ('Планирование', {
            'fields': ('next_review', 'last_review')
        }),
        ('Статусы', {
            'fields': ('is_in_learning_mode', 'is_auxiliary', 'is_suspended')
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
// CARD TYPES (Этап 3)
// ═══════════════════════════════════════════════════════════════

export type CardType = 'normal' | 'inverted' | 'empty' | 'cloze';

export interface CardContent {
  text: string | null;
  translation?: string | null;
  image_url: string | null;
  audio_url: string | null;
}

export interface Card {
  id: number;
  word: Word;
  card_type: CardType;
  cloze_sentence: string;
  cloze_word_index: number;
  // SM-2
  ease_factor: number;
  interval: number;
  repetitions: number;
  lapses: number;
  consecutive_lapses: number;
  learning_step: number;
  // Планирование
  next_review: string | null;
  last_review: string | null;
  // Статусы
  is_in_learning_mode: boolean;
  is_auxiliary: boolean;
  is_suspended: boolean;
  // Контент
  front_content: CardContent;
  back_content: CardContent;
  is_due: boolean;
  // Мета
  created_at: string;
  updated_at: string;
}

export interface CardListItem {
  id: number;
  card_type: CardType;
  word_text: string;
  word_translation: string;
  interval: number;
  ease_factor: number;
  next_review: string | null;
  is_in_learning_mode: boolean;
  is_auxiliary: boolean;
  is_suspended: boolean;
  is_due: boolean;
}

export interface CardCreateClozeRequest {
  sentence: string;
  word_index?: number;
}

export interface CardReview {
  id: number;
  card_type: CardType;
  front_content: CardContent;
  is_in_learning_mode: boolean;
}

export interface CardAnswer {
  id: number;
  card_type: CardType;
  front_content: CardContent;
  back_content: CardContent;
  is_in_learning_mode: boolean;
  word_etymology: string;
  word_notes: string;
  word_hint_text: string;
  word_sentences: Array<{ text: string; source: string }>;
}
```

---

## 🧪 Тесты

### Unit-тесты модели Card

**Файл**: `backend/apps/cards/tests.py`

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status

from apps.words.models import Word
from apps.cards.models import Card

User = get_user_model()


class TestCardModel(TestCase):
    """Unit-тесты модели Card"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.word = Word.objects.create(
            user=self.user,
            original_word='Hund',
            translation='собака',
            language='de'
        )
    
    def test_create_normal_card(self):
        """Тест создания обычной карточки"""
        card = Card.create_from_word(self.word, 'normal')
        
        self.assertEqual(card.card_type, 'normal')
        self.assertEqual(card.word, self.word)
        self.assertEqual(card.user, self.user)
        self.assertEqual(card.ease_factor, 2.5)
        self.assertTrue(card.is_in_learning_mode)
        self.assertFalse(card.is_auxiliary)
        self.assertFalse(card.is_suspended)
    
    def test_create_inverted_card(self):
        """Тест создания инвертированной карточки"""
        card = Card.create_inverted(self.word)
        
        self.assertEqual(card.card_type, 'inverted')
        self.assertFalse(card.is_auxiliary)
    
    def test_create_empty_card_without_media_fails(self):
        """Тест: empty-карточка требует медиа"""
        with self.assertRaises(ValueError) as context:
            Card.create_empty(self.word)
        
        self.assertIn('изображение или аудио', str(context.exception))
    
    def test_create_empty_card_with_image(self):
        """Тест создания empty-карточки с изображением"""
        image = SimpleUploadedFile(
            name='test.jpg',
            content=b'\x89PNG\r\n\x1a\n',
            content_type='image/jpeg'
        )
        self.word.image_file = image
        self.word.save()
        
        card = Card.create_empty(self.word)
        
        self.assertEqual(card.card_type, 'empty')
        self.assertTrue(card.is_auxiliary)
    
    def test_create_cloze_card(self):
        """Тест создания cloze-карточки"""
        sentence = "Der Hund ist groß"
        card = Card.create_cloze(self.word, sentence, word_index=1)
        
        self.assertEqual(card.card_type, 'cloze')
        self.assertEqual(card.cloze_sentence, sentence)
        self.assertEqual(card.cloze_word_index, 1)
        self.assertTrue(card.is_auxiliary)
    
    def test_create_cloze_without_sentence_fails(self):
        """Тест: cloze требует предложение"""
        with self.assertRaises(ValueError):
            Card.create_cloze(self.word, '', 0)
    
    def test_suspend_and_unsuspend(self):
        """Тест приостановки и возобновления"""
        card = Card.create_from_word(self.word)
        
        card.suspend()
        self.assertTrue(card.is_suspended)
        
        card.unsuspend()
        self.assertFalse(card.is_suspended)
    
    def test_enter_and_exit_learning_mode(self):
        """Тест входа/выхода из режима изучения"""
        card = Card.create_from_word(self.word)
        card.is_in_learning_mode = False
        card.save()
        
        card.enter_learning_mode()
        self.assertTrue(card.is_in_learning_mode)
        self.assertEqual(card.learning_step, 0)
        
        card.exit_learning_mode()
        self.assertFalse(card.is_in_learning_mode)
    
    def test_get_front_content_normal(self):
        """Тест получения лицевой стороны normal"""
        card = Card.create_from_word(self.word)
        front = card.get_front_content()
        
        self.assertEqual(front['text'], 'Hund')
        self.assertIsNone(front['image_url'])
        self.assertIsNone(front['audio_url'])
    
    def test_get_front_content_inverted(self):
        """Тест получения лицевой стороны inverted"""
        card = Card.create_inverted(self.word)
        front = card.get_front_content()
        
        self.assertEqual(front['text'], 'собака')
    
    def test_get_back_content_normal(self):
        """Тест получения оборотной стороны normal"""
        card = Card.create_from_word(self.word)
        back = card.get_back_content()
        
        self.assertEqual(back['text'], 'собака')
    
    def test_cloze_text_creation(self):
        """Тест создания текста с пропуском"""
        sentence = "Der Hund ist groß"
        card = Card.create_cloze(self.word, sentence, word_index=1)
        
        cloze_text = card._create_cloze_text()
        self.assertEqual(cloze_text, "Der [...] ist groß")
    
    def test_is_due_new_card(self):
        """Тест: новая карточка готова для показа"""
        card = Card.create_from_word(self.word)
        self.assertTrue(card.is_due())
    
    def test_is_due_suspended_card(self):
        """Тест: приостановленная карточка не готова"""
        card = Card.create_from_word(self.word)
        card.suspend()
        self.assertFalse(card.is_due())
    
    def test_is_due_future_review(self):
        """Тест: карточка с будущим next_review не готова"""
        card = Card.create_from_word(self.word)
        card.is_in_learning_mode = False
        card.next_review = timezone.now() + timedelta(days=1)
        card.save()
        
        self.assertFalse(card.is_due())
    
    def test_is_due_past_review(self):
        """Тест: карточка с прошедшим next_review готова"""
        card = Card.create_from_word(self.word)
        card.is_in_learning_mode = False
        card.next_review = timezone.now() - timedelta(hours=1)
        card.save()
        
        self.assertTrue(card.is_due())


class TestCardManager(TestCase):
    """Тесты менеджера CardManager"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.word1 = Word.objects.create(
            user=self.user,
            original_word='Hund',
            translation='собака',
            language='de'
        )
        self.word2 = Word.objects.create(
            user=self.user,
            original_word='Katze',
            translation='кошка',
            language='de'
        )
    
    def test_for_user(self):
        """Тест получения карточек пользователя"""
        card1 = Card.create_from_word(self.word1)
        card2 = Card.create_from_word(self.word2)
        card2.suspend()
        
        cards = Card.objects.for_user(self.user)
        self.assertEqual(cards.count(), 1)  # Только не приостановленные
    
    def test_due_for_review(self):
        """Тест получения карточек для повторения"""
        card = Card.create_from_word(self.word1)
        card.is_in_learning_mode = False
        card.next_review = timezone.now() - timedelta(hours=1)
        card.save()
        
        due = Card.objects.due_for_review(self.user)
        self.assertEqual(due.count(), 1)
    
    def test_in_learning(self):
        """Тест получения карточек в режиме изучения"""
        card1 = Card.create_from_word(self.word1)
        card2 = Card.create_from_word(self.word2)
        card2.is_in_learning_mode = False
        card2.save()
        
        learning = Card.objects.in_learning(self.user)
        self.assertEqual(learning.count(), 1)
    
    def test_by_word(self):
        """Тест получения карточек по слову"""
        Card.create_from_word(self.word1)
        Card.create_inverted(self.word1)
        Card.create_from_word(self.word2)
        
        cards = Card.objects.by_word(self.word1)
        self.assertEqual(cards.count(), 2)


class TestCardSignals(TestCase):
    """Тесты сигналов автосоздания"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_auto_create_card_on_word_creation(self):
        """Тест: при создании слова автоматически создаётся карточка"""
        word = Word.objects.create(
            user=self.user,
            original_word='Auto',
            translation='машина',
            language='de'
        )
        
        cards = Card.objects.filter(word=word)
        self.assertEqual(cards.count(), 1)
        self.assertEqual(cards.first().card_type, 'normal')


class TestCardAPI(APITestCase):
    """API-тесты для карточек"""
    
    def setUp(self):
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
        # Удаляем автосозданную карточку для чистых тестов
        Card.objects.filter(word=self.word).delete()
    
    def test_list_cards(self):
        """GET /api/cards/ — список карточек"""
        Card.create_from_word(self.word)
        
        response = self.client.get('/api/cards/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_card_detail(self):
        """GET /api/cards/{id}/ — детали карточки"""
        card = Card.create_from_word(self.word)
        
        response = self.client.get(f'/api/cards/{card.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['card_type'], 'normal')
        self.assertIn('front_content', response.data)
        self.assertIn('back_content', response.data)
    
    def test_create_inverted_card(self):
        """POST /api/words/{id}/cards/inverted/"""
        response = self.client.post(f'/api/words/{self.word.id}/cards/inverted/')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['card_type'], 'inverted')
    
    def test_create_cloze_card(self):
        """POST /api/words/{id}/cards/cloze/"""
        data = {
            'sentence': 'Das Haus ist groß',
            'word_index': 1
        }
        
        response = self.client.post(
            f'/api/words/{self.word.id}/cards/cloze/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['card_type'], 'cloze')
        self.assertEqual(response.data['cloze_sentence'], 'Das Haus ist groß')
    
    def test_suspend_card(self):
        """POST /api/cards/{id}/suspend/"""
        card = Card.create_from_word(self.word)
        
        response = self.client.post(f'/api/cards/{card.id}/suspend/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertTrue(card.is_suspended)
    
    def test_unsuspend_card(self):
        """POST /api/cards/{id}/unsuspend/"""
        card = Card.create_from_word(self.word)
        card.suspend()
        
        response = self.client.post(f'/api/cards/{card.id}/unsuspend/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertFalse(card.is_suspended)
    
    def test_delete_auxiliary_card(self):
        """DELETE /api/cards/{id}/ — удаление вспомогательной"""
        self.word.sentences = [{'text': 'Das Haus ist groß', 'source': 'user'}]
        self.word.save()
        card = Card.create_cloze(self.word, 'Das Haus ist groß', 1)
        
        response = self.client.delete(f'/api/cards/{card.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_cannot_delete_only_normal_card(self):
        """DELETE /api/cards/{id}/ — нельзя удалить единственную normal"""
        card = Card.create_from_word(self.word)
        
        response = self.client.delete(f'/api/cards/{card.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_enter_learning_mode(self):
        """POST /api/cards/{id}/enter-learning/"""
        card = Card.create_from_word(self.word)
        card.is_in_learning_mode = False
        card.save()
        
        response = self.client.post(f'/api/cards/{card.id}/enter-learning/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertTrue(card.is_in_learning_mode)
    
    def test_word_cards_list(self):
        """GET /api/words/{id}/cards/ — все карточки слова"""
        Card.create_from_word(self.word)
        Card.create_inverted(self.word)
        
        response = self.client.get(f'/api/words/{self.word.id}/cards/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
```

---

## ✅ Definition of Done

- [ ] Модель `Card` создана с полями SM-2
- [ ] Миграция успешно применена
- [ ] Фабричные методы работают: `create_from_word`, `create_inverted`, `create_empty`, `create_cloze`
- [ ] `CardManager` реализован с методами фильтрации
- [ ] Сигнал автосоздания карточки при создании слова
- [ ] Все API эндпоинты работают
- [ ] Сериализаторы возвращают корректные данные
- [ ] Карточка зарегистрирована в Django Admin
- [ ] TypeScript типы добавлены
- [ ] Все тесты проходят (30+ тестов)
- [ ] `python manage.py check` без ошибок

---

## 🔧 Команды

```bash
# Создание миграции
cd backend && python3 manage.py makemigrations cards

# Применение миграции  
python3 manage.py migrate

# Проверка моделей
python3 manage.py check

# Запуск тестов
python3 -m pytest apps/cards/tests.py -v

# Проверка покрытия
python3 -m pytest apps/cards/tests.py -v --cov=apps.cards --cov-report=term-missing
```

---

## 📝 Примечания

### Почему Card отдельно от Word?

1. **Разделение ответственности**: Word = знание, Card = тренировка
2. **Множественные карточки**: одно слово может иметь 4+ карточки разных типов
3. **Независимый прогресс**: каждая карточка живёт в SM-2 независимо
4. **Вспомогательные карточки**: empty/cloze могут "сгореть", но слово остаётся

### unique_together для Card

```python
unique_together = [['word', 'card_type', 'cloze_sentence']]
```

Это позволяет:
- Одну `normal` карточку на слово
- Одну `inverted` карточку на слово  
- Одну `empty` карточку на слово
- Множество `cloze` карточек с **разными** предложениями

### Интеграция с UserTrainingSettings

Модель `Card` использует значения по умолчанию (ease_factor=2.5, learning_steps=[2,10]).
В Этапе 4 (UserTrainingSettings) начальный ease_factor будет браться из настроек пользователя.
