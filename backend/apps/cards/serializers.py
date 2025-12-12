from rest_framework import serializers
from .models import UserPrompt

# Константа для всех поддерживаемых языков
LANGUAGE_CHOICES = [
    ('ru', 'Русский'),
    ('en', 'English'),
    ('pt', 'Португальский'),
    ('de', 'Немецкий'),
    ('es', 'Испанский'),
    ('fr', 'Французский'),
    ('it', 'Итальянский'),
]


class CardGenerationSerializer(serializers.Serializer):
    """Сериализатор для генерации карточек"""
    
    words = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Слова через точку с запятой или запятую. Также поддерживается массив слов (JSON)."
    )
    language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=True
    )
    translations = serializers.DictField(
        child=serializers.CharField(),
        required=True,
        help_text="Словарь переводов: {'слово': 'перевод'}"
    )
    audio_files = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="Словарь аудиофайлов: {'слово': 'путь_к_файлу'}"
    )
    image_files = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="Словарь изображений: {'слово': 'путь_к_файлу'}"
    )
    deck_name = serializers.CharField(
        max_length=200,
        required=True
    )
    image_style = serializers.ChoiceField(
        choices=[('minimalistic', 'Минималистичный'), ('balanced', 'Сбалансированный'), ('creative', 'Творческий')],
        required=False,
        default='balanced',
        help_text="Стиль генерации изображений для всей колоды"
    )
    generate_images = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Генерировать изображения"
    )
    generate_audio = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Генерировать аудио"
    )
    save_to_decks = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Сохранить колоду в 'Мои колоды' для последующего редактирования"
    )
    
    def to_internal_value(self, data):
        """
        Переопределяем для поддержки массива слов
        """
        # Если words приходит как массив, преобразуем в строку для CharField
        if 'words' in data and isinstance(data['words'], list):
            # Преобразуем массив в строку через точку с запятой
            data = data.copy()
            data['words'] = '; '.join(str(w) for w in data['words'] if w)
        return super().to_internal_value(data)
    
    def validate_words(self, value):
        """
        Валидация списка слов
        Поддерживает:
        - Строку через точку с запятой: "word1; word2" (предпочтительно)
        - Строку через запятую: "word1, word2" (для обратной совместимости)
        - Массив слов: ["word1", "word2"] (преобразуется в строку в to_internal_value)
        """
        # Если это уже список (массив), возвращаем как есть
        if isinstance(value, list):
            words = [w.strip() for w in value if w and w.strip()]
            if not words:
                raise serializers.ValidationError("Список слов не может быть пустым")
            return words
        
        # Если это строка, парсим её
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise serializers.ValidationError("Список слов не может быть пустым")
            
            # Проверяем, есть ли точка с запятой (приоритетный разделитель)
            if ';' in value:
                # Используем parse_words_input для умного парсинга (точка с запятой)
                from .utils import parse_words_input
                words = parse_words_input(value)
            else:
                # Если нет точки с запятой, пробуем запятую (для обратной совместимости)
                if ',' in value:
                    # Разбиваем по запятой, но аккуратно (не разбиваем запятые внутри скобок)
                    import re
                    # Простой парсинг: разбиваем по запятым, но учитываем скобки
                    parts = []
                    current = ''
                    depth = 0
                    for char in value:
                        if char == '(':
                            depth += 1
                            current += char
                        elif char == ')':
                            depth -= 1
                            current += char
                        elif char == ',' and depth == 0:
                            if current.strip():
                                parts.append(current.strip())
                            current = ''
                        else:
                            current += char
                    if current.strip():
                        parts.append(current.strip())
                    words = [p.strip() for p in parts if p.strip()]
                else:
                    # Одно слово
                    words = [value.strip()]
            
            if not words:
                raise serializers.ValidationError("Список слов не может быть пустым")
            return words
        
        raise serializers.ValidationError("Слова должны быть строкой или массивом")
    
    def validate_translations(self, value):
        """Валидация переводов"""
        if not value:
            raise serializers.ValidationError("Переводы не могут быть пустыми")
        return value


class ImageGenerationSerializer(serializers.Serializer):
    """Сериализатор для генерации изображения (OpenAI или Gemini)"""
    
    word = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Слово для генерации изображения"
    )
    translation = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Перевод слова"
    )
    language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=True
    )
    image_style = serializers.ChoiceField(
        choices=[('minimalistic', 'Минималистичный'), ('balanced', 'Сбалансированный'), ('creative', 'Творческий')],
        required=False,
        default='balanced',
        help_text="Стиль генерации изображения"
    )
    provider = serializers.ChoiceField(
        choices=[('openai', 'OpenAI DALL-E 3'), ('gemini', 'Google Gemini')],
        required=False,
        help_text="Провайдер для генерации изображения (по умолчанию берется из настроек пользователя)"
    )
    gemini_model = serializers.ChoiceField(
        choices=[
            ('gemini-2.5-flash-image', 'Gemini Flash (быстрая, 0.5 токена)'),
            ('nano-banana-pro-preview', 'Nano Banana Pro (новая, 1 токен)')
        ],
        required=False,
        help_text="Модель Gemini для генерации (по умолчанию берется из настроек пользователя)"
    )
    word_id = serializers.IntegerField(
        required=False,
        help_text="ID слова для автоматической привязки медиа (опционально)"
    )


class AudioGenerationSerializer(serializers.Serializer):
    """Сериализатор для генерации аудио через OpenAI TTS или gTTS"""
    
    word = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Слово для генерации аудио"
    )
    language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=True
    )
    provider = serializers.ChoiceField(
        choices=[('openai', 'OpenAI TTS'), ('gtts', 'Google TTS (gTTS)')],
        required=False,
        help_text="Провайдер для генерации аудио (по умолчанию берется из настроек пользователя)"
    )
    word_id = serializers.IntegerField(
        required=False,
        help_text="ID слова для автоматической привязки медиа (опционально)"
    )


class ImageUploadSerializer(serializers.Serializer):
    """Сериализатор для загрузки изображения"""
    
    image = serializers.ImageField(
        required=True,
        help_text="Изображение (JPG или PNG, максимум 10MB)"
    )
    
    def validate_image(self, value):
        """Валидация изображения"""
        # Проверка размера (10MB = 10 * 1024 * 1024 байт)
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Размер файла превышает 10MB. Текущий размер: {value.size / (1024 * 1024):.2f}MB"
            )
        
        # Проверка формата
        allowed_formats = ['JPEG', 'JPG', 'PNG']
        if value.image.format not in allowed_formats:
            raise serializers.ValidationError(
                f"Неподдерживаемый формат. Разрешены: {', '.join(allowed_formats)}"
            )
        
        return value


class AudioUploadSerializer(serializers.Serializer):
    """Сериализатор для загрузки аудио"""
    
    audio = serializers.FileField(
        required=True,
        help_text="Аудиофайл (MP3, максимум 5MB)"
    )
    
    def validate_audio(self, value):
        """Валидация аудиофайла"""
        # Проверка размера (5MB = 5 * 1024 * 1024 байт)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Размер файла превышает 5MB. Текущий размер: {value.size / (1024 * 1024):.2f}MB"
            )
        
        # Проверка формата
        if not value.name.lower().endswith('.mp3'):
            raise serializers.ValidationError("Файл должен быть в формате MP3")
        
        return value


class UserPromptSerializer(serializers.ModelSerializer):
    """Сериализатор для промптов пользователя"""
    
    prompt_type_display = serializers.CharField(
        source='get_prompt_type_display',
        read_only=True
    )
    
    class Meta:
        model = UserPrompt
        fields = [
            'id',
            'prompt_type',
            'prompt_type_display',
            'custom_prompt',
            'is_custom',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserPromptUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления промпта"""
    
    class Meta:
        model = UserPrompt
        fields = ['custom_prompt']
    
    def validate_custom_prompt(self, value):
        """Валидация промпта с проверкой плейсхолдеров"""
        if not value or not value.strip():
            raise serializers.ValidationError("Промпт не может быть пустым")
        return value


class WordAnalysisSerializer(serializers.Serializer):
    """Сериализатор для анализа смешанных языков"""
    
    words = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        min_length=1,
        help_text="Список слов для анализа"
    )
    learning_language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=True
    )
    native_language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=True
    )


class WordTranslationSerializer(serializers.Serializer):
    """Сериализатор для перевода слов"""
    
    words = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        min_length=1,
        help_text="Список слов для перевода"
    )
    learning_language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=True
    )
    native_language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=True
    )


class GermanWordProcessingSerializer(serializers.Serializer):
    """Сериализатор для обработки немецких слов"""
    
    word = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Немецкое слово для обработки"
    )


# ========== ЭТАП 7: Управление колодами и карточками ==========

class WordSerializer(serializers.Serializer):
    """Сериализатор для слова в колоде"""
    
    id = serializers.IntegerField(read_only=True)
    original_word = serializers.CharField(read_only=True)
    translation = serializers.CharField(read_only=True)
    language = serializers.CharField(read_only=True)
    image_file = serializers.SerializerMethodField()
    audio_file = serializers.SerializerMethodField()
    
    def get_image_file(self, obj):
        """Возвращает URL изображения или None"""
        if obj.image_file:
            return obj.image_file.url
        return None
    
    def get_audio_file(self, obj):
        """Возвращает URL аудио или None"""
        if obj.audio_file:
            return obj.audio_file.url
        return None


class DeckSerializer(serializers.ModelSerializer):
    """Сериализатор для колоды (список)"""
    
    words_count = serializers.IntegerField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        from .models import Deck
        model = Deck
        fields = [
            'id', 'name', 'cover', 'target_lang', 'source_lang',
            'words_count', 'user', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeckDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о колоде (со списком слов)"""
    
    words = serializers.SerializerMethodField()
    words_count = serializers.IntegerField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        from .models import Deck
        model = Deck
        fields = [
            'id', 'name', 'cover', 'target_lang', 'source_lang',
            'words', 'words_count', 'user', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_words(self, obj):
        """Возвращает список слов колоды"""
        words = obj.words.all()
        return WordSerializer(words, many=True).data


class DeckCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания колоды"""
    
    class Meta:
        from .models import Deck
        model = Deck
        fields = ['name', 'cover', 'target_lang', 'source_lang']
    
    def validate_name(self, value):
        """Валидация названия колоды"""
        if not value or not value.strip():
            raise serializers.ValidationError("Название колоды не может быть пустым")
        return value.strip()


class DeckUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления колоды"""
    
    class Meta:
        from .models import Deck
        model = Deck
        fields = ['name', 'cover', 'target_lang', 'source_lang']
    
    def validate_name(self, value):
        """Валидация названия колоды"""
        if not value or not value.strip():
            raise serializers.ValidationError("Название колоды не может быть пустым")
        return value.strip()


class DeckWordAddSerializer(serializers.Serializer):
    """Сериализатор для добавления слова в колоду"""
    
    word_id = serializers.IntegerField(
        required=False,
        help_text="ID существующего слова"
    )
    original_word = serializers.CharField(
        required=False,
        max_length=200,
        help_text="Исходное слово (если создается новое)"
    )
    translation = serializers.CharField(
        required=False,
        max_length=200,
        help_text="Перевод слова (если создается новое)"
    )
    language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=False,
        help_text="Язык слова (если создается новое)"
    )
    image_url = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="URL сгенерированного изображения"
    )
    audio_url = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="URL сгенерированного аудио"
    )
    
    def validate(self, attrs):
        """Валидация: либо word_id, либо все поля для нового слова"""
        word_id = attrs.get('word_id')
        original_word = attrs.get('original_word')
        translation = attrs.get('translation')
        language = attrs.get('language')
        
        if word_id:
            # Если указан word_id, остальные поля не нужны
            return attrs
        elif original_word and translation and language:
            # Если указаны все поля для нового слова
            return attrs
        else:
            raise serializers.ValidationError(
                "Необходимо указать либо word_id существующего слова, "
                "либо все поля (original_word, translation, language) для нового слова"
            )


class DeckWordRemoveSerializer(serializers.Serializer):
    """Сериализатор для удаления слова из колоды"""
    
    word_id = serializers.IntegerField(
        required=True,
        help_text="ID слова для удаления"
    )


class DeckMergeSerializer(serializers.Serializer):
    """Сериализатор для объединения колод"""
    
    deck_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=2,
        required=True,
        help_text="Список ID колод для объединения (минимум 2 колоды)"
    )
    target_deck_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID целевой колоды (если не указан, создается новая колода)"
    )
    new_deck_name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="Название новой колоды (используется только если target_deck_id не указан)"
    )
    delete_source_decks = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Удалить исходные колоды после объединения"
    )


class DeckInvertWordSerializer(serializers.Serializer):
    """Сериализатор для инвертирования одного слова в колоде"""
    
    word_id = serializers.IntegerField(
        required=True,
        help_text="ID слова для инвертирования"
    )


class DeckCreateEmptyCardSerializer(serializers.Serializer):
    """Сериализатор для создания пустой карточки для одного слова"""
    
    word_id = serializers.IntegerField(
        required=True,
        help_text="ID слова для создания пустой карточки"
    )

