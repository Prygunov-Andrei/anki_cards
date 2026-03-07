from rest_framework import serializers
from .models import LiterarySource, LiteraryText, WordContextMedia, SceneAnchor


class LiterarySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiterarySource
        fields = ['slug', 'name', 'description', 'cover', 'available_languages', 'is_active']
        read_only_fields = fields


class LiteraryTextListSerializer(serializers.ModelSerializer):
    """For table-of-contents listing (without full_text)."""
    languages = serializers.SerializerMethodField()

    class Meta:
        model = LiteraryText
        fields = ['slug', 'title', 'year', 'word_count', 'sort_order', 'languages']
        read_only_fields = fields

    def get_languages(self, obj):
        return obj._languages if hasattr(obj, '_languages') else [obj.language]


class LiteraryTextDetailSerializer(serializers.ModelSerializer):
    """Full text for reader."""
    class Meta:
        model = LiteraryText
        fields = ['slug', 'title', 'language', 'full_text', 'year', 'word_count', 'sort_order']
        read_only_fields = fields


class SceneAnchorCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SceneAnchor
        fields = ['id', 'scene_description', 'characters', 'mood', 'image_file']
        read_only_fields = fields


class WordContextMediaSerializer(serializers.ModelSerializer):
    source = LiterarySourceSerializer(read_only=True)
    anchor = SceneAnchorCompactSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = WordContextMedia
        fields = [
            'id', 'source', 'anchor', 'hint_text', 'hint_audio',
            'sentences', 'audio_file', 'is_fallback', 'match_method',
            'match_score', 'image_url', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_image_url(self, obj):
        if obj.anchor and obj.anchor.image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.anchor.image_file.url)
            return obj.anchor.image_file.url
        return None


class WordContextMediaCompactSerializer(serializers.ModelSerializer):
    """Compact serializer for embedding in WordSerializer."""
    source_slug = serializers.CharField(source='source.slug', read_only=True)
    scene_description = serializers.CharField(
        source='anchor.scene_description', read_only=True, default=''
    )
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = WordContextMedia
        fields = [
            'source_slug', 'hint_text', 'sentences', 'is_fallback',
            'match_method', 'scene_description', 'image_url',
        ]
        read_only_fields = fields

    def get_image_url(self, obj):
        if obj.anchor and obj.anchor.image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.anchor.image_file.url)
            return obj.anchor.image_file.url
        return None
