from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


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
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'preferred_language', 'native_language', 'learning_language'
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
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
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
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'native_language', 'learning_language',
            'theme', 'mode', 'preferred_language', 'image_provider', 'gemini_model', 'audio_provider', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'created_at']
    
    def validate(self, data):
        """Валидация: родной и изучаемый языки не должны совпадать"""
        native = data.get('native_language', self.instance.native_language if self.instance else None)
        learning = data.get('learning_language', self.instance.learning_language if self.instance else None)
        
        if native and learning and native == learning:
            raise serializers.ValidationError({
                'learning_language': 'Родной и изучаемый языки должны быть разными'
            })
        
        return data

