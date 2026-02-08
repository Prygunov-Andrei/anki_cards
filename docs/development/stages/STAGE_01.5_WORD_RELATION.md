# 📦 Этап 1.5: Модель WordRelation (связи между словами)

> **Статус**: ✅ Завершён  
> **Тип**: Backend  
> **Зависимости**: Этап 1 (Word Refactoring)  
> **Следующий этап**: 2 (Category)

---

## 🎯 Цель этапа

Реализовать систему связей между словами:
- Синонимы
- Антонимы

**Ключевой принцип**: Каждое слово остаётся **самостоятельной сущностью** со своими карточками. Связи — это просто указатели на другие слова.

---

## 📋 Задачи

### 1. Создание модели WordRelation

- [x] **1.1** Создать модель `WordRelation`
- [x] **1.2** Создать миграцию
- [x] **1.3** Добавить методы в модель `Word`

### 2. API эндпоинты

- [x] **2.1** GET `/api/words/{id}/relations/` — получить все связи слова
- [x] **2.2** POST `/api/words/{id}/add-synonym/` — добавить синоним
- [x] **2.3** POST `/api/words/{id}/add-antonym/` — добавить антоним
- [x] **2.4** DELETE `/api/words/{id}/relations/{relation_id}/` — удалить связь

### 3. Сериализаторы

- [x] **3.1** Создать `WordRelationSerializer`
- [x] **3.2** Обновить `WordSerializer` для включения связей

### 4. Тесты

- [x] **4.1** Unit-тесты модели
- [x] **4.2** API-тесты

---

## 📁 Файлы для изменения/создания

| Файл | Действие |
|------|----------|
| `backend/apps/words/models.py` | Добавить модель `WordRelation` + методы в `Word` |
| `backend/apps/words/serializers.py` | Добавить `WordRelationSerializer` |
| `backend/apps/words/views.py` | Добавить views для связей |
| `backend/apps/words/urls.py` | Добавить URL-маршруты |
| `backend/apps/words/tests.py` | Добавить тесты |
| `frontend/src/types/index.ts` | Добавить TypeScript типы |

---

## 💻 Код

### 1.1 Модель WordRelation

**Файл**: `backend/apps/words/models.py`

```python
# Добавить в конец файла после класса Word

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
        unique_together = ['word_from', 'word_to', 'relation_type']
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
    def create_bidirectional(cls, word1: 'Word', word2: 'Word', relation_type: str) -> tuple['WordRelation', 'WordRelation']:
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
    def delete_bidirectional(cls, word1: 'Word', word2: 'Word', relation_type: str) -> int:
        """
        Удаляет двустороннюю связь между словами.
        Возвращает количество удалённых связей.
        """
        deleted_count, _ = cls.objects.filter(
            models.Q(word_from=word1, word_to=word2, relation_type=relation_type) |
            models.Q(word_from=word2, word_to=word1, relation_type=relation_type)
        ).delete()
        return deleted_count
```

### 1.2 Методы для модели Word

**Файл**: `backend/apps/words/models.py`

Добавить в класс `Word`:

```python
    # ═══════════════════════════════════════════════════════════════
    # МЕТОДЫ ДЛЯ СВЯЗЕЙ (добавить в класс Word)
    # ═══════════════════════════════════════════════════════════════
    
    def get_synonyms(self):
        """Возвращает QuerySet всех синонимов этого слова"""
        return Word.objects.filter(
            relations_to__word_from=self,
            relations_to__relation_type='synonym'
        )
    
    def get_antonyms(self):
        """Возвращает QuerySet всех антонимов этого слова"""
        return Word.objects.filter(
            relations_to__word_from=self,
            relations_to__relation_type='antonym'
        )
    
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
```

---

### 2.1 Сериализаторы

**Файл**: `backend/apps/words/serializers.py`

```python
# Добавить в конец файла

class WordRelationSerializer(serializers.ModelSerializer):
    """Сериализатор для связи между словами"""
    
    word_to_details = WordListSerializer(source='word_to', read_only=True)
    
    class Meta:
        model = WordRelation
        fields = [
            'id',
            'word_from',
            'word_to',
            'word_to_details',
            'relation_type',
            'created_at',
        ]
        read_only_fields = ['id', 'word_from', 'created_at']


class WordRelationCreateSerializer(serializers.Serializer):
    """Сериализатор для создания связи"""
    
    word_id = serializers.IntegerField(
        help_text='ID слова для связи'
    )
    
    def validate_word_id(self, value):
        """Проверяем, что слово существует и принадлежит пользователю"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Нет контекста запроса")
        
        try:
            word = Word.objects.get(id=value, user=request.user)
        except Word.DoesNotExist:
            raise serializers.ValidationError("Слово не найдено")
        
        return value


class WordWithRelationsSerializer(serializers.ModelSerializer):
    """Сериализатор слова с включёнными связями"""
    
    synonyms = serializers.SerializerMethodField()
    antonyms = serializers.SerializerMethodField()
    
    class Meta:
        model = Word
        fields = [
            'id',
            'original_word',
            'translation',
            'language',
            'card_type',
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
            'synonyms',
            'antonyms',
            'created_at',
            'updated_at',
        ]
    
    def get_synonyms(self, obj):
        """Возвращает список синонимов"""
        return WordListSerializer(obj.get_synonyms(), many=True).data
    
    def get_antonyms(self, obj):
        """Возвращает список антонимов"""
        return WordListSerializer(obj.get_antonyms(), many=True).data
```

---

### 2.2 Views

**Файл**: `backend/apps/words/views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Word, WordRelation
from .serializers import (
    WordSerializer,
    WordListSerializer,
    WordRelationSerializer,
    WordRelationCreateSerializer,
    WordWithRelationsSerializer,
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def words_list_view(request):
    """Получение списка всех слов пользователя"""
    words = Word.objects.filter(user=request.user)
    
    # Фильтрация по языку
    language = request.query_params.get('language', None)
    if language in ['ru', 'en', 'pt', 'de', 'es', 'fr', 'it']:
        words = words.filter(language=language)
    
    # Фильтрация по статусу обучения
    learning_status = request.query_params.get('learning_status', None)
    if learning_status in ['new', 'learning', 'reviewing', 'mastered']:
        words = words.filter(learning_status=learning_status)
    
    # Поиск по словам и переводам
    search = request.query_params.get('search', None)
    if search:
        words = words.filter(
            Q(original_word__icontains=search) |
            Q(translation__icontains=search)
        )
    
    serializer = WordSerializer(words, many=True)
    return Response({
        'count': len(serializer.data),
        'results': serializer.data
    }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════
# WORD RELATIONS API
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_relations_view(request, word_id):
    """Получение всех связей слова (синонимы + антонимы)"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    relations = WordRelation.objects.filter(word_from=word)
    serializer = WordRelationSerializer(relations, many=True)
    
    return Response({
        'word_id': word_id,
        'relations': serializer.data,
        'synonyms_count': relations.filter(relation_type='synonym').count(),
        'antonyms_count': relations.filter(relation_type='antonym').count(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def word_add_synonym_view(request, word_id):
    """Добавление синонима к слову"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    serializer = WordRelationCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    other_word_id = serializer.validated_data['word_id']
    
    # Проверяем, что не пытаемся связать слово с самим собой
    if other_word_id == word_id:
        return Response(
            {'error': 'Слово не может быть синонимом самого себя'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    other_word = get_object_or_404(Word, id=other_word_id, user=request.user)
    
    # Создаём двустороннюю связь
    relation1, relation2 = word.add_synonym(other_word)
    
    return Response({
        'message': 'Синоним добавлен',
        'relation': WordRelationSerializer(relation1).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def word_add_antonym_view(request, word_id):
    """Добавление антонима к слову"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    serializer = WordRelationCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    other_word_id = serializer.validated_data['word_id']
    
    # Проверяем, что не пытаемся связать слово с самим собой
    if other_word_id == word_id:
        return Response(
            {'error': 'Слово не может быть антонимом самого себя'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    other_word = get_object_or_404(Word, id=other_word_id, user=request.user)
    
    # Создаём двустороннюю связь
    relation1, relation2 = word.add_antonym(other_word)
    
    return Response({
        'message': 'Антоним добавлен',
        'relation': WordRelationSerializer(relation1).data
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def word_delete_relation_view(request, word_id, relation_id):
    """Удаление связи между словами"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    # Ищем связь
    relation = get_object_or_404(
        WordRelation,
        id=relation_id,
        word_from=word
    )
    
    # Получаем тип связи и другое слово для удаления обратной связи
    relation_type = relation.relation_type
    other_word = relation.word_to
    
    # Удаляем обе связи (двустороннюю)
    if relation_type == 'synonym':
        deleted_count = word.remove_synonym(other_word)
    else:
        deleted_count = word.remove_antonym(other_word)
    
    return Response({
        'message': 'Связь удалена',
        'deleted_count': deleted_count
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_detail_view(request, word_id):
    """Получение детальной информации о слове (со связями)"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    serializer = WordWithRelationsSerializer(word)
    return Response(serializer.data)
```

---

### 2.3 URL-маршруты

**Файл**: `backend/apps/words/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    # Список слов
    path('list/', views.words_list_view, name='words-list'),
    
    # Детали слова (со связями)
    path('<int:word_id>/', views.word_detail_view, name='word-detail'),
    
    # Связи слова
    path('<int:word_id>/relations/', views.word_relations_view, name='word-relations'),
    path('<int:word_id>/add-synonym/', views.word_add_synonym_view, name='word-add-synonym'),
    path('<int:word_id>/add-antonym/', views.word_add_antonym_view, name='word-add-antonym'),
    path('<int:word_id>/relations/<int:relation_id>/', views.word_delete_relation_view, name='word-delete-relation'),
]
```

---

### 3. TypeScript типы

**Файл**: `frontend/src/types/index.ts`

```typescript
// Добавить после интерфейсов Word

// ========== WORD RELATIONS ==========

export type RelationType = 'synonym' | 'antonym';

export interface WordRelation {
  id: number;
  word_from: number;
  word_to: number;
  word_to_details: Word;
  relation_type: RelationType;
  created_at: string;
}

export interface WordRelationsResponse {
  word_id: number;
  relations: WordRelation[];
  synonyms_count: number;
  antonyms_count: number;
}

export interface AddRelationRequest {
  word_id: number;
}

export interface AddRelationResponse {
  message: string;
  relation: WordRelation;
}

export interface DeleteRelationResponse {
  message: string;
  deleted_count: number;
}

// Расширенный Word с синонимами/антонимами
export interface WordWithRelations extends Word {
  synonyms: Word[];
  antonyms: Word[];
}
```

---

### 4. Миграция

**Файл**: `backend/apps/words/migrations/0007_wordrelation.py`

```python
# Generated manually for Stage 1.5: WordRelation

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('words', '0006_add_training_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='WordRelation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relation_type', models.CharField(
                    choices=[('synonym', 'Синоним'), ('antonym', 'Антоним')],
                    max_length=20,
                    verbose_name='Тип связи'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('word_from', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='relations_from',
                    to='words.word',
                    verbose_name='Исходное слово'
                )),
                ('word_to', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='relations_to',
                    to='words.word',
                    verbose_name='Связанное слово'
                )),
            ],
            options={
                'verbose_name': 'Связь между словами',
                'verbose_name_plural': 'Связи между словами',
            },
        ),
        migrations.AddConstraint(
            model_name='wordrelation',
            constraint=models.UniqueConstraint(
                fields=['word_from', 'word_to', 'relation_type'],
                name='unique_word_relation'
            ),
        ),
        migrations.AddIndex(
            model_name='wordrelation',
            index=models.Index(fields=['word_from', 'relation_type'], name='words_wordr_word_fr_idx'),
        ),
        migrations.AddIndex(
            model_name='wordrelation',
            index=models.Index(fields=['word_to', 'relation_type'], name='words_wordr_word_to_idx'),
        ),
    ]
```

---

## 🧪 Тесты

### Unit-тесты модели

```python
# Добавить в backend/apps/words/tests.py

@pytest.mark.django_db
class TestWordRelationModel:
    """Тесты для модели WordRelation"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def word1(self, user):
        return Word.objects.create(
            user=user,
            original_word='groß',
            translation='большой',
            language='de'
        )
    
    @pytest.fixture
    def word2(self, user):
        return Word.objects.create(
            user=user,
            original_word='klein',
            translation='маленький',
            language='de'
        )
    
    @pytest.fixture
    def word3(self, user):
        return Word.objects.create(
            user=user,
            original_word='riesig',
            translation='огромный',
            language='de'
        )
    
    def test_create_synonym(self, word1, word3):
        """Тест создания синонима"""
        relation1, relation2 = word1.add_synonym(word3)
        
        assert relation1.relation_type == 'synonym'
        assert relation1.word_from == word1
        assert relation1.word_to == word3
        
        # Проверяем обратную связь
        assert relation2.word_from == word3
        assert relation2.word_to == word1
    
    def test_create_antonym(self, word1, word2):
        """Тест создания антонима"""
        relation1, relation2 = word1.add_antonym(word2)
        
        assert relation1.relation_type == 'antonym'
        assert relation1.word_from == word1
        assert relation1.word_to == word2
    
    def test_get_synonyms(self, word1, word3):
        """Тест получения синонимов"""
        word1.add_synonym(word3)
        
        synonyms = word1.get_synonyms()
        assert word3 in synonyms
        
        # Проверяем обратную сторону
        synonyms_of_word3 = word3.get_synonyms()
        assert word1 in synonyms_of_word3
    
    def test_get_antonyms(self, word1, word2):
        """Тест получения антонимов"""
        word1.add_antonym(word2)
        
        antonyms = word1.get_antonyms()
        assert word2 in antonyms
    
    def test_remove_synonym(self, word1, word3):
        """Тест удаления синонима"""
        word1.add_synonym(word3)
        
        deleted_count = word1.remove_synonym(word3)
        assert deleted_count == 2  # Удаляются обе связи
        
        synonyms = word1.get_synonyms()
        assert word3 not in synonyms
    
    def test_cannot_relate_to_self(self, word1):
        """Тест: слово не может быть связано с самим собой"""
        with pytest.raises(ValueError):
            WordRelation.objects.create(
                word_from=word1,
                word_to=word1,
                relation_type='synonym'
            )
    
    def test_unique_constraint(self, word1, word2):
        """Тест уникальности связи"""
        word1.add_synonym(word2)
        
        # Повторное создание не должно дублировать
        relation1, relation2 = word1.add_synonym(word2)
        
        # Должно быть только 2 связи (A→B и B→A)
        count = WordRelation.objects.filter(relation_type='synonym').count()
        assert count == 2
    
    def test_delete_word_cascades_relations(self, user, word1, word2, word3):
        """Тест: при удалении слова удаляются все его связи"""
        word1.add_synonym(word3)
        word1.add_antonym(word2)
        
        word1.delete()
        
        # Все связи должны быть удалены
        relations_count = WordRelation.objects.filter(
            Q(word_from=word1) | Q(word_to=word1)
        ).count()
        assert relations_count == 0
    
    def test_different_users_cannot_relate(self, word1):
        """Тест: нельзя связать слова разных пользователей"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        other_word = Word.objects.create(
            user=other_user,
            original_word='autre',
            translation='другой',
            language='fr'
        )
        
        with pytest.raises(ValueError):
            WordRelation.objects.create(
                word_from=word1,
                word_to=other_word,
                relation_type='synonym'
            )


@pytest.mark.django_db
class TestWordRelationAPI:
    """API тесты для связей между словами"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    
    @pytest.fixture
    def word1(self, user):
        return Word.objects.create(
            user=user,
            original_word='schnell',
            translation='быстрый',
            language='de'
        )
    
    @pytest.fixture
    def word2(self, user):
        return Word.objects.create(
            user=user,
            original_word='langsam',
            translation='медленный',
            language='de'
        )
    
    def test_get_relations_empty(self, client, word1):
        """Тест получения пустого списка связей"""
        response = client.get(f'/api/words/{word1.id}/relations/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['relations'] == []
        assert response.data['synonyms_count'] == 0
        assert response.data['antonyms_count'] == 0
    
    def test_add_synonym(self, client, word1, word2):
        """Тест добавления синонима через API"""
        response = client.post(
            f'/api/words/{word1.id}/add-synonym/',
            {'word_id': word2.id}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['message'] == 'Синоним добавлен'
        assert response.data['relation']['relation_type'] == 'synonym'
    
    def test_add_antonym(self, client, word1, word2):
        """Тест добавления антонима через API"""
        response = client.post(
            f'/api/words/{word1.id}/add-antonym/',
            {'word_id': word2.id}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['message'] == 'Антоним добавлен'
        assert response.data['relation']['relation_type'] == 'antonym'
    
    def test_get_relations_with_data(self, client, word1, word2):
        """Тест получения связей после добавления"""
        word1.add_antonym(word2)
        
        response = client.get(f'/api/words/{word1.id}/relations/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['relations']) == 1
        assert response.data['antonyms_count'] == 1
    
    def test_delete_relation(self, client, word1, word2):
        """Тест удаления связи через API"""
        relation1, _ = word1.add_synonym(word2)
        
        response = client.delete(
            f'/api/words/{word1.id}/relations/{relation1.id}/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['deleted_count'] == 2
        
        # Проверяем, что связей больше нет
        assert word1.get_synonyms().count() == 0
    
    def test_add_self_as_synonym_fails(self, client, word1):
        """Тест: нельзя добавить слово как синоним самого себя"""
        response = client.post(
            f'/api/words/{word1.id}/add-synonym/',
            {'word_id': word1.id}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_word_detail_includes_relations(self, client, word1, word2):
        """Тест: детали слова включают связи"""
        word1.add_antonym(word2)
        
        response = client.get(f'/api/words/{word1.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'antonyms' in response.data
        assert len(response.data['antonyms']) == 1
        assert response.data['antonyms'][0]['original_word'] == 'langsam'
    
    def test_unauthorized_access(self, word1):
        """Тест: неавторизованный доступ запрещён"""
        client = APIClient()  # Без аутентификации
        
        response = client.get(f'/api/words/{word1.id}/relations/')
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]
```

---

## ✅ Definition of Done

Этап считается завершённым, когда:

- [x] Модель `WordRelation` создана
- [x] Миграция успешно применена
- [x] Методы `Word` для связей работают (`get_synonyms`, `get_antonyms`, `add_synonym`, `add_antonym`, `remove_*`)
- [x] API эндпоинты реализованы и работают
- [x] TypeScript типы обновлены
- [x] Все тесты проходят (`pytest`) — 33/33 тестов прошли
- [x] Двусторонние связи создаются автоматически
- [x] Удаление слова каскадно удаляет связи
- [x] Код прошёл review

---

## 🔄 Команды для выполнения

```bash
# 1. Обновить модели (ручное редактирование)

# 2. Создать и применить миграцию
cd backend
python3 manage.py makemigrations words --name wordrelation
# Или создать вручную 0007_wordrelation.py
python3 manage.py migrate

# 3. Запустить тесты
python3 -m pytest apps/words/tests.py -v

# 4. Проверить API
python3 manage.py runserver
# GET http://localhost:8000/api/words/1/relations/
# POST http://localhost:8000/api/words/1/add-synonym/
# POST http://localhost:8000/api/words/1/add-antonym/
# DELETE http://localhost:8000/api/words/1/relations/1/
```

---

## 📝 Заметки

- **Двусторонние связи**: При создании A→B автоматически создаётся B→A
- **Каскадное удаление**: При удалении слова все его связи удаляются автоматически
- **Валидация пользователя**: Связывать можно только слова одного пользователя
- **Уникальность**: Нельзя создать дубликат связи (unique_together)
- **Генерация AI**: Эндпоинты `/generate-synonym/` и `/generate-antonym/` будут добавлены на Этапе 7

---

> **Предыдущий этап**: [STAGE_01_WORD_REFACTORING.md](./STAGE_01_WORD_REFACTORING.md)  
> **Следующий этап**: [STAGE_02_CATEGORY.md](./STAGE_02_CATEGORY.md)
