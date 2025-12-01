import os
import uuid
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.storage import default_storage

from apps.words.models import Word
from .models import GeneratedDeck, UserPrompt
from .serializers import (
    CardGenerationSerializer,
    ImageGenerationSerializer,
    AudioGenerationSerializer,
    ImageUploadSerializer,
    AudioUploadSerializer,
    UserPromptSerializer,
    UserPromptUpdateSerializer
)
from .utils import generate_apkg
from .llm_utils import generate_image_with_dalle, generate_audio_with_tts
from .prompt_utils import get_or_create_user_prompt, reset_user_prompt_to_default


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_cards_view(request):
    """
    Генерация карточек Anki
    """
    serializer = CardGenerationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Получаем валидированные данные
    words_list = serializer.validated_data['words']
    language = serializer.validated_data['language']
    translations = serializer.validated_data['translations']
    audio_files = serializer.validated_data.get('audio_files', {})
    image_files = serializer.validated_data.get('image_files', {})
    deck_name = serializer.validated_data['deck_name']
    
    # Подготавливаем данные для генерации
    words_data = []
    media_files = []
    
    # Логируем для отладки
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Обработка слов: {words_list}")
    logger.info(f"Audio files keys: {list(audio_files.keys())}")
    logger.info(f"Image files keys: {list(image_files.keys())}")
    logger.info(f"Audio files values: {list(audio_files.values())}")
    logger.info(f"Image files values: {list(image_files.values())}")
    logger.info(f"Request data keys: {list(request.data.keys())}")
    logger.info(f"Request data audio_files: {request.data.get('audio_files', 'NOT FOUND')}")
    logger.info(f"Request data image_files: {request.data.get('image_files', 'NOT FOUND')}")
    
    for word in words_list:
        # Получаем или создаем слово в БД
        word_obj, created = Word.objects.get_or_create(
            user=request.user,
            original_word=word,
            language=language,
            defaults={
                'translation': translations.get(word, ''),
            }
        )
        
        # Обновляем перевод, если слово уже существовало
        if not created and word_obj.translation != translations.get(word, ''):
            word_obj.translation = translations.get(word, '')
            word_obj.save()
        
        # Подготавливаем данные для карточки
        word_data = {
            'original_word': word,
            'translation': translations.get(word, ''),
        }
        
        # Добавляем аудио, если есть
        # Проверяем точное совпадение и также пробуем найти по ключу
        audio_path = None
        if word in audio_files:
            audio_path = audio_files[word]
        else:
            # Пробуем найти по ключу без учета регистра или с пробелами
            for key, path in audio_files.items():
                if key.strip() == word.strip():
                    audio_path = path
                    break
        
        if audio_path:
            # Проверяем существование файла
            if os.path.exists(audio_path):
                word_data['audio_file'] = audio_path
                if audio_path not in media_files:
                    media_files.append(audio_path)
                logger.info(f"✅ Добавлено аудио для '{word}': {audio_path}")
            else:
                logger.error(f"❌ Файл аудио не существует: {audio_path}")
        else:
            logger.warning(f"⚠️ Аудио не найдено для '{word}'. Доступные ключи: {list(audio_files.keys())}")
        
        # Добавляем изображение, если есть
        image_path = None
        if word in image_files:
            image_path = image_files[word]
        else:
            # Пробуем найти по ключу без учета регистра или с пробелами
            for key, path in image_files.items():
                if key.strip() == word.strip():
                    image_path = path
                    break
        
        if image_path:
            # Проверяем существование файла
            if os.path.exists(image_path):
                word_data['image_file'] = image_path
                if image_path not in media_files:
                    media_files.append(image_path)
                logger.info(f"✅ Добавлено изображение для '{word}': {image_path}")
            else:
                logger.error(f"❌ Файл изображения не существует: {image_path}")
        else:
            logger.warning(f"⚠️ Изображение не найдено для '{word}'. Доступные ключи: {list(image_files.keys())}")
        
        words_data.append(word_data)
    
    # Логируем перед генерацией
    logger.info(f"Генерация .apkg файла:")
    logger.info(f"  - Слов: {len(words_data)}")
    logger.info(f"  - Медиафайлов: {len(media_files)}")
    logger.info(f"  - Пути к медиафайлам: {media_files}")
    for word_data in words_data:
        logger.info(f"  - Слово '{word_data.get('original_word')}': audio={word_data.get('audio_file')}, image={word_data.get('image_file')}")
    
    # Генерируем .apkg файл
    file_id = uuid.uuid4()
    temp_dir = Path(settings.MEDIA_ROOT) / 'temp_files'
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = temp_dir / f"{file_id}.apkg"
    
    try:
        generate_apkg(
            words_data=words_data,
            deck_name=deck_name,
            media_files=media_files if media_files else None,
            output_path=output_path
        )
        
        # Сохраняем информацию о колоде
        generated_deck = GeneratedDeck.objects.create(
            id=file_id,
            user=request.user,
            deck_name=deck_name,
            file_path=str(output_path),
            cards_count=len(words_data) * 2  # Двусторонние карточки
        )
        
        return Response({
            'file_id': file_id,
            'download_url': f'/api/cards/download/{file_id}/',
            'deck_name': deck_name,
            'cards_count': generated_deck.cards_count
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({
            'error': f'Ошибка при генерации карточек: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_cards_view(request, file_id):
    """
    Скачивание сгенерированного .apkg файла
    """
    try:
        generated_deck = GeneratedDeck.objects.get(id=file_id, user=request.user)
    except GeneratedDeck.DoesNotExist:
        raise Http404("Файл не найден")
    
    file_path = Path(generated_deck.file_path)
    
    if not file_path.exists():
        raise Http404("Файл не найден на сервере")
    
    # Отправляем файл
    response = FileResponse(
        open(file_path, 'rb'),
        content_type='application/apkg'
    )
    response['Content-Disposition'] = f'attachment; filename="{generated_deck.deck_name}.apkg"'
    
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_image_view(request):
    """
    Генерация изображения для слова через OpenAI DALL-E 3
    """
    serializer = ImageGenerationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word = serializer.validated_data['word']
    translation = serializer.validated_data['translation']
    language = serializer.validated_data['language']
    image_style = serializer.validated_data.get('image_style', 'balanced')
    
    try:
        # Генерируем изображение с использованием выбранного стиля
        image_path, dalle_prompt = generate_image_with_dalle(
            word=word,
            translation=translation,
            language=language,
            user=request.user,
            native_language='русском',  # TODO: получить из профиля пользователя
            english_translation=None,  # TODO: получить из перевода или API
            image_style=image_style
        )
        
        # Получаем относительный путь для URL
        media_root = Path(settings.MEDIA_ROOT)
        relative_path = image_path.relative_to(media_root)
        image_url = f"{settings.MEDIA_URL}{relative_path}"
        
        # Получаем ID файла из имени
        image_id = image_path.stem
        
        return Response({
            'image_url': image_url,
            'image_id': image_id,
            'file_path': str(image_path),
            'dalle_prompt': dalle_prompt  # Для отладки - показываем промпт в ответе
        }, status=status.HTTP_201_CREATED)
    
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'error': f'Ошибка при генерации изображения: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_audio_view(request):
    """
    Генерация аудио для слова через OpenAI TTS-1-HD
    """
    serializer = AudioGenerationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word = serializer.validated_data['word']
    language = serializer.validated_data['language']
    
    try:
        # Генерируем аудио с использованием промпта пользователя
        audio_path = generate_audio_with_tts(
            word=word,
            language=language,
            user=request.user
        )
        
        # Получаем относительный путь для URL
        media_root = Path(settings.MEDIA_ROOT)
        relative_path = audio_path.relative_to(media_root)
        audio_url = f"{settings.MEDIA_URL}{relative_path}"
        
        # Получаем ID файла из имени
        audio_id = audio_path.stem
        
        return Response({
            'audio_url': audio_url,
            'audio_id': audio_id,
            'file_path': str(audio_path)
        }, status=status.HTTP_201_CREATED)
    
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'error': f'Ошибка при генерации аудио: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image_view(request):
    """
    Загрузка собственного изображения
    """
    serializer = ImageUploadSerializer(data=request.FILES)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    image_file = serializer.validated_data['image']
    
    try:
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        file_extension = Path(image_file.name).suffix.lower()
        
        # Проверяем расширение
        if file_extension not in ['.jpg', '.jpeg', '.png']:
            file_extension = '.jpg'
        
        filename = f"{file_id}{file_extension}"
        
        # Сохраняем файл
        media_root = Path(settings.MEDIA_ROOT)
        images_dir = media_root / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = images_dir / filename
        
        # Сохраняем файл
        with open(file_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)
        
        # Получаем относительный путь для URL
        relative_path = file_path.relative_to(media_root)
        image_url = f"{settings.MEDIA_URL}{relative_path}"
        
        return Response({
            'image_url': image_url,
            'image_id': file_id,
            'file_path': str(file_path)
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({
            'error': f'Ошибка при загрузке изображения: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_audio_view(request):
    """
    Загрузка собственного аудио
    """
    serializer = AudioUploadSerializer(data=request.FILES)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    audio_file = serializer.validated_data['audio']
    
    try:
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.mp3"
        
        # Сохраняем файл
        media_root = Path(settings.MEDIA_ROOT)
        audio_dir = media_root / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = audio_dir / filename
        
        # Сохраняем файл
        with open(file_path, 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
        
        # Получаем относительный путь для URL
        relative_path = file_path.relative_to(media_root)
        audio_url = f"{settings.MEDIA_URL}{relative_path}"
        
        return Response({
            'audio_url': audio_url,
            'audio_id': file_id,
            'file_path': str(file_path)
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({
            'error': f'Ошибка при загрузке аудио: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_prompts_view(request):
    """
    Получение всех промптов пользователя
    """
    try:
        # Получаем или создаем промпты для всех типов
        prompt_types = [choice[0] for choice in UserPrompt.PROMPT_TYPE_CHOICES]
        prompts = []
        
        for prompt_type in prompt_types:
            user_prompt = get_or_create_user_prompt(request.user, prompt_type)
            prompts.append(user_prompt)
        
        serializer = UserPromptSerializer(prompts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': f'Ошибка при получении промптов: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_prompt_view(request, prompt_type):
    """
    Получение конкретного промпта пользователя
    """
    # Проверяем валидность типа промпта
    valid_types = [choice[0] for choice in UserPrompt.PROMPT_TYPE_CHOICES]
    if prompt_type not in valid_types:
        return Response({
            'error': f'Неверный тип промпта. Доступные типы: {", ".join(valid_types)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_prompt = get_or_create_user_prompt(request.user, prompt_type)
        serializer = UserPromptSerializer(user_prompt)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': f'Ошибка при получении промпта: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_prompt_view(request, prompt_type):
    """
    Обновление промпта пользователя
    """
    # Проверяем валидность типа промпта
    valid_types = [choice[0] for choice in UserPrompt.PROMPT_TYPE_CHOICES]
    if prompt_type not in valid_types:
        return Response({
            'error': f'Неверный тип промпта. Доступные типы: {", ".join(valid_types)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_prompt = get_or_create_user_prompt(request.user, prompt_type)
        serializer = UserPromptUpdateSerializer(user_prompt, data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Валидация плейсхолдеров
        try:
            user_prompt.custom_prompt = serializer.validated_data['custom_prompt']
            user_prompt.is_custom = True
            user_prompt.full_clean()  # Вызывает метод clean() модели
            user_prompt.save()
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result_serializer = UserPromptSerializer(user_prompt)
        return Response(result_serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': f'Ошибка при обновлении промпта: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_user_prompt_view(request, prompt_type):
    """
    Сброс промпта до заводских настроек
    """
    # Проверяем валидность типа промпта
    valid_types = [choice[0] for choice in UserPrompt.PROMPT_TYPE_CHOICES]
    if prompt_type not in valid_types:
        return Response({
            'error': f'Неверный тип промпта. Доступные типы: {", ".join(valid_types)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_prompt = reset_user_prompt_to_default(request.user, prompt_type)
        serializer = UserPromptSerializer(user_prompt)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': f'Ошибка при сбросе промпта: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
