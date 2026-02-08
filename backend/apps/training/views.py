import uuid
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
from .session_utils import build_card_queue
from .sm2 import SM2Algorithm
from apps.cards.models import Card, Deck
from apps.cards.serializers import CardListSerializer
from apps.cards.token_utils import check_balance
from apps.words.models import Word, Category
from apps.words.serializers import WordSerializer
from .ai_generation import (
    generate_etymology,
    generate_hint,
    generate_sentence,
    generate_synonym_word
)

DEFAULT_AGE_GROUP = 'adult'

import logging
logger = logging.getLogger(__name__)


def _resolve_word_fields(word, user):
    """
    Для инвертированных слов возвращает скорректированные поля.
    
    При legacy-инвертировании original_word и translation меняются местами,
    а language становится родным языком. Эта функция восстанавливает
    правильные значения для AI-генерации.
    
    Returns:
        tuple: (target_word, target_translation, target_language)
    """
    if word.card_type == 'inverted':
        target_word = word.translation         # Изучаемое слово (было original_word до инверсии)
        target_translation = word.original_word  # Перевод на родной язык
        target_language = getattr(user, 'learning_language', word.language)
        logger.info(
            f"Инвертированное слово: используем '{target_word}' ({target_language}) "
            f"вместо '{word.original_word}' ({word.language})"
        )
        return target_word, target_translation, target_language
    return word.original_word, word.translation, word.language


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def training_settings_view(request):
    """
    GET /api/training/settings/ — Получить настройки тренировки
    PATCH /api/training/settings/ — Обновить настройки тренировки
    """
    settings, created = UserTrainingSettings.objects.get_or_create(
        user=request.user,
        defaults={'age_group': DEFAULT_AGE_GROUP}
    )
    
    if request.method == 'GET':
        serializer = UserTrainingSettingsSerializer(settings)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = UserTrainingSettingsUpdateSerializer(
            settings,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            # Возвращаем полное представление
            full_serializer = UserTrainingSettingsSerializer(settings)
            return Response(full_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_settings_reset_view(request):
    """
    POST /api/training/settings/reset/ — Сбросить настройки к значениям по умолчанию
    """
    settings = get_object_or_404(UserTrainingSettings, user=request.user)
    settings.reset_to_defaults()
    
    serializer = UserTrainingSettingsSerializer(settings)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_settings_defaults_view(request):
    """
    GET /api/training/settings/defaults/?age_group=adult — Получить значения по умолчанию
    """
    age_group = request.query_params.get('age_group', 'adult')
    
    serializer = UserTrainingSettingsDefaultsSerializer(data={'age_group': age_group})
    if serializer.is_valid():
        return Response(serializer.to_representation(None))
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════
# ЭТАП 6: Training API Views
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_session_view(request):
    """
    GET /api/training/session/
    Получить карточки для тренировочной сессии
    
    Query params:
    - deck_id: int (опционально)
    - category_id: int (опционально)
    - duration: int (минуты, по умолчанию из settings)
    - new_cards: bool (включать новые, по умолчанию true)
    """
    # Получаем параметры
    deck_id = request.query_params.get('deck_id')
    category_id = request.query_params.get('category_id')
    duration = request.query_params.get('duration')
    new_cards = request.query_params.get('new_cards', 'true').lower() == 'true'
    
    # Валидация deck_id
    if deck_id is not None:
        try:
            deck_id = int(deck_id)
        except (ValueError, TypeError):
            return Response(
                {'error': 'deck_id должен быть целым числом'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Валидация category_id
    if category_id is not None:
        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            return Response(
                {'error': 'category_id должен быть целым числом'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Нельзя указывать оба фильтра одновременно
    if deck_id is not None and category_id is not None:
        return Response(
            {'error': 'Нельзя указывать deck_id и category_id одновременно'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Валидация duration
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
    
    # Получаем настройки пользователя
    settings, _ = UserTrainingSettings.objects.get_or_create(
        user=request.user,
        defaults={'age_group': DEFAULT_AGE_GROUP}
    )
    
    # Используем duration из настроек, если не указан
    if duration is None:
        duration = settings.default_session_duration
    
    # Формируем очередь карточек
    queue_result = build_card_queue(
        user=request.user,
        deck_id=deck_id,
        category_id=category_id,
        duration_minutes=duration,
        include_new_cards=new_cards,
        settings=settings
    )
    
    # Генерируем session_id
    session_id = uuid.uuid4()
    
    # Сериализуем карточки (с request для абсолютных URL медиа-файлов)
    cards_data = CardListSerializer(queue_result['cards'], many=True, context={'request': request}).data
    
    # Формируем ответ
    response_data = {
        'session_id': session_id,
        'cards': cards_data,
        'estimated_time': queue_result['estimated_time'],
        'new_count': queue_result['new_count'],
        'review_count': queue_result['review_count'],
        'learning_count': queue_result['learning_count'],
        'total_count': queue_result['total_count']
    }
    
    serializer = TrainingSessionSerializer(response_data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_answer_view(request):
    """
    POST /api/training/answer/
    Обработать ответ пользователя на карточку
    
    Body:
    {
        "session_id": "uuid" (опционально),
        "card_id": 123,
        "answer": 2,  # 0=Again, 1=Hard, 2=Good, 3=Easy
        "time_spent": 5.2  # Секунды (опционально)
    }
    """
    serializer = TrainingAnswerRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    card_id = serializer.validated_data['card_id']
    answer = serializer.validated_data['answer']
    time_spent = serializer.validated_data.get('time_spent')
    
    # Получаем карточку
    try:
        card = Card.objects.select_related('word').get(id=card_id, user=request.user)
    except Card.DoesNotExist:
        return Response(
            {'error': 'Карточка не найдена или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Получаем настройки
    settings, _ = UserTrainingSettings.objects.get_or_create(
        user=request.user,
        defaults={'age_group': DEFAULT_AGE_GROUP}
    )
    
    # Сохраняем состояние до обработки
    was_in_learning_before = card.is_in_learning_mode
    was_calibrated_before = settings.last_calibration_at is not None
    
    # Обрабатываем ответ через SM2Algorithm
    result = SM2Algorithm.process_answer(
        card=card,
        answer=answer,
        settings=settings,
        time_spent=time_spent
    )
    
    # Обновляем карточку и настройки (уже сохранены в process_answer)
    card.refresh_from_db()
    settings.refresh_from_db()
    
    # Определяем изменения
    is_in_learning_after = card.is_in_learning_mode
    exited_learning_mode = was_in_learning_before and not is_in_learning_after
    
    was_calibrated_after = settings.last_calibration_at is not None
    calibrated = was_calibrated_after and not was_calibrated_before
    
    # Сериализуем карточку (с request для абсолютных URL медиа-файлов)
    card_data = CardListSerializer(card, context={'request': request}).data
    
    # Формируем ответ
    response_data = {
        'card_id': card.id,
        'new_interval': result['new_interval'],
        'new_ease_factor': result['new_ease_factor'],
        'next_review': result['next_review'],
        'entered_learning_mode': result['entered_learning_mode'],
        'exited_learning_mode': exited_learning_mode,
        'learning_step': result['learning_step'],
        'calibrated': calibrated,
        'card': card_data
    }
    
    response_serializer = TrainingAnswerResponseSerializer(response_data)
    return Response(response_serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_enter_learning_view(request):
    """
    POST /api/training/enter-learning/
    Перевести карточку в режим изучения вручную
    
    Body: {"card_id": 123}
    """
    serializer = CardActionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    card_id = serializer.validated_data['card_id']
    
    # Получаем карточку
    try:
        card = Card.objects.select_related('word').get(id=card_id, user=request.user)
    except Card.DoesNotExist:
        return Response(
            {'error': 'Карточка не найдена или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Переводим в режим изучения
    card.enter_learning_mode()
    card.save()
    
    # Сериализуем карточку (с request для абсолютных URL медиа-файлов)
    card_data = CardListSerializer(card, context={'request': request}).data
    
    response_data = {
        'card_id': card.id,
        'message': 'Карточка переведена в режим изучения',
        'card': card_data
    }
    
    serializer = CardActionResponseSerializer(response_data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_exit_learning_view(request):
    """
    POST /api/training/exit-learning/
    Вывести карточку из режима изучения вручную
    
    Body: {"card_id": 123}
    """
    serializer = CardActionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    card_id = serializer.validated_data['card_id']
    
    # Получаем карточку
    try:
        card = Card.objects.select_related('word').get(id=card_id, user=request.user)
    except Card.DoesNotExist:
        return Response(
            {'error': 'Карточка не найдена или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Выводим из режима изучения
    card.exit_learning_mode()
    card.save()
    
    # Сериализуем карточку (с request для абсолютных URL медиа-файлов)
    card_data = CardListSerializer(card, context={'request': request}).data
    
    response_data = {
        'card_id': card.id,
        'message': 'Карточка выведена из режима изучения',
        'card': card_data
    }
    
    serializer = CardActionResponseSerializer(response_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_stats_view(request):
    """
    GET /api/training/stats/
    Получить статистику тренировок
    
    Query params:
    - period: "day" | "week" | "month" | "all" (по умолчанию "all")
    """
    from django.utils import timezone
    from datetime import timedelta
    from collections import defaultdict
    
    period = request.query_params.get('period', 'all')
    
    # Определяем период
    now = timezone.now()
    if period == 'day':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    else:  # 'all'
        start_date = None
    
    # Получаем настройки для статистики
    settings, _ = UserTrainingSettings.objects.get_or_create(
        user=request.user,
        defaults={'age_group': DEFAULT_AGE_GROUP}
    )
    
    # Подсчитываем общую статистику
    total_reviews = settings.total_reviews
    successful_reviews = settings.successful_reviews
    success_rate = (successful_reviews / total_reviews) if total_reviews > 0 else 0.0
    
    # Получаем все карточки пользователя
    cards = Card.objects.for_user(request.user)
    
    # Фильтруем по периоду, если нужно
    if start_date:
        # Для периода используем last_review карточек
        cards_in_period = cards.filter(last_review__gte=start_date)
    else:
        cards_in_period = cards
    
    # Подсчитываем статистику по дням
    reviews_by_day_dict = defaultdict(lambda: {'total': 0, 'successful': 0})
    
    for card in cards_in_period:
        if card.last_review:
            day = card.last_review.date()
            reviews_by_day_dict[day]['total'] += 1
            # Считаем успешным, если repetitions > 0 или ease_factor >= starting_ease
            if card.repetitions > 0 or card.ease_factor >= settings.starting_ease:
                reviews_by_day_dict[day]['successful'] += 1
    
    # Преобразуем в список и сортируем
    reviews_by_day = []
    for date, stats in sorted(reviews_by_day_dict.items()):
        success_rate_day = (stats['successful'] / stats['total']) if stats['total'] > 0 else 0.0
        reviews_by_day.append({
            'date': date,
            'total': stats['total'],
            'successful': stats['successful'],
            'success_rate': round(success_rate_day, 2)
        })
    
    # Подсчитываем streak (дни подряд с тренировками)
    streak_days = calculate_streak_days(request.user)
    
    # Распределение карточек по статусам
    cards_by_status = get_cards_by_status(request.user)
    
    # Среднее время на карточку и общее время
    # total_time_spent хранится в settings, но может отсутствовать в старых версиях
    total_time_spent = getattr(settings, 'total_time_spent', 0)  # в секундах
    average_time_per_card = (
        total_time_spent / total_reviews
        if total_reviews > 0 else 0.0
    )
    
    # Формируем ответ
    response_data = {
        'period': period,
        'total_reviews': total_reviews,
        'successful_reviews': successful_reviews,
        'success_rate': round(success_rate, 2),
        'streak_days': streak_days,
        'cards_by_status': cards_by_status,
        'reviews_by_day': reviews_by_day,
        'average_time_per_card': round(average_time_per_card, 2),
        'total_time_spent': total_time_spent
    }
    
    serializer = TrainingStatsSerializer(response_data)
    return Response(serializer.data)


def calculate_streak_days(user):
    """
    Подсчитывает количество дней подряд с тренировками.
    
    Returns:
        int: Количество дней streak
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Получаем все карточки с last_review
    cards = Card.objects.for_user(user).filter(
        last_review__isnull=False
    ).exclude(last_review__lt=timezone.now() - timedelta(days=365))  # Только за последний год
    
    if not cards.exists():
        return 0
    
    # Получаем уникальные даты тренировок
    training_dates = set()
    for card in cards:
        if card.last_review:
            training_dates.add(card.last_review.date())
    
    if not training_dates:
        return 0
    
    # Сортируем даты по убыванию
    sorted_dates = sorted(training_dates, reverse=True)
    
    # Подсчитываем streak
    streak = 0
    current_date = timezone.now().date()
    
    for date in sorted_dates:
        # Проверяем, является ли дата следующим днем в streak
        if date == current_date or date == current_date - timedelta(days=streak):
            streak += 1
            current_date = date
        else:
            break
    
    return streak


def get_cards_by_status(user):
    """
    Возвращает распределение карточек по статусам.
    
    Returns:
        dict: {'new': int, 'learning': int, 'review': int, 'mastered': int}
    """
    from django.utils import timezone
    
    cards = Card.objects.for_user(user)
    now = timezone.now()
    
    # Новые карточки: is_in_learning_mode=True, repetitions=0, interval=0
    new_count = cards.filter(
        is_in_learning_mode=True,
        repetitions=0,
        interval=0
    ).count()
    
    # Карточки в режиме обучения: is_in_learning_mode=True, но не new
    learning_count = cards.filter(
        is_in_learning_mode=True
    ).exclude(
        repetitions=0,
        interval=0
    ).count()
    
    # Карточки на повторение: is_in_learning_mode=False, next_review <= now
    review_count = cards.filter(
        is_in_learning_mode=False,
        next_review__lte=now
    ).count()
    
    # Освоенные карточки: is_in_learning_mode=False, next_review > now, interval >= 30
    mastered_count = cards.filter(
        is_in_learning_mode=False,
        next_review__gt=now,
        interval__gte=30
    ).count()
    
    return {
        'new': new_count,
        'learning': learning_count,
        'review': review_count,
        'mastered': mastered_count
    }


# ═══════════════════════════════════════════════════════════════
# ДАШБОРД ТРЕНИРОВОК И АКТИВАЦИЯ
# ═══════════════════════════════════════════════════════════════


def _get_card_counts_for_queryset(cards_qs):
    """
    Подсчитывает карточки по статусам для произвольного queryset.
    
    Returns:
        dict: {'new': int, 'learning': int, 'review': int, 'mastered': int, 'total': int, 'due': int}
    """
    from django.utils import timezone
    now = timezone.now()
    
    total = cards_qs.count()
    
    new_count = cards_qs.filter(
        is_in_learning_mode=True,
        repetitions=0,
        interval=0
    ).count()
    
    learning_count = cards_qs.filter(
        is_in_learning_mode=True
    ).exclude(
        repetitions=0,
        interval=0
    ).count()
    
    review_count = cards_qs.filter(
        is_in_learning_mode=False,
        next_review__lte=now
    ).count()
    
    mastered_count = cards_qs.filter(
        is_in_learning_mode=False,
        next_review__gt=now,
        interval__gte=30
    ).count()
    
    due_count = new_count + learning_count + review_count
    
    return {
        'new': new_count,
        'learning': learning_count,
        'review': review_count,
        'mastered': mastered_count,
        'total': total,
        'due': due_count,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_dashboard_view(request):
    """
    GET /api/training/dashboard/
    Дашборд тренировок: колоды и категории с подсчётом карточек.
    """
    from django.db.models import Q
    
    user = request.user
    
    # Настройки тренировки
    training_settings, _ = UserTrainingSettings.objects.get_or_create(
        user=user,
        defaults={'age_group': DEFAULT_AGE_GROUP}
    )
    
    # Быстрая статистика
    streak_days = calculate_streak_days(user)
    total_reviews = training_settings.total_reviews
    successful_reviews = training_settings.successful_reviews
    success_rate = (successful_reviews / total_reviews) if total_reviews > 0 else 0.0
    
    all_user_cards = Card.objects.for_user(user)
    
    # Подсчёт общего числа карточек к повторению
    total_due = _get_card_counts_for_queryset(all_user_cards)['due']
    
    # --- Колоды ---
    decks_data = []
    for deck in Deck.objects.filter(user=user).order_by('-updated_at'):
        deck_cards = all_user_cards.filter(word__decks=deck)
        cards_info = _get_card_counts_for_queryset(deck_cards)
        decks_data.append({
            'id': deck.id,
            'name': deck.name,
            'cover': deck.cover.url if deck.cover else None,
            'is_learning_active': deck.is_learning_active,
            'cards': cards_info,
        })
    
    # --- Категории (только корневые + плоский список) ---
    categories_data = []
    for cat in Category.objects.filter(user=user).order_by('order', 'name'):
        cat_cards = all_user_cards.filter(word__categories=cat)
        cards_info = _get_card_counts_for_queryset(cat_cards)
        categories_data.append({
            'id': cat.id,
            'name': cat.name,
            'icon': cat.icon,
            'parent_id': cat.parent_id,
            'is_learning_active': cat.is_learning_active,
            'cards': cards_info,
        })
    
    # --- Сироты (слова без колоды) ---
    orphan_cards = all_user_cards.filter(word__decks__isnull=True)
    orphans_info = _get_card_counts_for_queryset(orphan_cards)
    
    return Response({
        'quick_stats': {
            'streak_days': streak_days,
            'success_rate': round(success_rate, 2),
            'total_due': total_due,
        },
        'decks': decks_data,
        'categories': categories_data,
        'orphans': {
            'is_active': training_settings.include_orphan_words,
            'cards': orphans_info,
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_deck_activate_view(request, deck_id):
    """
    POST /api/training/deck/<id>/activate/
    Активировать колоду для тренировки.
    """
    try:
        deck = Deck.objects.get(id=deck_id, user=request.user)
    except Deck.DoesNotExist:
        return Response(
            {'error': 'Колода не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    deck.is_learning_active = True
    deck.save(update_fields=['is_learning_active', 'updated_at'])
    
    return Response({'id': deck.id, 'is_learning_active': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_deck_deactivate_view(request, deck_id):
    """
    POST /api/training/deck/<id>/deactivate/
    Деактивировать колоду.
    """
    try:
        deck = Deck.objects.get(id=deck_id, user=request.user)
    except Deck.DoesNotExist:
        return Response(
            {'error': 'Колода не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    deck.is_learning_active = False
    deck.save(update_fields=['is_learning_active', 'updated_at'])
    
    return Response({'id': deck.id, 'is_learning_active': False})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_category_activate_view(request, category_id):
    """
    POST /api/training/category/<id>/activate/
    Активировать категорию для тренировки.
    """
    try:
        category = Category.objects.get(id=category_id, user=request.user)
    except Category.DoesNotExist:
        return Response(
            {'error': 'Категория не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    category.is_learning_active = True
    category.save(update_fields=['is_learning_active'])
    
    return Response({'id': category.id, 'is_learning_active': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def training_category_deactivate_view(request, category_id):
    """
    POST /api/training/category/<id>/deactivate/
    Деактивировать категорию.
    """
    try:
        category = Category.objects.get(id=category_id, user=request.user)
    except Category.DoesNotExist:
        return Response(
            {'error': 'Категория не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    category.is_learning_active = False
    category.save(update_fields=['is_learning_active'])
    
    return Response({'id': category.id, 'is_learning_active': False})


# ═══════════════════════════════════════════════════════════════
# ЭТАП 7: AI Generation API Views
# ═══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_etymology_view(request):
    """
    POST /api/training/generate-etymology/
    Генерация этимологии для слова
    
    Body:
    {
        "word_id": 123,
        "force_regenerate": false
    }
    """
    serializer = GenerateEtymologyRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word_id = serializer.validated_data['word_id']
    force_regenerate = serializer.validated_data.get('force_regenerate', False)
    
    # Получаем слово
    try:
        word = Word.objects.get(id=word_id, user=request.user)
    except Word.DoesNotExist:
        return Response(
            {'error': 'Слово не найдено или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Проверяем, нужна ли генерация
    if word.etymology and not force_regenerate:
        return Response(
            {'error': 'Этимология уже существует. Используйте force_regenerate=true для перегенерации'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Для инвертированных слов используем правильные поля
        target_word, target_translation, target_language = _resolve_word_fields(word, request.user)
        
        # Генерируем этимологию
        etymology = generate_etymology(
            word=target_word,
            translation=target_translation,
            language=target_language,
            user=request.user,
            force_regenerate=force_regenerate
        )
        
        # Обновляем слово
        word.etymology = etymology
        word.save(update_fields=['etymology'])
        
        # Получаем баланс после списания
        balance = check_balance(request.user)
        balance_display = balance
        
        response_data = {
            'word_id': word.id,
            'etymology': etymology,
            'tokens_spent': 1,
            'balance_after': balance_display
        }
        
        serializer = GenerateEtymologyResponseSerializer(response_data)
        return Response(serializer.data)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Ошибка при генерации этимологии: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_hint_view(request):
    """
    POST /api/training/generate-hint/
    Генерация подсказки (текст + аудио) для слова
    
    Body:
    {
        "word_id": 123,
        "force_regenerate": false,
        "generate_audio": true
    }
    """
    serializer = GenerateHintRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word_id = serializer.validated_data['word_id']
    force_regenerate = serializer.validated_data.get('force_regenerate', False)
    generate_audio = serializer.validated_data.get('generate_audio', True)
    
    # Получаем слово
    try:
        word = Word.objects.get(id=word_id, user=request.user)
    except Word.DoesNotExist:
        return Response(
            {'error': 'Слово не найдено или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Проверяем, нужна ли генерация
    if word.hint_text and not force_regenerate:
        # Возвращаем существующую подсказку
        hint_audio_url = word.hint_audio.url if word.hint_audio else None
        
        response_data = {
            'word_id': word.id,
            'hint_text': word.hint_text,
            'hint_audio_url': hint_audio_url,
            'tokens_spent': 0,
            'balance_after': check_balance(request.user)
        }
        
        serializer = GenerateHintResponseSerializer(response_data)
        return Response(serializer.data)
    
    try:
        # Для инвертированных слов используем правильные поля
        target_word, target_translation, target_language = _resolve_word_fields(word, request.user)
        
        # Генерируем подсказку
        hint_text, hint_audio_path = generate_hint(
            word=target_word,
            translation=target_translation,
            language=target_language,
            user=request.user,
            generate_audio=generate_audio,
            force_regenerate=force_regenerate
        )
        
        # Обновляем слово
        word.hint_text = hint_text
        
        # Сохраняем путь к аудио файлу
        if hint_audio_path:
            # Преобразуем абсолютный путь в относительный для сохранения в БД
            from pathlib import Path
            from django.conf import settings
            
            if Path(hint_audio_path).is_absolute():
                # Вычисляем относительный путь от MEDIA_ROOT
                media_root = Path(settings.MEDIA_ROOT)
                try:
                    relative_path = Path(hint_audio_path).relative_to(media_root)
                    word.hint_audio = str(relative_path)
                except ValueError:
                    # Если не удалось вычислить относительный путь, сохраняем как есть
                    word.hint_audio = hint_audio_path
            else:
                word.hint_audio = hint_audio_path
        
        word.save(update_fields=['hint_text', 'hint_audio'])
        
        # Получаем баланс после списания
        balance = check_balance(request.user)
        balance_display = balance
        
        # Формируем URL для аудио
        hint_audio_url = word.hint_audio.url if word.hint_audio else None
        
        # Стоимость: 1 токен за текст + 1 токен за аудио (если генерировалось)
        tokens_spent = 2 if generate_audio and hint_audio_path else 1
        
        response_data = {
            'word_id': word.id,
            'hint_text': hint_text,
            'hint_audio_url': hint_audio_url,
            'tokens_spent': tokens_spent,
            'balance_after': balance_display
        }
        
        serializer = GenerateHintResponseSerializer(response_data)
        return Response(serializer.data)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Ошибка при генерации подсказки: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_sentence_view(request):
    """
    POST /api/training/generate-sentence/
    Генерация примеров предложений для слова
    
    Body:
    {
        "word_id": 123,
        "count": 3,
        "context": "формальное общение"
    }
    """
    serializer = GenerateSentenceRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word_id = serializer.validated_data['word_id']
    count = serializer.validated_data.get('count', 1)
    context = serializer.validated_data.get('context')
    
    # Получаем слово
    try:
        word = Word.objects.get(id=word_id, user=request.user)
    except Word.DoesNotExist:
        return Response(
            {'error': 'Слово не найдено или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Для инвертированных слов используем правильные поля
        target_word, target_translation, target_language = _resolve_word_fields(word, request.user)
        
        # Генерируем предложения
        sentences_result = generate_sentence(
            word=target_word,
            translation=target_translation,
            language=target_language,
            user=request.user,
            context=context,
            count=count
        )
        
        # Преобразуем в список, если это одно предложение
        if isinstance(sentences_result, str):
            sentences_list = [sentences_result]
        else:
            sentences_list = sentences_result
        
        # Добавляем предложения в word.sentences
        for sentence_text in sentences_list:
            word.add_sentence(sentence_text, source='ai')
        
        # Получаем баланс после списания
        balance = check_balance(request.user)
        balance_display = balance
        
        response_data = {
            'word_id': word.id,
            'sentences': sentences_list,
            'tokens_spent': 1,
            'balance_after': balance_display
        }
        
        serializer = GenerateSentenceResponseSerializer(response_data)
        return Response(serializer.data)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Ошибка при генерации предложений: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_synonym_view(request):
    """
    POST /api/training/generate-synonym/
    Генерация синонима для слова
    
    Body:
    {
        "word_id": 123,
        "create_card": true
    }
    """
    serializer = GenerateSynonymRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word_id = serializer.validated_data['word_id']
    create_card = serializer.validated_data.get('create_card', True)
    
    # Получаем слово
    try:
        word = Word.objects.get(id=word_id, user=request.user)
    except Word.DoesNotExist:
        return Response(
            {'error': 'Слово не найдено или не принадлежит пользователю'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Генерируем синоним
        synonym_word = generate_synonym_word(
            word=word,
            user=request.user,
            create_card=create_card
        )
        
        # Сериализуем новое слово
        synonym_data = WordSerializer(synonym_word).data
        
        # Получаем баланс после списания
        balance = check_balance(request.user)
        balance_display = balance
        
        # Стоимость: 1 токен за синоним + 1 токен за этимологию (автоматически)
        tokens_spent = 2
        
        response_data = {
            'original_word_id': word.id,
            'synonym_word': synonym_data,
            'relation_created': True,
            'tokens_spent': tokens_spent,
            'balance_after': balance_display
        }
        
        serializer = GenerateSynonymResponseSerializer(response_data)
        return Response(serializer.data)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Ошибка при генерации синонима: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ═══════════════════════════════════════════════════════════════
# Этап 13: Уведомления
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def notification_settings_view(request):
    """
    GET  — получить настройки уведомлений
    PUT/PATCH — обновить настройки
    """
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
        settings_obj,
        data=request.data,
        partial=(request.method == 'PATCH')
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_check_view(request):
    """
    GET — проверить, нужно ли показать уведомление.
    Вызывается фронтендом периодически.
    Возвращает: should_notify, cards_due, streak_at_risk, message, notification_type
    """
    from django.utils import timezone
    from datetime import timedelta

    settings_obj, _ = NotificationSettings.objects.get_or_create(
        user=request.user,
        defaults={'notification_frequency': 'normal'}
    )

    # Карточки для повторения
    now = timezone.now()
    cards_due = Card.objects.filter(
        user=request.user,
        next_review__lte=now,
    ).count()

    # Стрик в опасности: сегодня не было ни одного ответа
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_reviews = Card.objects.filter(
        user=request.user,
        last_review__gte=today_start,
    ).count()
    streak_at_risk = today_reviews == 0

    # Определяем, нужно ли уведомление
    should_notify = False
    message = ''
    notification_type = 'none'

    if not settings_obj.should_notify():
        return Response({
            'should_notify': False,
            'cards_due': cards_due,
            'streak_at_risk': streak_at_risk,
            'message': '',
            'notification_type': 'none',
        })

    if settings_obj.notify_cards_due and cards_due >= settings_obj.cards_due_threshold:
        should_notify = True
        message = f'У вас {cards_due} карточек для повторения!'
        notification_type = 'cards_due'
    elif settings_obj.notify_streak_warning and streak_at_risk and now.hour >= 18:
        should_notify = True
        message = 'Ваш стрик в опасности! Не забудьте позаниматься сегодня.'
        notification_type = 'streak_warning'

    if should_notify:
        settings_obj.last_notified_at = now
        settings_obj.save(update_fields=['last_notified_at'])

    return Response({
        'should_notify': should_notify,
        'cards_due': cards_due,
        'streak_at_risk': streak_at_risk,
        'message': message,
        'notification_type': notification_type,
    })


# ═══════════════════════════════════════════════════════════════
# Этап 14: Кривые забывания
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forgetting_curve_view(request):
    """
    GET — данные для построения кривой забывания пользователя.

    Агрегирует карточки по интервалам и вычисляет retention rate
    на каждом интервале, чтобы построить индивидуальную кривую.

    Возвращает:
        points: [{interval_days, retention_rate, total_cards, successful}]
        theoretical_curve: [{day, retention}]  — эталонная экспонента
        summary: {total_reviews, avg_retention, current_stability}
    """
    import math
    from django.db.models import Avg, Count, Q

    user = request.user

    # Все карточки пользователя, которые хотя бы раз были повторены
    reviewed_cards = Card.objects.filter(
        user=user,
        repetitions__gt=0,
    )

    if not reviewed_cards.exists():
        return Response({
            'points': [],
            'theoretical_curve': [],
            'summary': {
                'total_reviews': 0,
                'avg_retention': 0,
                'current_stability': 0,
            }
        })

    # Группируем карточки по текущему интервалу (бакеты)
    # Бакеты: 1, 2-3, 4-7, 8-14, 15-30, 31-60, 61-90, 91+
    buckets = [
        (1, 1, '1'),
        (2, 3, '2-3'),
        (4, 7, '4-7'),
        (8, 14, '8-14'),
        (15, 30, '15-30'),
        (31, 60, '31-60'),
        (61, 90, '61-90'),
        (91, 365, '91+'),
    ]

    points = []
    for low, high, label in buckets:
        cards_in_bucket = reviewed_cards.filter(
            interval__gte=low,
            interval__lte=high,
        )
        total = cards_in_bucket.count()
        if total == 0:
            continue

        # "Успешные" = карточки, у которых ease_factor > min_ease и low lapses
        # Более точно: retention = 1 - (lapses / (repetitions + lapses))
        successful = cards_in_bucket.filter(
            consecutive_lapses=0
        ).count()
        retention = successful / total if total > 0 else 0

        mid_day = (low + high) / 2
        points.append({
            'interval_days': mid_day,
            'label': label,
            'retention_rate': round(retention * 100, 1),
            'total_cards': total,
            'successful': successful,
        })

    # Теоретическая кривая: R(t) = e^(-t/S)
    # S = средняя стабильность (средний интервал успешных карточек)
    avg_interval = reviewed_cards.filter(
        consecutive_lapses=0
    ).aggregate(avg=Avg('interval'))['avg'] or 30

    theoretical = []
    for day in [1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90, 120, 180, 365]:
        retention = math.exp(-day / max(avg_interval, 1)) * 100
        theoretical.append({
            'day': day,
            'retention': round(retention, 1),
        })

    # Summary
    total_reviews = reviewed_cards.aggregate(
        total=Count('id')
    )['total'] or 0
    avg_retention = reviewed_cards.aggregate(
        avg_ef=Avg('ease_factor')
    )['avg_ef'] or 2.5

    return Response({
        'points': points,
        'theoretical_curve': theoretical,
        'summary': {
            'total_reviews': total_reviews,
            'avg_retention': round((avg_retention - 1.3) / (4.0 - 1.3) * 100, 1),
            'current_stability': round(avg_interval, 1),
        },
    })
