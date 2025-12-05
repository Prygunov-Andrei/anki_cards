from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from PIL import Image
import os

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
)

User = get_user_model()

# Максимальный размер файла аватара: 5MB
MAX_AVATAR_SIZE = 5 * 1024 * 1024
# Разрешенные форматы изображений
ALLOWED_IMAGE_FORMATS = ['JPEG', 'PNG', 'WEBP']


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Регистрация нового пользователя"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user_id': user.id,
            'token': token.key,
            'username': user.username,
            'email': user.email,
            'preferred_language': user.preferred_language,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Вход пользователя"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def validate_avatar(avatar_file):
    """
    Валидация загружаемого аватара
    
    Args:
        avatar_file: Загружаемый файл
    
    Raises:
        ValidationError: Если файл не проходит валидацию
    """
    # Проверка размера файла
    if avatar_file.size > MAX_AVATAR_SIZE:
        raise ValidationError(f'Размер файла не должен превышать {MAX_AVATAR_SIZE / (1024 * 1024)}MB')
    
    # Проверка формата файла
    try:
        # Сохраняем текущую позицию
        current_pos = avatar_file.tell()
        avatar_file.seek(0)
        image = Image.open(avatar_file)
        format_name = image.format
        # Возвращаем позицию на начало
        avatar_file.seek(current_pos)
        if format_name not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError(f'Разрешенные форматы: {", ".join(ALLOWED_IMAGE_FORMATS)}')
    except Exception as e:
        # Возвращаем позицию на начало в случае ошибки
        avatar_file.seek(0)
        raise ValidationError('Некорректный файл изображения')


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """Получение и обновление профиля пользователя"""
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        # Валидация аватара, если он загружается
        if 'avatar' in request.FILES:
            try:
                validate_avatar(request.FILES['avatar'])
            except ValidationError as e:
                return Response(
                    {'avatar': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Обработка удаления аватара (отправка пустой строки или null)
        if 'avatar' in request.data and request.data['avatar'] in ['', None]:
            if request.user.avatar:
                # Удаляем старый файл
                if os.path.isfile(request.user.avatar.path):
                    os.remove(request.user.avatar.path)
                request.user.avatar = None
                request.user.save()
        
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
