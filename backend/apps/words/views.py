from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from .models import Word
from .serializers import WordSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def words_list_view(request):
    """Получение списка всех слов пользователя"""
    words = Word.objects.filter(user=request.user)
    
    # Фильтрация по языку
    language = request.query_params.get('language', None)
    if language in ['pt', 'de']:
        words = words.filter(language=language)
    
    # Поиск по словам и переводам
    search = request.query_params.get('search', None)
    if search:
        words = words.filter(
            Q(original_word__icontains=search) |
            Q(translation__icontains=search)
        )
    
    serializer = WordSerializer(words, many=True)
    return Response({
        'count': len(serializer.data),
        'results': serializer.data
    }, status=status.HTTP_200_OK)
