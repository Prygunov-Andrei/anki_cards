# 📦 Этап 2: Модель Category (иерархическая система категорий)

> **Статус**: ✅ Завершён  
> **Тип**: Backend  
> **Зависимости**: Этап 1 (Word Refactoring)  
> **Следующий этап**: 3 (Card)

---

## 🎯 Цель этапа

Реализовать иерархическую систему категорий для слов:
- Категории создаются пользователем самостоятельно
- Неограниченная вложенность (parent-child)
- Слово может принадлежать нескольким категориям (ManyToMany)

**Примеры категорий**:
- Пользователь 1: "Еда", "Транспорт", "Животные"
- Пользователь 2: "1", "мое", "к отпуску"
- Вложенность: "Еда" → "Фрукты" → "Тропические фрукты"

---

## 📋 Задачи

### 1. Создание модели Category

- [x] **1.1** Создать модель `Category`
- [x] **1.2** Добавить методы `get_ancestors()`, `get_descendants()`
- [x] **1.3** Создать миграцию

### 2. Связь Word ↔ Category

- [x] **2.1** Добавить `ManyToManyField` в модель `Word`
- [x] **2.2** Создать миграцию для связи

### 3. API эндпоинты

- [x] **3.1** GET `/api/categories/` — получить дерево категорий
- [x] **3.2** POST `/api/categories/` — создать категорию
- [x] **3.3** PATCH `/api/categories/{id}/` — обновить категорию
- [x] **3.4** DELETE `/api/categories/{id}/` — удалить категорию
- [x] **3.5** GET `/api/categories/{id}/words/` — слова в категории

### 4. Сериализаторы

- [x] **4.1** Создать `CategorySerializer`
- [x] **4.2** Создать `CategoryTreeSerializer` (рекурсивный)
- [x] **4.3** Обновить `WordSerializer` для включения категорий

### 5. Тесты

- [x] **5.1** Unit-тесты модели
- [x] **5.2** API-тесты

---

## 📁 Файлы для изменения/создания

| Файл | Действие |
|------|----------|
| `backend/apps/words/models.py` | Добавить модель `Category`, связь в `Word` |
| `backend/apps/words/serializers.py` | Добавить сериализаторы категорий |
| `backend/apps/words/views.py` | Добавить views для категорий |
| `backend/apps/words/urls.py` | Добавить URL-маршруты |
| `backend/apps/words/admin.py` | Зарегистрировать `Category` |
| `backend/apps/words/tests.py` | Добавить тесты |
| `frontend/src/types/index.ts` | Добавить TypeScript типы |

---

## 💻 Код

### 1.1 Модель Category

**Файл**: `backend/apps/words/models.py`

```python
# Добавить ПЕРЕД классом Word

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
```

### 1.2 Обновление модели Word (добавление связи)

**Файл**: `backend/apps/words/models.py`

В классе `Word` добавить поле `categories` в раздел "НОВЫЕ ПОЛЯ":

```python
    # --- Классификация ---
    part_of_speech = models.CharField(
        max_length=20,
        choices=PART_OF_SPEECH_CHOICES,
        blank=True,
        default='',
        verbose_name='Часть речи'
    )
    
    # НОВОЕ ПОЛЕ: связь с категориями
    categories = models.ManyToManyField(
        'Category',
        blank=True,
        related_name='words',
        verbose_name='Категории'
    )
```

---

### 2. Сериализаторы

**Файл**: `backend/apps/words/serializers.py`

```python
# Добавить после импортов
from .models import Word, WordRelation, Category


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории (плоский)"""
    
    words_count = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'parent',
            'icon',
            'order',
            'words_count',
            'full_path',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_words_count(self, obj):
        return obj.get_words_count()
    
    def get_full_path(self, obj):
        return obj.get_full_path()


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания категории"""
    
    class Meta:
        model = Category
        fields = [
            'name',
            'parent',
            'icon',
            'order',
        ]
    
    def validate_parent(self, value):
        """Проверяем, что parent принадлежит тому же пользователю"""
        if value:
            request = self.context.get('request')
            if request and value.user != request.user:
                raise serializers.ValidationError(
                    "Родительская категория не найдена"
                )
        return value


class CategoryUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления категории"""
    
    class Meta:
        model = Category
        fields = [
            'name',
            'parent',
            'icon',
            'order',
        ]
        extra_kwargs = {field: {'required': False} for field in [
            'name', 'parent', 'icon', 'order'
        ]}
    
    def validate_parent(self, value):
        """Проверяем, что parent принадлежит тому же пользователю и нет цикла"""
        if value:
            request = self.context.get('request')
            if request and value.user != request.user:
                raise serializers.ValidationError(
                    "Родительская категория не найдена"
                )
            # Проверка на цикл
            instance = self.instance
            if instance and value.pk == instance.pk:
                raise serializers.ValidationError(
                    "Категория не может быть родителем самой себя"
                )
            # Проверяем, что parent не является потомком текущей категории
            if instance:
                descendants = instance.get_descendants()
                if value in descendants:
                    raise serializers.ValidationError(
                        "Нельзя установить потомка как родителя"
                    )
        return value


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Рекурсивный сериализатор для дерева категорий.
    Включает вложенные children.
    """
    
    children = serializers.SerializerMethodField()
    words_count = serializers.SerializerMethodField()
    total_words_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'parent',
            'icon',
            'order',
            'words_count',
            'total_words_count',
            'children',
            'created_at',
        ]
    
    def get_children(self, obj):
        """Рекурсивно сериализует дочерние категории"""
        children = obj.children.all().order_by('order', 'name')
        return CategoryTreeSerializer(children, many=True).data
    
    def get_words_count(self, obj):
        return obj.get_words_count()
    
    def get_total_words_count(self, obj):
        return obj.get_total_words_count()


class CategoryListSerializer(serializers.ModelSerializer):
    """Компактный сериализатор для списков (без children)"""
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'icon',
        ]
```

---

### 3. Views

**Файл**: `backend/apps/words/views.py`

```python
# Добавить импорты
from .models import Word, WordRelation, Category
from .serializers import (
    WordSerializer,
    WordListSerializer,
    WordRelationSerializer,
    WordRelationCreateSerializer,
    WordWithRelationsSerializer,
    CategorySerializer,
    CategoryCreateSerializer,
    CategoryUpdateSerializer,
    CategoryTreeSerializer,
)


# ═══════════════════════════════════════════════════════════════
# CATEGORY API
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def categories_list_view(request):
    """
    GET: Получение дерева категорий пользователя
    POST: Создание новой категории
    """
    if request.method == 'GET':
        # Получаем только корневые категории (без parent)
        root_categories = Category.objects.filter(
            user=request.user,
            parent__isnull=True
        ).order_by('order', 'name')
        
        # Формат ответа зависит от параметра
        flat = request.query_params.get('flat', 'false').lower() == 'true'
        
        if flat:
            # Плоский список всех категорий
            all_categories = Category.objects.filter(
                user=request.user
            ).order_by('order', 'name')
            serializer = CategorySerializer(all_categories, many=True)
        else:
            # Дерево категорий
            serializer = CategoryTreeSerializer(root_categories, many=True)
        
        return Response({
            'count': Category.objects.filter(user=request.user).count(),
            'categories': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = CategoryCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        category = serializer.save(user=request.user)
        
        return Response({
            'message': 'Категория создана',
            'category': CategorySerializer(category).data
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def category_detail_view(request, category_id):
    """
    GET: Получение деталей категории
    PATCH: Обновление категории
    DELETE: Удаление категории (и всех потомков)
    """
    category = get_object_or_404(
        Category,
        id=category_id,
        user=request.user
    )
    
    if request.method == 'GET':
        serializer = CategoryTreeSerializer(category)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = CategoryUpdateSerializer(
            category,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        category = serializer.save()
        
        return Response({
            'message': 'Категория обновлена',
            'category': CategorySerializer(category).data
        })
    
    elif request.method == 'DELETE':
        # Считаем, сколько категорий будет удалено (включая потомков)
        descendants = category.get_descendants()
        total_deleted = 1 + len(descendants)
        
        category_name = category.name
        category.delete()  # CASCADE удалит всех потомков
        
        return Response({
            'message': f'Категория "{category_name}" удалена',
            'deleted_count': total_deleted
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_words_view(request, category_id):
    """Получение слов в категории"""
    category = get_object_or_404(
        Category,
        id=category_id,
        user=request.user
    )
    
    # Параметр: включать слова из подкатегорий?
    include_descendants = request.query_params.get(
        'include_descendants', 'false'
    ).lower() == 'true'
    
    if include_descendants:
        # Собираем слова из текущей категории и всех потомков
        category_ids = [category.id] + [d.id for d in category.get_descendants()]
        words = Word.objects.filter(
            user=request.user,
            categories__id__in=category_ids
        ).distinct()
    else:
        words = category.words.filter(user=request.user)
    
    serializer = WordListSerializer(words, many=True)
    
    return Response({
        'category_id': category_id,
        'category_name': category.name,
        'include_descendants': include_descendants,
        'count': words.count(),
        'words': serializer.data
    })


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def word_categories_view(request, word_id):
    """
    POST: Добавить слово в категорию
    DELETE: Удалить слово из категории
    
    Body: {"category_id": 123}
    """
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    category_id = request.data.get('category_id')
    if not category_id:
        return Response(
            {'error': 'category_id обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    category = get_object_or_404(
        Category,
        id=category_id,
        user=request.user
    )
    
    if request.method == 'POST':
        word.categories.add(category)
        return Response({
            'message': f'Слово добавлено в категорию "{category.name}"',
            'word_id': word.id,
            'category_id': category.id
        })
    
    elif request.method == 'DELETE':
        word.categories.remove(category)
        return Response({
            'message': f'Слово удалено из категории "{category.name}"',
            'word_id': word.id,
            'category_id': category.id
        })
```

---

### 4. URL-маршруты

**Файл**: `backend/apps/words/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════
    # WORDS
    # ═══════════════════════════════════════════════════════════════
    
    # Список слов
    path('list/', views.words_list_view, name='words-list'),
    
    # Детали слова (со связями)
    path('<int:word_id>/', views.word_detail_view, name='word-detail'),
    
    # Связи слова (синонимы/антонимы)
    path('<int:word_id>/relations/', views.word_relations_view, name='word-relations'),
    path('<int:word_id>/add-synonym/', views.word_add_synonym_view, name='word-add-synonym'),
    path('<int:word_id>/add-antonym/', views.word_add_antonym_view, name='word-add-antonym'),
    path('<int:word_id>/relations/<int:relation_id>/', views.word_delete_relation_view, name='word-delete-relation'),
    
    # Категории слова
    path('<int:word_id>/categories/', views.word_categories_view, name='word-categories'),
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORIES
    # ═══════════════════════════════════════════════════════════════
    
    # Список/создание категорий
    path('categories/', views.categories_list_view, name='categories-list'),
    
    # Детали/обновление/удаление категории
    path('categories/<int:category_id>/', views.category_detail_view, name='category-detail'),
    
    # Слова в категории
    path('categories/<int:category_id>/words/', views.category_words_view, name='category-words'),
]
```

---

### 5. TypeScript типы

**Файл**: `frontend/src/types/index.ts`

```typescript
// ========== CATEGORY ==========

export interface Category {
  id: number;
  name: string;
  parent: number | null;
  icon: string;
  order: number;
  words_count: number;
  full_path?: string;
  created_at: string;
}

export interface CategoryTree extends Category {
  children: CategoryTree[];
  total_words_count: number;
}

export interface CategoryListItem {
  id: number;
  name: string;
  icon: string;
}

export interface CategoriesResponse {
  count: number;
  categories: CategoryTree[];
}

export interface CategoryCreateRequest {
  name: string;
  parent?: number | null;
  icon?: string;
  order?: number;
}

export interface CategoryUpdateRequest {
  name?: string;
  parent?: number | null;
  icon?: string;
  order?: number;
}

export interface CategoryWordsResponse {
  category_id: number;
  category_name: string;
  include_descendants: boolean;
  count: number;
  words: Word[];
}

export interface WordCategoryRequest {
  category_id: number;
}
```

---

### 6. Миграция

**Файл**: `backend/apps/words/migrations/0008_category_word_categories.py`

```python
# Generated manually for Stage 2: Category

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('words', '0007_wordrelation'),
    ]

    operations = [
        # 1. Создаём модель Category
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('icon', models.CharField(blank=True, default='', max_length=10, help_text='Эмодзи (например: 🍎, 🚗, 🐕)', verbose_name='Иконка')),
                ('order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('parent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='children',
                    to='words.category',
                    verbose_name='Родительская категория'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='categories',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Пользователь'
                )),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
                'ordering': ['order', 'name'],
            },
        ),
        
        # 2. Уникальный constraint
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(
                fields=['user', 'name', 'parent'],
                name='unique_category_name_per_parent'
            ),
        ),
        
        # 3. Индекс
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['user', 'parent'], name='words_categ_user_pa_idx'),
        ),
        
        # 4. Добавляем M2M поле в Word
        migrations.AddField(
            model_name='word',
            name='categories',
            field=models.ManyToManyField(
                blank=True,
                related_name='words',
                to='words.category',
                verbose_name='Категории'
            ),
        ),
    ]
```

---

### 7. Admin

**Файл**: `backend/apps/words/admin.py`

```python
from django.contrib import admin
from .models import Word, WordRelation, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'parent', 'icon', 'order', 'created_at']
    list_filter = ['user', 'parent']
    search_fields = ['name']
    ordering = ['user', 'order', 'name']
```

---

## 🧪 Тесты

### Unit-тесты модели

```python
# Добавить в backend/apps/words/tests.py

@pytest.mark.django_db
class TestCategoryModel:
    """Тесты для модели Category"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def root_category(self, user):
        return Category.objects.create(
            user=user,
            name='Еда',
            icon='🍎'
        )
    
    @pytest.fixture
    def child_category(self, user, root_category):
        return Category.objects.create(
            user=user,
            name='Фрукты',
            parent=root_category,
            icon='🍇'
        )
    
    @pytest.fixture
    def grandchild_category(self, user, child_category):
        return Category.objects.create(
            user=user,
            name='Тропические',
            parent=child_category,
            icon='🥭'
        )
    
    def test_create_category(self, user):
        """Тест создания категории"""
        category = Category.objects.create(
            user=user,
            name='Транспорт',
            icon='🚗'
        )
        
        assert category.name == 'Транспорт'
        assert category.icon == '🚗'
        assert category.parent is None
        assert category.order == 0
    
    def test_create_nested_category(self, root_category, user):
        """Тест создания вложенной категории"""
        child = Category.objects.create(
            user=user,
            name='Овощи',
            parent=root_category
        )
        
        assert child.parent == root_category
        assert child in root_category.children.all()
    
    def test_get_ancestors(self, grandchild_category, child_category, root_category):
        """Тест получения предков"""
        ancestors = grandchild_category.get_ancestors()
        
        assert len(ancestors) == 2
        assert ancestors[0] == child_category
        assert ancestors[1] == root_category
    
    def test_get_descendants(self, root_category, child_category, grandchild_category):
        """Тест получения потомков"""
        descendants = root_category.get_descendants()
        
        assert len(descendants) == 2
        assert child_category in descendants
        assert grandchild_category in descendants
    
    def test_get_full_path(self, grandchild_category):
        """Тест получения полного пути"""
        path = grandchild_category.get_full_path()
        
        assert path == 'Еда → Фрукты → Тропические'
    
    def test_cannot_be_own_parent(self, root_category):
        """Тест: категория не может быть своим родителем"""
        root_category.parent = root_category
        
        with pytest.raises(ValueError):
            root_category.save()
    
    def test_no_circular_dependency(self, root_category, child_category, grandchild_category):
        """Тест: нельзя создать циклическую зависимость"""
        root_category.parent = grandchild_category
        
        with pytest.raises(ValueError):
            root_category.save()
    
    def test_unique_name_per_parent(self, user, root_category):
        """Тест: уникальность имени в рамках родителя"""
        Category.objects.create(
            user=user,
            name='Овощи',
            parent=root_category
        )
        
        # Попытка создать с тем же именем и родителем
        with pytest.raises(Exception):
            Category.objects.create(
                user=user,
                name='Овощи',
                parent=root_category
            )
    
    def test_same_name_different_parent_allowed(self, user, root_category):
        """Тест: одинаковое имя с разными родителями разрешено"""
        Category.objects.create(
            user=user,
            name='Прочее',
            parent=root_category
        )
        
        # Можно создать с тем же именем, но без родителя
        other = Category.objects.create(
            user=user,
            name='Прочее',
            parent=None
        )
        
        assert other.name == 'Прочее'
    
    def test_cascade_delete(self, root_category, child_category, grandchild_category):
        """Тест: каскадное удаление потомков"""
        root_category.delete()
        
        # Все должны быть удалены
        assert Category.objects.filter(name='Еда').count() == 0
        assert Category.objects.filter(name='Фрукты').count() == 0
        assert Category.objects.filter(name='Тропические').count() == 0


@pytest.mark.django_db
class TestWordCategoryRelation:
    """Тесты связи Word ↔ Category"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def category(self, user):
        return Category.objects.create(
            user=user,
            name='Еда'
        )
    
    @pytest.fixture
    def word(self, user):
        return Word.objects.create(
            user=user,
            original_word='Apfel',
            translation='яблоко',
            language='de'
        )
    
    def test_add_word_to_category(self, word, category):
        """Тест добавления слова в категорию"""
        word.categories.add(category)
        
        assert category in word.categories.all()
        assert word in category.words.all()
    
    def test_word_in_multiple_categories(self, user, word, category):
        """Тест: слово может быть в нескольких категориях"""
        category2 = Category.objects.create(
            user=user,
            name='Фрукты'
        )
        
        word.categories.add(category)
        word.categories.add(category2)
        
        assert word.categories.count() == 2
    
    def test_remove_word_from_category(self, word, category):
        """Тест удаления слова из категории"""
        word.categories.add(category)
        word.categories.remove(category)
        
        assert category not in word.categories.all()


@pytest.mark.django_db
class TestCategoryAPI:
    """API тесты для категорий"""
    
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
    def category(self, user):
        return Category.objects.create(
            user=user,
            name='Еда',
            icon='🍎'
        )
    
    def test_list_categories_empty(self, client):
        """Тест получения пустого списка категорий"""
        response = client.get('/api/words/categories/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert response.data['categories'] == []
    
    def test_create_category(self, client):
        """Тест создания категории"""
        response = client.post('/api/words/categories/', {
            'name': 'Транспорт',
            'icon': '🚗'
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['category']['name'] == 'Транспорт'
        assert response.data['category']['icon'] == '🚗'
    
    def test_create_nested_category(self, client, category):
        """Тест создания вложенной категории"""
        response = client.post('/api/words/categories/', {
            'name': 'Фрукты',
            'parent': category.id
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['category']['parent'] == category.id
    
    def test_get_category_tree(self, client, user):
        """Тест получения дерева категорий"""
        root = Category.objects.create(user=user, name='Еда')
        child = Category.objects.create(user=user, name='Фрукты', parent=root)
        
        response = client.get('/api/words/categories/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        
        # Проверяем дерево
        tree = response.data['categories']
        assert len(tree) == 1  # Только корневая
        assert tree[0]['name'] == 'Еда'
        assert len(tree[0]['children']) == 1
        assert tree[0]['children'][0]['name'] == 'Фрукты'
    
    def test_get_flat_categories(self, client, user):
        """Тест получения плоского списка категорий"""
        root = Category.objects.create(user=user, name='Еда')
        child = Category.objects.create(user=user, name='Фрукты', parent=root)
        
        response = client.get('/api/words/categories/?flat=true')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['categories']) == 2
    
    def test_update_category(self, client, category):
        """Тест обновления категории"""
        response = client.patch(f'/api/words/categories/{category.id}/', {
            'name': 'Продукты',
            'icon': '🥗'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['category']['name'] == 'Продукты'
        assert response.data['category']['icon'] == '🥗'
    
    def test_delete_category(self, client, category):
        """Тест удаления категории"""
        response = client.delete(f'/api/words/categories/{category.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert Category.objects.filter(id=category.id).count() == 0
    
    def test_get_category_words(self, client, user, category):
        """Тест получения слов в категории"""
        word = Word.objects.create(
            user=user,
            original_word='Apfel',
            translation='яблоко',
            language='de'
        )
        word.categories.add(category)
        
        response = client.get(f'/api/words/categories/{category.id}/words/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['words'][0]['original_word'] == 'Apfel'
    
    def test_add_word_to_category_api(self, client, user, category):
        """Тест добавления слова в категорию через API"""
        word = Word.objects.create(
            user=user,
            original_word='Birne',
            translation='груша',
            language='de'
        )
        
        response = client.post(f'/api/words/{word.id}/categories/', {
            'category_id': category.id
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert category in word.categories.all()
    
    def test_remove_word_from_category_api(self, client, user, category):
        """Тест удаления слова из категории через API"""
        word = Word.objects.create(
            user=user,
            original_word='Birne',
            translation='груша',
            language='de'
        )
        word.categories.add(category)
        
        response = client.delete(f'/api/words/{word.id}/categories/', {
            'category_id': category.id
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert category not in word.categories.all()
    
    def test_unauthorized_access(self, category):
        """Тест: неавторизованный доступ запрещён"""
        client = APIClient()
        
        response = client.get('/api/words/categories/')
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]
```

---

## ✅ Definition of Done

Этап считается завершённым, когда:

- [x] Модель `Category` создана с полной иерархией
- [x] Миграция успешно применена
- [x] Связь `Word ↔ Category` (ManyToMany) работает
- [x] CRUD API для категорий реализован
- [x] Дерево категорий возвращается корректно
- [x] TypeScript типы обновлены
- [x] Все тесты проходят (`pytest`) — 57/57 тестов прошли
- [x] Каскадное удаление работает
- [x] Защита от циклических зависимостей
- [x] Код прошёл review

---

## 🔄 Команды для выполнения

```bash
# 1. Обновить модели (ручное редактирование)

# 2. Создать и применить миграцию
cd backend
python3 manage.py makemigrations words --name category_word_categories
# Или создать вручную 0008_category_word_categories.py
python3 manage.py migrate

# 3. Запустить тесты
python3 -m pytest apps/words/tests.py -v

# 4. Проверить API
python3 manage.py runserver
# GET http://localhost:8000/api/words/categories/
# POST http://localhost:8000/api/words/categories/
# PATCH http://localhost:8000/api/words/categories/1/
# DELETE http://localhost:8000/api/words/categories/1/
# GET http://localhost:8000/api/words/categories/1/words/
```

---

## 📝 Заметки

- **Иерархия**: Неограниченная вложенность через `parent` ForeignKey
- **Уникальность**: Имя категории уникально в рамках (user, parent)
- **Каскадное удаление**: При удалении категории удаляются все её потомки
- **Циклы**: Защита от циклических зависимостей в `save()`
- **ManyToMany**: Слово может принадлежать нескольким категориям
- **Порядок**: Поле `order` для кастомной сортировки

---

> **Предыдущий этап**: [STAGE_01.5_WORD_RELATION.md](./STAGE_01.5_WORD_RELATION.md)  
> **Следующий этап**: [STAGE_03_CARD.md](./STAGE_03_CARD.md)
