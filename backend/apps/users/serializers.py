from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from apps.training.models import UserTrainingSettings


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    native_language = serializers.ChoiceField(
        choices=User.NATIVE_LANGUAGE_CHOICES,
        required=False,
        help_text='Родной язык пользователя'
    )
    learning_language = serializers.ChoiceField(
        choices=User.LEARNING_LANGUAGE_CHOICES,
        required=False,
        help_text='Язык изучения'
    )
    age_group = serializers.ChoiceField(
        choices=UserTrainingSettings.AGE_GROUPS,
        required=False,
        default='adult',
        help_text='Возрастная группа (влияет на начальные параметры тренировки)'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'preferred_language', 'native_language', 'learning_language', 'age_group'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'preferred_language': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'Пароли не совпадают'
            })
        
        # Валидация: родной и изучаемый языки не должны совпадать
        native = attrs.get('native_language')
        learning = attrs.get('learning_language')
        
        if native and learning and native == learning:
            raise serializers.ValidationError({
                'learning_language': 'Родной и изучаемый языки должны быть разными'
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        # Извлекаем age_group для передачи в сигнал
        age_group = validated_data.pop('age_group', 'adult')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        # Устанавливаем age_group как атрибут для сигнала
        user._age_group = age_group
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для входа пользователя"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Неверное имя пользователя или пароль')
            if not user.is_active:
                raise serializers.ValidationError('Пользователь неактивен')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Необходимо указать имя пользователя и пароль')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    
    avatar = serializers.ImageField(required=False, allow_null=True)
    native_language = serializers.ChoiceField(
        choices=User.NATIVE_LANGUAGE_CHOICES,
        required=False
    )
    learning_language = serializers.ChoiceField(
        choices=User.LEARNING_LANGUAGE_CHOICES,
        required=False
    )
    
    active_literary_source = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'native_language', 'learning_language',
            'theme', 'mode', 'preferred_language', 'image_provider', 'gemini_model',
            'audio_provider', 'image_style', 'active_literary_source',
            # Per-user LLM settings
            'hint_generation_model', 'scene_description_model',
            'matching_model', 'keyword_extraction_model',
            'hint_temperature', 'scene_description_temperature',
            'matching_temperature', 'keyword_temperature',
            'elevenlabs_voice_id',
            'hint_prompt_template', 'scene_description_prompt',
            'keyword_extraction_prompt', 'image_prompt_template',
            'created_at',
        ]
        read_only_fields = ['id', 'username', 'created_at']

    def get_active_literary_source(self, obj):
        if obj.active_literary_source:
            return obj.active_literary_source.slug
        return None

    def to_internal_value(self, data):
        if 'active_literary_source' in data:
            slug = data.pop('active_literary_source')
            result = super().to_internal_value(data)
            if slug:
                from apps.literary_context.models import LiterarySource
                try:
                    result['active_literary_source'] = LiterarySource.objects.get(
                        slug=slug, is_active=True
                    )
                except LiterarySource.DoesNotExist:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({'active_literary_source': f'Source "{slug}" not found'})
            else:
                result['active_literary_source'] = None
            return result
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Валидация: родной и изучаемый языки не должны совпадать, температуры в диапазоне"""
        native = data.get('native_language', self.instance.native_language if self.instance else None)
        learning = data.get('learning_language', self.instance.learning_language if self.instance else None)

        if native and learning and native == learning:
            raise serializers.ValidationError({
                'learning_language': 'Родной и изучаемый языки должны быть разными'
            })

        # Validate temperatures are in range [0.0, 2.0]
        temp_fields = [
            'hint_temperature', 'scene_description_temperature',
            'matching_temperature', 'keyword_temperature',
        ]
        for field in temp_fields:
            if field in data:
                val = data[field]
                if not (0.0 <= val <= 2.0):
                    raise serializers.ValidationError({
                        field: 'Температура должна быть от 0.0 до 2.0'
                    })

        return data

