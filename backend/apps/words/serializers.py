from rest_framework import serializers
from .models import Word


class WordSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Word"""
    
    class Meta:
        model = Word
        fields = [
            'id',
            'original_word',
            'translation',
            'language',
            'audio_file',
            'image_file',
            'card_type',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

