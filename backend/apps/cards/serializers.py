from rest_framework import serializers


class CardGenerationSerializer(serializers.Serializer):
    """Сериализатор для генерации карточек"""
    
    words = serializers.CharField(
        required=True,
        help_text="Слова через запятую"
    )
    language = serializers.ChoiceField(
        choices=[('pt', 'Португальский'), ('de', 'Немецкий')],
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
    
    def validate_words(self, value):
        """Валидация списка слов"""
        words = [w.strip() for w in value.split(',') if w.strip()]
        if not words:
            raise serializers.ValidationError("Список слов не может быть пустым")
        return words
    
    def validate_translations(self, value):
        """Валидация переводов"""
        if not value:
            raise serializers.ValidationError("Переводы не могут быть пустыми")
        return value


class ImageGenerationSerializer(serializers.Serializer):
    """Сериализатор для генерации изображения через OpenAI"""
    
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
        choices=[('pt', 'Португальский'), ('de', 'Немецкий')],
        required=True
    )


class AudioGenerationSerializer(serializers.Serializer):
    """Сериализатор для генерации аудио через OpenAI"""
    
    word = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Слово для генерации аудио"
    )
    language = serializers.ChoiceField(
        choices=[('pt', 'Португальский'), ('de', 'Немецкий')],
        required=True
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

