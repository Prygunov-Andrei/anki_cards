"""
Training views — thin layer: validate input → call service → return response.
"""
import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import UserTrainingSettings, NotificationSettings
from .serializers import (
    UserTrainingSettingsSerializer,
    UserTrainingSettingsUpdateSerializer,
    UserTrainingSettingsDefaultsSerializer,
    TrainingSessionSerializer,
    TrainingAnswerRequestSerializer,
    TrainingAnswerResponseSerializer,
    CardActionRequestSerializer,
    CardActionResponseSerializer,
    TrainingStatsSerializer,
    GenerateEtymologyRequestSerializer,
    GenerateEtymologyResponseSerializer,
    GenerateHintRequestSerializer,
    GenerateHintResponseSerializer,
    GenerateSentenceRequestSerializer,
    GenerateSentenceResponseSerializer,
    GenerateSynonymRequestSerializer,
    NotificationSettingsSerializer,
    NotificationCheckResponseSerializer,
    GenerateSynonymResponseSerializer,
)
from .services.session_service import (
    get_or_create_settings,
    build_training_session,
    process_answer,
    enter_learning_mode,
    exit_learning_mode,
)
from .services.stats_service import (
    get_training_stats,
    get_dashboard_data,
    activate_deck,
    deactivate_deck,
    activate_category,
    deactivate_category,
    get_forgetting_curve_data,
    check_notification,
)
from .services.ai_service import (
    generate_etymology_for_word,
    generate_hint_for_word,
    generate_sentences_for_word,
    generate_synonym_for_word,
)
from apps.cards.models import Card, Deck
from apps.words.models import Word, Category

DEFAULT_AGE_GROUP = 'adult'

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Settings Views
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def training_settings_view(request):
    """GET/PATCH /api/training/settings/"""
    settings = get_or_create_settings(request.user)

    if request.method == 'GET':
        serializer = UserTrainingSettingsSerializer(settings)
        return Response(serializer.data)

    serializer = UserTrainingSettingsUpdateSerializer(
        settings, data=request.data, partial=True
    )
    if serializer.is_valid():
        serializer.save()
        full_serializer = UserTrainingSettingsSerializer(settings)
        return Response(full_serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_settings_reset_view(request):
    """POST /api/training/settings/reset/"""
    settings = get_object_or_404(UserTrainingSettings, user=request.user)
    settings.reset_to_defaults()
    serializer = UserTrainingSettingsSerializer(settings)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_settings_defaults_view(request):
    """GET /api/training/settings/defaults/?age_group=adult"""
    age_group = request.query_params.get('age_group', 'adult')
    serializer = UserTrainingSettingsDefaultsSerializer(data={'age_group': age_group})
    if serializer.is_valid():
        return Response(serializer.to_representation(None))
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════
# Session Views
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_session_view(request):
    """GET /api/training/session/"""
    deck_id = request.query_params.get('deck_id')
    category_id = request.query_params.get('category_id')
    duration = request.query_params.get('duration')
    new_cards = request.query_params.get('new_cards', 'true').lower() == 'true'

    # Validate deck_id
    if deck_id is not None:
        try:
            deck_id = int(deck_id)
        except (ValueError, TypeError):
            return Response(
                {'error': 'deck_id должен быть целым числом'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Validate category_id
    if category_id is not None:
        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            return Response(
                {'error': 'category_id должен быть целым числом'},
                status=status.HTTP_400_BAD_REQUEST
            )

    if deck_id is not None and category_id is not None:
        return Response(
            {'error': 'Нельзя указывать deck_id и category_id одновременно'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate duration
    if duration is not None:
        try:
            duration = int(duration)
            if duration < 1:
                return Response(
                    {'error': 'duration должен быть не менее 1 минуты'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'duration должен быть целым числом'},
                status=status.HTTP_400_BAD_REQUEST
            )

    response_data = build_training_session(
        user=request.user,
        deck_id=deck_id,
        category_id=category_id,
        duration=duration,
        new_cards=new_cards,
        request=request,
    )

    serializer = TrainingSessionSerializer(response_data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_answer_view(request):
    """POST /api/training/answer/"""
    serializer = TrainingAnswerRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    card_id = serializer.validated_data['card_id']
    answer = serializer.validated_data['answer']
    time_spent = serializer.validated_data.get('time_spent')

    try:
        response_data = process_answer(
            user=request.user,
            card_id=card_id,
            answer=answer,
            time_spent=time_spent,
            request=request,
        )
    except Card.DoesNotExist:
        return Response(
            {'error': 'Карточка не найдена или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )

    response_serializer = TrainingAnswerResponseSerializer(response_data)
    return Response(response_serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_enter_learning_view(request):
    """POST /api/training/enter-learning/"""
    serializer = CardActionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        response_data = enter_learning_mode(
            user=request.user,
            card_id=serializer.validated_data['card_id'],
            request=request,
        )
    except Card.DoesNotExist:
        return Response(
            {'error': 'Карточка не найдена или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = CardActionResponseSerializer(response_data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_exit_learning_view(request):
    """POST /api/training/exit-learning/"""
    serializer = CardActionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        response_data = exit_learning_mode(
            user=request.user,
            card_id=serializer.validated_data['card_id'],
            request=request,
        )
    except Card.DoesNotExist:
        return Response(
            {'error': 'Карточка не найдена или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = CardActionResponseSerializer(response_data)
    return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════
# Stats & Dashboard Views
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_stats_view(request):
    """GET /api/training/stats/"""
    period = request.query_params.get('period', 'all')
    response_data = get_training_stats(request.user, period)
    serializer = TrainingStatsSerializer(response_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_dashboard_view(request):
    """GET /api/training/dashboard/"""
    return Response(get_dashboard_data(request.user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_deck_activate_view(request, deck_id):
    """POST /api/training/deck/<id>/activate/"""
    try:
        return Response(activate_deck(request.user, deck_id))
    except Deck.DoesNotExist:
        return Response(
            {'error': 'Колода не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_deck_deactivate_view(request, deck_id):
    """POST /api/training/deck/<id>/deactivate/"""
    try:
        return Response(deactivate_deck(request.user, deck_id))
    except Deck.DoesNotExist:
        return Response(
            {'error': 'Колода не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_category_activate_view(request, category_id):
    """POST /api/training/category/<id>/activate/"""
    try:
        return Response(activate_category(request.user, category_id))
    except Category.DoesNotExist:
        return Response(
            {'error': 'Категория не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_category_deactivate_view(request, category_id):
    """POST /api/training/category/<id>/deactivate/"""
    try:
        return Response(deactivate_category(request.user, category_id))
    except Category.DoesNotExist:
        return Response(
            {'error': 'Категория не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


# ═══════════════════════════════════════════════════════════════
# AI Generation Views
# ═══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_etymology_view(request):
    """POST /api/training/generate-etymology/"""
    serializer = GenerateEtymologyRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        response_data = generate_etymology_for_word(
            user=request.user,
            word_id=serializer.validated_data['word_id'],
            force_regenerate=serializer.validated_data.get('force_regenerate', False),
        )
        serializer = GenerateEtymologyResponseSerializer(response_data)
        return Response(serializer.data)
    except Word.DoesNotExist:
        return Response(
            {'error': 'Слово не найдено или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Ошибка при генерации этимологии: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_hint_view(request):
    """POST /api/training/generate-hint/"""
    serializer = GenerateHintRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        response_data = generate_hint_for_word(
            user=request.user,
            word_id=serializer.validated_data['word_id'],
            force_regenerate=serializer.validated_data.get('force_regenerate', False),
            generate_audio=serializer.validated_data.get('generate_audio', True),
        )
        serializer = GenerateHintResponseSerializer(response_data)
        return Response(serializer.data)
    except Word.DoesNotExist:
        return Response(
            {'error': 'Слово не найдено или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Ошибка при генерации подсказки: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_sentence_view(request):
    """POST /api/training/generate-sentence/"""
    serializer = GenerateSentenceRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        response_data = generate_sentences_for_word(
            user=request.user,
            word_id=serializer.validated_data['word_id'],
            count=serializer.validated_data.get('count', 1),
            context=serializer.validated_data.get('context'),
        )
        serializer = GenerateSentenceResponseSerializer(response_data)
        return Response(serializer.data)
    except Word.DoesNotExist:
        return Response(
            {'error': 'Слово не найдено или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Ошибка при генерации предложений: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_synonym_view(request):
    """POST /api/training/generate-synonym/"""
    serializer = GenerateSynonymRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        response_data = generate_synonym_for_word(
            user=request.user,
            word_id=serializer.validated_data['word_id'],
            create_card=serializer.validated_data.get('create_card', True),
        )
        serializer = GenerateSynonymResponseSerializer(response_data)
        return Response(serializer.data)
    except Word.DoesNotExist:
        return Response(
            {'error': 'Слово не найдено или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Ошибка при генерации синонима: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ═══════════════════════════════════════════════════════════════
# Notification Views
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def notification_settings_view(request):
    """GET/PUT/PATCH /api/training/notifications/settings/"""
    settings_obj, _ = NotificationSettings.objects.get_or_create(
        user=request.user,
        defaults={
            'notification_frequency': 'normal',
            'browser_notifications_enabled': True,
        }
    )

    if request.method == 'GET':
        serializer = NotificationSettingsSerializer(settings_obj)
        return Response(serializer.data)

    serializer = NotificationSettingsSerializer(
        settings_obj, data=request.data, partial=(request.method == 'PATCH')
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_check_view(request):
    """GET /api/training/notifications/check/"""
    return Response(check_notification(request.user))


# ═══════════════════════════════════════════════════════════════
# Forgetting Curve View
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forgetting_curve_view(request):
    """GET /api/training/forgetting-curve/"""
    return Response(get_forgetting_curve_data(request.user))
