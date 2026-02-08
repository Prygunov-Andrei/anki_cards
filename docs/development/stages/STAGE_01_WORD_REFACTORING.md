# 📦 Этап 1: Рефакторинг модели Word

> **Статус**: ✅ Завершён  
> **Тип**: Backend  
> **Зависимости**: Нет  
> **Следующий этап**: 1.5 (WordRelation)

---

## 🎯 Цель этапа

Расширить существующую модель `Word` новыми полями для поддержки:
- Этимологии (автогенерация AI)
- Примеров предложений (для cloze карточек)
- Подсказок (текст + аудио)
- Заметок пользователя
- Персонализации (стикеры)
- Статуса обучения

---

## 📋 Задачи

### 1. Обновление модели Word

- [x] **1.1** Добавить новые поля в модель
- [x] **1.2** Создать миграцию
- [x] **1.3** Обновить сериализатор
- [x] **1.4** Обновить существующие API эндпоинты
- [x] **1.5** Написать тесты

---

## 📁 Файлы для изменения

| Файл | Действие |
|------|----------|
| `backend/apps/words/models.py` | Изменить |
| `backend/apps/words/serializers.py` | Изменить |
| `backend/apps/words/views.py` | Изменить (если нужно) |
| `backend/apps/words/tests.py` | Изменить/Создать |
| `frontend/src/types/index.ts` | Изменить |

---

## 💻 Код

### 1.1 Обновление модели Word

**Файл**: `backend/apps/words/models.py`

```python
from django.db import models
from django.conf import settings


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
    # СУЩЕСТВУЮЩИЕ ПОЛЯ (не менять!)
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
        choices=[
            ('normal', 'Обычная карточка'),
            ('inverted', 'Инвертированная карточка'),
            ('empty', 'Пустая карточка'),
        ],
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
    # НОВЫЕ ПОЛЯ
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
```

---

### 1.2 Создание миграции

**Команда:**
```bash
cd backend
python manage.py makemigrations words --name add_training_fields
python manage.py migrate
```

**Ожидаемая миграция** (примерно):
```python
# backend/apps/words/migrations/XXXX_add_training_fields.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('words', '0005_fix_all_card_types'),  # Последняя существующая
    ]

    operations = [
        migrations.AddField(
            model_name='word',
            name='etymology',
            field=models.TextField(blank=True, default='', verbose_name='Этимология'),
        ),
        migrations.AddField(
            model_name='word',
            name='sentences',
            field=models.JSONField(blank=True, default=list, verbose_name='Примеры предложений'),
        ),
        migrations.AddField(
            model_name='word',
            name='notes',
            field=models.TextField(blank=True, default='', verbose_name='Заметки пользователя'),
        ),
        migrations.AddField(
            model_name='word',
            name='hint_text',
            field=models.TextField(blank=True, default='', verbose_name='Текстовая подсказка'),
        ),
        migrations.AddField(
            model_name='word',
            name='hint_audio',
            field=models.FileField(blank=True, null=True, upload_to='hints/', verbose_name='Аудио подсказка'),
        ),
        migrations.AddField(
            model_name='word',
            name='part_of_speech',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Часть речи'),
        ),
        migrations.AddField(
            model_name='word',
            name='stickers',
            field=models.JSONField(blank=True, default=list, verbose_name='Стикеры'),
        ),
        migrations.AddField(
            model_name='word',
            name='learning_status',
            field=models.CharField(
                choices=[
                    ('new', 'Новое'),
                    ('learning', 'В изучении'),
                    ('reviewing', 'На повторении'),
                    ('mastered', 'Освоено'),
                ],
                default='new',
                max_length=20,
                verbose_name='Статус обучения'
            ),
        ),
        migrations.AddIndex(
            model_name='word',
            index=models.Index(fields=['user', 'learning_status'], name='words_word_user_id_learning_idx'),
        ),
    ]
```

---

### 1.3 Обновление сериализатора

**Файл**: `backend/apps/words/serializers.py`

```python
from rest_framework import serializers
from .models import Word


class WordSerializer(serializers.ModelSerializer):
    """Сериализатор слова (полный)"""
    
    class Meta:
        model = Word
        fields = [
            'id',
            'original_word',
            'translation',
            'language',
            'card_type',  # deprecated, но пока оставляем
            'audio_file',
            'image_file',
            # Новые поля
            'etymology',
            'sentences',
            'notes',
            'hint_text',
            'hint_audio',
            'part_of_speech',
            'stickers',
            'learning_status',
            # Timestamps
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WordListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка слов (компактный)"""
    
    class Meta:
        model = Word
        fields = [
            'id',
            'original_word',
            'translation',
            'language',
            'audio_file',
            'image_file',
            'learning_status',
            'part_of_speech',
            'created_at',
        ]


class WordCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания слова"""
    
    class Meta:
        model = Word
        fields = [
            'original_word',
            'translation',
            'language',
            'audio_file',
            'image_file',
            'notes',
            'part_of_speech',
        ]


class WordUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления слова"""
    
    class Meta:
        model = Word
        fields = [
            'original_word',
            'translation',
            'audio_file',
            'image_file',
            'etymology',
            'sentences',
            'notes',
            'hint_text',
            'hint_audio',
            'part_of_speech',
            'stickers',
            'learning_status',
        ]
        # Все поля опциональны при PATCH
        extra_kwargs = {field: {'required': False} for field in fields}
```

---

### 1.4 Обновление TypeScript типов

**Файл**: `frontend/src/types/index.ts`

Добавить/обновить:

```typescript
// ========== WORD (обновлённый) ==========

export type LearningStatus = 'new' | 'learning' | 'reviewing' | 'mastered';

export type PartOfSpeech = 
  | 'noun' 
  | 'verb' 
  | 'adjective' 
  | 'adverb' 
  | 'pronoun' 
  | 'preposition' 
  | 'conjunction' 
  | 'interjection' 
  | 'article' 
  | 'numeral' 
  | 'particle' 
  | 'other';

export interface WordSentence {
  text: string;
  source: 'ai' | 'user';
}

export interface Word {
  id: number;
  original_word: string;
  translation: string;
  language: string;
  card_type?: 'normal' | 'inverted' | 'empty'; // deprecated
  audio_file: string | null;
  image_file: string | null;
  
  // Новые поля
  etymology: string;
  sentences: WordSentence[];
  notes: string;
  hint_text: string;
  hint_audio: string | null;
  part_of_speech: PartOfSpeech | '';
  stickers: string[];  // ["❤️", "⭐"]
  learning_status: LearningStatus;
  
  created_at: string;
  updated_at: string;
}

// Для создания слова (без id и timestamps)
export interface WordCreate {
  original_word: string;
  translation: string;
  language: string;
  audio_file?: File | null;
  image_file?: File | null;
  notes?: string;
  part_of_speech?: PartOfSpeech;
}

// Для обновления слова (все опционально)
export interface WordUpdate {
  original_word?: string;
  translation?: string;
  audio_file?: File | null;
  image_file?: File | null;
  etymology?: string;
  sentences?: WordSentence[];
  notes?: string;
  hint_text?: string;
  hint_audio?: File | null;
  part_of_speech?: PartOfSpeech;
  stickers?: string[];
  learning_status?: LearningStatus;
}
```

---

## 🧪 Тесты

**Файл**: `backend/apps/words/tests.py`

```python
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Word

User = get_user_model()


class WordModelTests(TestCase):
    """Тесты модели Word"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_word_with_new_fields(self):
        """Тест создания слова с новыми полями"""
        word = Word.objects.create(
            user=self.user,
            original_word='Hund',
            translation='собака',
            language='de',
            etymology='От древневерхненемецкого hunt',
            notes='Мужской род: der Hund',
            hint_text='Ein Tier mit vier Beinen',
            part_of_speech='noun',
            learning_status='new'
        )
        
        self.assertEqual(word.etymology, 'От древневерхненемецкого hunt')
        self.assertEqual(word.notes, 'Мужской род: der Hund')
        self.assertEqual(word.hint_text, 'Ein Tier mit vier Beinen')
        self.assertEqual(word.part_of_speech, 'noun')
        self.assertEqual(word.learning_status, 'new')
        self.assertEqual(word.sentences, [])
        self.assertEqual(word.stickers, [])
    
    def test_add_sentence(self):
        """Тест добавления предложения"""
        word = Word.objects.create(
            user=self.user,
            original_word='Hund',
            translation='собака',
            language='de'
        )
        
        word.add_sentence('Der Hund läuft schnell.', source='ai')
        word.add_sentence('Mein Hund ist braun.', source='user')
        
        word.refresh_from_db()
        self.assertEqual(len(word.sentences), 2)
        self.assertEqual(word.sentences[0]['text'], 'Der Hund läuft schnell.')
        self.assertEqual(word.sentences[0]['source'], 'ai')
        self.assertEqual(word.sentences[1]['source'], 'user')
    
    def test_add_sticker(self):
        """Тест добавления стикера"""
        word = Word.objects.create(
            user=self.user,
            original_word='Liebe',
            translation='любовь',
            language='de'
        )
        
        word.add_sticker('❤️')
        word.add_sticker('⭐')
        word.add_sticker('❤️')  # Дубликат не должен добавиться
        
        word.refresh_from_db()
        self.assertEqual(word.stickers, ['❤️', '⭐'])
    
    def test_remove_sticker(self):
        """Тест удаления стикера"""
        word = Word.objects.create(
            user=self.user,
            original_word='Test',
            translation='тест',
            language='de',
            stickers=['❤️', '⭐', '🔥']
        )
        
        word.remove_sticker('⭐')
        
        word.refresh_from_db()
        self.assertEqual(word.stickers, ['❤️', '🔥'])
    
    def test_learning_status_default(self):
        """Тест дефолтного статуса обучения"""
        word = Word.objects.create(
            user=self.user,
            original_word='Test',
            translation='тест',
            language='de'
        )
        
        self.assertEqual(word.learning_status, 'new')
    
    def test_learning_status_choices(self):
        """Тест валидных статусов обучения"""
        for status_code, _ in Word.LEARNING_STATUS_CHOICES:
            word = Word.objects.create(
                user=self.user,
                original_word=f'Test_{status_code}',
                translation='тест',
                language='de',
                learning_status=status_code
            )
            self.assertEqual(word.learning_status, status_code)


class WordAPITests(APITestCase):
    """Тесты API для Word"""
    
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
            language='de',
            learning_status='new'
        )
    
    def test_get_word_with_new_fields(self):
        """Тест получения слова с новыми полями"""
        response = self.client.get(f'/api/words/{self.word.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('etymology', response.data)
        self.assertIn('sentences', response.data)
        self.assertIn('notes', response.data)
        self.assertIn('hint_text', response.data)
        self.assertIn('part_of_speech', response.data)
        self.assertIn('stickers', response.data)
        self.assertIn('learning_status', response.data)
    
    def test_update_word_new_fields(self):
        """Тест обновления новых полей слова"""
        data = {
            'etymology': 'От средневерхненемецкого hūs',
            'notes': 'Das Haus - средний род',
            'hint_text': 'Ein Gebäude zum Wohnen',
            'part_of_speech': 'noun',
            'learning_status': 'learning'
        }
        
        response = self.client.patch(f'/api/words/{self.word.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.word.refresh_from_db()
        self.assertEqual(self.word.etymology, 'От средневерхненемецкого hūs')
        self.assertEqual(self.word.notes, 'Das Haus - средний род')
        self.assertEqual(self.word.learning_status, 'learning')
    
    def test_update_stickers(self):
        """Тест обновления стикеров через API"""
        data = {
            'stickers': ['❤️', '⭐']
        }
        
        response = self.client.patch(f'/api/words/{self.word.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.word.refresh_from_db()
        self.assertEqual(self.word.stickers, ['❤️', '⭐'])
    
    def test_filter_by_learning_status(self):
        """Тест фильтрации по статусу обучения"""
        Word.objects.create(
            user=self.user,
            original_word='Katze',
            translation='кошка',
            language='de',
            learning_status='reviewing'
        )
        
        response = self.client.get('/api/words/', {'learning_status': 'new'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должно вернуть только слово со статусом 'new'
        for word in response.data.get('results', []):
            self.assertEqual(word['learning_status'], 'new')
```

---

## ✅ Definition of Done

Этап считается завершённым, когда:

- [x] Все новые поля добавлены в модель Word
- [x] Миграция успешно применена
- [x] Сериализаторы обновлены
- [x] API возвращает новые поля
- [x] TypeScript типы обновлены
- [x] Все тесты проходят (`pytest`)
- [x] Существующий функционал не сломан
- [x] Код прошёл review

---

## 🔄 Команды для выполнения

```bash
# 1. Обновить модель (ручное редактирование)

# 2. Создать и применить миграцию
cd backend
python manage.py makemigrations words --name add_training_fields
python manage.py migrate

# 3. Запустить тесты
pytest apps/words/tests.py -v

# 4. Проверить API
python manage.py runserver
# GET http://localhost:8000/api/words/
# PATCH http://localhost:8000/api/words/1/

# 5. Обновить TypeScript типы (ручное редактирование)
```

---

## 📝 Заметки

- Поле `card_type` помечено как deprecated, но НЕ удаляем — нужно для обратной совместимости до Этапа 3
- `sentences` хранит JSON массив для гибкости
- `stickers` — простой массив emoji строк
- Индекс по `learning_status` для быстрой фильтрации

---

> **Следующий этап**: [STAGE_01.5_WORD_RELATION.md](./STAGE_01.5_WORD_RELATION.md)
