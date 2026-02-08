from rest_framework import serializers
from .models import Word, WordRelation, Category


class WordSerializer(serializers.ModelSerializer):
    """Сериализатор слова (полный)"""
    
    categories = serializers.SerializerMethodField()
    
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
            'categories',
            # Timestamps
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_categories(self, obj):
        """Список категорий (компактный)"""
        return [
            {
                'id': cat.id,
                'name': cat.name,
                'icon': cat.icon
            }
            for cat in obj.categories.all()
        ]


class WordListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка слов (компактный)"""
    
    next_review = serializers.DateTimeField(read_only=True)
    cards_count = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    decks = serializers.SerializerMethodField()
    
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
            'next_review',
            'cards_count',
            'categories',
            'decks',
            'created_at',
        ]
    
    def get_cards_count(self, obj):
        """Количество карточек слова"""
        return obj.cards.count()
    
    def get_categories(self, obj):
        """Список категорий (компактный)"""
        # Используем простой словарь, чтобы избежать циклических зависимостей
        return [
            {
                'id': cat.id,
                'name': cat.name,
                'icon': cat.icon
            }
            for cat in obj.categories.all()
        ]
    
    def get_decks(self, obj):
        """Список колод (компактный)"""
        from apps.cards.serializers import DeckSerializer
        return DeckSerializer(obj.decks.all(), many=True).data


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
        extra_kwargs = {field: {'required': False} for field in [
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
        ]}


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


# ═══════════════════════════════════════════════════════════════
# CATEGORY SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class CategoryListSerializer(serializers.ModelSerializer):
    """Компактный сериализатор для списков (без children)"""
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'icon',
        ]


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


# ═══════════════════════════════════════════════════════════════
# ЭТАП 8: Words Catalog Serializers
# ═══════════════════════════════════════════════════════════════

class WordStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики слова"""
    
    word_id = serializers.IntegerField()
    cards_stats = serializers.DictField()
    learning_status = serializers.CharField()
    has_etymology = serializers.BooleanField()
    has_hint = serializers.BooleanField()
    has_sentences = serializers.BooleanField()
    sentences_count = serializers.IntegerField()
    relations_count = serializers.DictField()
    categories_count = serializers.IntegerField()
    decks_count = serializers.IntegerField()


class WordsStatsSerializer(serializers.Serializer):
    """Сериализатор для общей статистики слов"""
    
    total_words = serializers.IntegerField()
    by_language = serializers.DictField(child=serializers.IntegerField())
    by_status = serializers.DictField(child=serializers.IntegerField())
    by_part_of_speech = serializers.DictField(child=serializers.IntegerField())
    with_etymology = serializers.IntegerField()
    with_hint = serializers.IntegerField()
    with_sentences = serializers.IntegerField()
    total_cards = serializers.IntegerField()
    due_for_review = serializers.IntegerField()


class BulkActionRequestSerializer(serializers.Serializer):
    """Сериализатор для массовых действий"""
    
    word_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100,
        help_text='Список ID слов (максимум 100)'
    )
    action = serializers.ChoiceField(
        choices=[
            'enter_learning',
            'delete',
            'add_to_deck',
            'add_to_category',
            'remove_from_category'
        ],
        help_text='Действие для выполнения'
    )
    params = serializers.DictField(
        required=False,
        default=dict,
        help_text='Дополнительные параметры (deck_id, category_id и т.д.)'
    )
    
    def validate_word_ids(self, value):
        """Проверяем, что все ID валидны"""
        if len(value) > 100:
            raise serializers.ValidationError("Максимум 100 слов за раз")
        return value
    
    def validate_params(self, value):
        """Валидация параметров в зависимости от действия"""
        action = self.initial_data.get('action')
        
        if action == 'add_to_deck':
            if 'deck_id' not in value:
                raise serializers.ValidationError("Для add_to_deck требуется deck_id в params")
        
        if action in ['add_to_category', 'remove_from_category']:
            if 'category_id' not in value:
                raise serializers.ValidationError(f"Для {action} требуется category_id в params")
        
        return value


class BulkActionResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа массовых действий"""
    
    action = serializers.CharField()
    processed = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.DictField(),
        help_text='Список ошибок для неудачных операций'
    )

