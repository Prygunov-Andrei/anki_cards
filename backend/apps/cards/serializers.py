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

