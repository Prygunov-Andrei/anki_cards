"""
Views для сервера синхронизации Anki
"""
import logging
import json
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def sync_endpoint(request):
    """
    Основной endpoint для синхронизации Anki
    Anki отправляет POST запросы на /sync/ с различными методами
    """
    try:
        # Получаем данные из запроса
        data = json.loads(request.body) if request.body else {}
        method = data.get('method', '')
        
        logger.info(f"Anki sync request: method={method}, user={request.user if hasattr(request, 'user') else 'anonymous'}")
        
        # Базовая аутентификация через HTTP Basic Auth
        # Anki использует username:password для аутентификации
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Basic '):
            return JsonResponse({'err': 'Unauthorized'}, status=401)
        
        # TODO: Реализовать парсинг Basic Auth и проверку пользователя
        
        # Обработка различных методов синхронизации
        if method == 'meta':
            return handle_sync_meta(request, data)
        elif method == 'start':
            return handle_sync_start(request, data)
        elif method == 'applyGraves':
            return handle_apply_graves(request, data)
        elif method == 'applyChanges':
            return handle_apply_changes(request, data)
        elif method == 'chunk':
            return handle_chunk(request, data)
        elif method == 'applyChunk':
            return handle_apply_chunk(request, data)
        elif method == 'sanitize':
            return handle_sanitize(request, data)
        else:
            logger.warning(f"Unknown sync method: {method}")
            return JsonResponse({'err': f'Unknown method: {method}'}, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'err': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in sync endpoint: {str(e)}", exc_info=True)
        return JsonResponse({'err': str(e)}, status=500)


def handle_sync_meta(request, data):
    """
    Обработка запроса метаданных синхронизации
    """
    # TODO: Реализовать получение метаданных коллекции пользователя
    return JsonResponse({
        'scm': 0,  # Schema modification time
        'ts': 0,   # Timestamp
        'mod': 0,  # Modification time
        'usn': 0,  # Update sequence number
        'musn': 0, # Media update sequence number
        'msg': '', # Message
        'cont': False  # Continue flag
    })


def handle_sync_start(request, data):
    """
    Обработка начала синхронизации
    """
    # TODO: Реализовать начало синхронизации
    return JsonResponse({
        'minUsn': 0,
        'lnewer': False,
        'graves': [],
        'tags': [],
        'models': {},
        'decks': {},
        'conf': {}
    })


def handle_apply_graves(request, data):
    """
    Обработка применения удалений (graves)
    """
    # TODO: Реализовать применение удалений
    return JsonResponse({'status': 'ok'})


def handle_apply_changes(request, data):
    """
    Обработка применения изменений
    """
    # TODO: Реализовать применение изменений
    return JsonResponse({'status': 'ok'})


def handle_chunk(request, data):
    """
    Обработка запроса чанка данных
    """
    # TODO: Реализовать отправку чанка данных
    return JsonResponse({'chunk': ''})


def handle_apply_chunk(request, data):
    """
    Обработка применения чанка данных
    """
    # TODO: Реализовать применение чанка данных
    return JsonResponse({'status': 'ok'})


def handle_sanitize(request, data):
    """
    Обработка санитизации данных
    """
    # TODO: Реализовать санитизацию
    return JsonResponse({'status': 'ok'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_deck_to_sync(request):
    """
    Импорт колоды в базу синхронизации Anki пользователя
    Вызывается автоматически при создании колоды
    """
    from apps.cards.models import GeneratedDeck
    from .utils import import_apkg_to_anki_collection
    
    file_id = request.data.get('file_id')
    if not file_id:
        return Response({'error': 'file_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        generated_deck = GeneratedDeck.objects.get(id=file_id, user=request.user)
    except GeneratedDeck.DoesNotExist:
        return Response({'error': 'Deck not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Импортируем .apkg файл в базу синхронизации
    try:
        result = import_apkg_to_anki_collection(
            user=request.user,
            apkg_path=Path(generated_deck.file_path)
        )
        return Response({
            'success': True,
            'message': 'Deck imported to sync collection',
            'result': result
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error importing deck to sync: {str(e)}", exc_info=True)
        return Response({
            'error': f'Failed to import deck: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
