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
from .models import GeneratedDeck
from .serializers import CardGenerationSerializer
from .utils import generate_apkg


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
        if word in audio_files:
            audio_path = audio_files[word]
            if os.path.exists(audio_path):
                word_data['audio_file'] = audio_path
                media_files.append(audio_path)
        
        # Добавляем изображение, если есть
        if word in image_files:
            image_path = image_files[word]
            if os.path.exists(image_path):
                word_data['image_file'] = image_path
                media_files.append(image_path)
        
        words_data.append(word_data)
    
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
