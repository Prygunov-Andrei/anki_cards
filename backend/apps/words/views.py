from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Min, Count, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Word, WordRelation, Category
from .serializers import (
    WordSerializer,
    WordListSerializer,
    WordUpdateSerializer,
    WordRelationSerializer,
    WordRelationCreateSerializer,
    WordWithRelationsSerializer,
    CategorySerializer,
    CategoryCreateSerializer,
    CategoryUpdateSerializer,
    CategoryTreeSerializer,
    CategoryListSerializer,
    WordStatsSerializer,
    WordsStatsSerializer,
    BulkActionRequestSerializer,
    BulkActionResponseSerializer,
)
from apps.cards.models import Card
from apps.cards.serializers import (
    CardSerializer,
    CardListSerializer,
    CardCreateClozeSerializer,
)
from .utils import (
    get_word_learning_status,
    update_word_learning_status,
    get_word_next_review,
    get_word_cards_stats
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def words_list_view(request):
    """
    GET /api/words/list/
    Получение списка всех слов пользователя с расширенной фильтрацией, сортировкой и пагинацией
    
    Query параметры:
    - language: фильтр по языку
    - learning_status: фильтр по статусу (new/learning/reviewing/mastered)
    - part_of_speech: фильтр по части речи
    - category_id: фильтр по категории
    - deck_id: фильтр по колоде
    - search: поиск по тексту
    - has_etymology: true/false - есть/нет этимология
    - has_hint: true/false - есть/нет подсказка
    - has_sentences: true/false - есть/нет предложения
    - ordering: сортировка (created_at, -created_at, original_word, -original_word, learning_status, next_review, -next_review)
    - page: номер страницы (по умолчанию 1)
    - page_size: размер страницы (по умолчанию 20, максимум 100)
    """
    words = Word.objects.filter(user=request.user)
    
    # Исключаем legacy-инвертированные Word-ы (артефакты old-style инвертирования)
    # Инвертирование теперь происходит на уровне Card, а не Word
    words = words.exclude(card_type='inverted')
    
    # Оптимизация запросов
    words = words.select_related('user').prefetch_related(
        'categories',
        'decks',
        Prefetch('cards', queryset=Card.objects.filter(user=request.user))
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ФИЛЬТРАЦИЯ
    # ═══════════════════════════════════════════════════════════════
    
    # Фильтрация по языку
    language = request.query_params.get('language', None)
    if language in ['ru', 'en', 'pt', 'de', 'es', 'fr', 'it']:
        words = words.filter(language=language)
    
    # Фильтрация по статусу обучения
    learning_status = request.query_params.get('learning_status', None)
    if learning_status in ['new', 'learning', 'reviewing', 'mastered']:
        words = words.filter(learning_status=learning_status)
    
    # Фильтрация по части речи
    part_of_speech = request.query_params.get('part_of_speech', None)
    if part_of_speech:
        words = words.filter(part_of_speech=part_of_speech)
    
    # Фильтрация по категории
    category_id = request.query_params.get('category_id', None)
    if category_id:
        try:
            category_id = int(category_id)
            words = words.filter(categories__id=category_id).distinct()
        except (ValueError, TypeError):
            pass
    
    # Фильтрация по колоде
    deck_id = request.query_params.get('deck_id', None)
    if deck_id:
        try:
            deck_id = int(deck_id)
            words = words.filter(decks__id=deck_id).distinct()
        except (ValueError, TypeError):
            pass
    
    # Поиск по словам и переводам
    search = request.query_params.get('search', None)
    if search:
        words = words.filter(
            Q(original_word__icontains=search) |
            Q(translation__icontains=search)
        )
    
    # Фильтрация по наличию контента
    has_etymology = request.query_params.get('has_etymology', None)
    if has_etymology is not None:
        has_etymology_bool = has_etymology.lower() == 'true'
        if has_etymology_bool:
            words = words.exclude(etymology='')
        else:
            words = words.filter(etymology='')
    
    has_hint = request.query_params.get('has_hint', None)
    if has_hint is not None:
        has_hint_bool = has_hint.lower() == 'true'
        if has_hint_bool:
            words = words.exclude(hint_text='')
        else:
            words = words.filter(hint_text='')
    
    has_sentences = request.query_params.get('has_sentences', None)
    if has_sentences is not None:
        has_sentences_bool = has_sentences.lower() == 'true'
        if has_sentences_bool:
            words = words.exclude(sentences=[])
        else:
            words = words.filter(sentences=[])
    
    # ═══════════════════════════════════════════════════════════════
    # АННОТАЦИИ ДЛЯ СОРТИРОВКИ
    # ═══════════════════════════════════════════════════════════════
    
    # Аннотация для next_review (ближайшая дата повторения среди всех карточек)
    words = words.annotate(
        next_review=Min('cards__next_review')
    )
    
    # ═══════════════════════════════════════════════════════════════
    # СОРТИРОВКА
    # ═══════════════════════════════════════════════════════════════
    
    ordering = request.query_params.get('ordering', '-created_at')
    
    # Валидация ordering
    valid_orderings = [
        'created_at', '-created_at',
        'original_word', '-original_word',
        'learning_status', '-learning_status',
        'next_review', '-next_review',
    ]
    
    if ordering in valid_orderings:
        words = words.order_by(ordering)
    else:
        # По умолчанию сортируем по дате создания (убывание)
        words = words.order_by('-created_at')
    
    # ═══════════════════════════════════════════════════════════════
    # ПАГИНАЦИЯ
    # ═══════════════════════════════════════════════════════════════
    
    # Получаем параметры пагинации
    try:
        page = int(request.query_params.get('page', 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    try:
        page_size = int(request.query_params.get('page_size', 20))
        if page_size < 1:
            page_size = 20
        elif page_size > 100:
            page_size = 100  # Максимум 100 элементов на странице
    except (ValueError, TypeError):
        page_size = 20
    
    # Применяем пагинацию
    paginator = Paginator(words, page_size)
    total_count = paginator.count
    
    try:
        page_obj = paginator.page(page)
        words_page = page_obj.object_list
    except Exception:
        # Если страница не существует, возвращаем пустой результат
        words_page = []
        page = 1
        total_count = 0
    
    # ═══════════════════════════════════════════════════════════════
    # СЕРИАЛИЗАЦИЯ И ОТВЕТ
    # ═══════════════════════════════════════════════════════════════
    
    serializer = WordListSerializer(words_page, many=True)
    
    # Формируем URL для следующей и предыдущей страницы
    next_url = None
    previous_url = None
    
    if page_obj.has_next():
        next_url = f"/api/words/list/?page={page_obj.next_page_number()}"
        # Сохраняем все query параметры
        query_params = request.query_params.copy()
        query_params['page'] = page_obj.next_page_number()
        next_url = f"/api/words/list/?{query_params.urlencode()}"
    
    if page_obj.has_previous():
        query_params = request.query_params.copy()
        query_params['page'] = page_obj.previous_page_number()
        previous_url = f"/api/words/list/?{query_params.urlencode()}"
    
    return Response({
        'count': total_count,
        'next': next_url,
        'previous': previous_url,
        'results': serializer.data
    }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════
# WORD RELATIONS API
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_relations_view(request, word_id):
    """Получение всех связей слова (синонимы + антонимы)"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    relations = WordRelation.objects.filter(word_from=word)
    serializer = WordRelationSerializer(relations, many=True)
    
    return Response({
        'word_id': word_id,
        'relations': serializer.data,
        'synonyms_count': relations.filter(relation_type='synonym').count(),
        'antonyms_count': relations.filter(relation_type='antonym').count(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def word_add_synonym_view(request, word_id):
    """Добавление синонима к слову"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    serializer = WordRelationCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    other_word_id = serializer.validated_data['word_id']
    
    # Проверяем, что не пытаемся связать слово с самим собой
    if other_word_id == word_id:
        return Response(
            {'error': 'Слово не может быть синонимом самого себя'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    other_word = get_object_or_404(Word, id=other_word_id, user=request.user)
    
    # Создаём двустороннюю связь
    relation1, relation2 = word.add_synonym(other_word)
    
    return Response({
        'message': 'Синоним добавлен',
        'relation': WordRelationSerializer(relation1).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def word_add_antonym_view(request, word_id):
    """Добавление антонима к слову"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    serializer = WordRelationCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    other_word_id = serializer.validated_data['word_id']
    
    # Проверяем, что не пытаемся связать слово с самим собой
    if other_word_id == word_id:
        return Response(
            {'error': 'Слово не может быть антонимом самого себя'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    other_word = get_object_or_404(Word, id=other_word_id, user=request.user)
    
    # Создаём двустороннюю связь
    relation1, relation2 = word.add_antonym(other_word)
    
    return Response({
        'message': 'Антоним добавлен',
        'relation': WordRelationSerializer(relation1).data
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def word_delete_relation_view(request, word_id, relation_id):
    """Удаление связи между словами"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    # Ищем связь
    relation = get_object_or_404(
        WordRelation,
        id=relation_id,
        word_from=word
    )
    
    # Получаем тип связи и другое слово для удаления обратной связи
    relation_type = relation.relation_type
    other_word = relation.word_to
    
    # Удаляем обе связи (двустороннюю)
    if relation_type == 'synonym':
        deleted_count = word.remove_synonym(other_word)
    else:
        deleted_count = word.remove_antonym(other_word)
    
    return Response({
        'message': 'Связь удалена',
        'deleted_count': deleted_count
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def word_detail_view(request, word_id):
    """
    GET /api/words/{word_id}/ — Получение детальной информации о слове
    PATCH /api/words/{word_id}/ — Обновление слова
    DELETE /api/words/{word_id}/ — Удаление слова
    """
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    if request.method == 'GET':
        serializer = WordWithRelationsSerializer(word)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = WordUpdateSerializer(
            word,
            data=request.data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        # Обновляем статус обучения на основе карточек
        update_word_learning_status(word)
        
        # Возвращаем обновлённое слово
        response_serializer = WordWithRelationsSerializer(word)
        return Response(response_serializer.data)
    
    elif request.method == 'DELETE':
        word_text = word.original_word
        word.delete()  # CASCADE удалит карточки, связи, категории
        
        return Response({
            'message': f'Слово "{word_text}" удалено'
        }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════
# CATEGORY API
# ═══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def categories_list_view(request):
    """
    GET: Получение дерева категорий пользователя
    POST: Создание новой категории
    """
    if request.method == 'GET':
        # Получаем только корневые категории (без parent)
        root_categories = Category.objects.filter(
            user=request.user,
            parent__isnull=True
        ).order_by('order', 'name')
        
        # Формат ответа зависит от параметра
        flat = request.query_params.get('flat', 'false').lower() == 'true'
        
        if flat:
            # Плоский список всех категорий
            all_categories = Category.objects.filter(
                user=request.user
            ).order_by('order', 'name')
            serializer = CategorySerializer(all_categories, many=True)
        else:
            # Дерево категорий
            serializer = CategoryTreeSerializer(root_categories, many=True)
        
        return Response({
            'count': Category.objects.filter(user=request.user).count(),
            'categories': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = CategoryCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        category = serializer.save(user=request.user)
        
        return Response({
            'message': 'Категория создана',
            'category': CategorySerializer(category).data
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def category_detail_view(request, category_id):
    """
    GET: Получение деталей категории
    PATCH: Обновление категории
    DELETE: Удаление категории (и всех потомков)
    """
    category = get_object_or_404(
        Category,
        id=category_id,
        user=request.user
    )
    
    if request.method == 'GET':
        serializer = CategoryTreeSerializer(category)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = CategoryUpdateSerializer(
            category,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        category = serializer.save()
        
        return Response({
            'message': 'Категория обновлена',
            'category': CategorySerializer(category).data
        })
    
    elif request.method == 'DELETE':
        # Считаем, сколько категорий будет удалено (включая потомков)
        descendants = category.get_descendants()
        total_deleted = 1 + len(descendants)
        
        category_name = category.name
        category.delete()  # CASCADE удалит всех потомков
        
        return Response({
            'message': f'Категория "{category_name}" удалена',
            'deleted_count': total_deleted
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_words_view(request, category_id):
    """Получение слов в категории"""
    category = get_object_or_404(
        Category,
        id=category_id,
        user=request.user
    )
    
    # Параметр: включать слова из подкатегорий?
    include_descendants = request.query_params.get(
        'include_descendants', 'false'
    ).lower() == 'true'
    
    if include_descendants:
        # Собираем слова из текущей категории и всех потомков
        category_ids = [category.id] + [d.id for d in category.get_descendants()]
        words = Word.objects.filter(
            user=request.user,
            categories__id__in=category_ids
        ).distinct()
    else:
        words = category.words.filter(user=request.user)
    
    serializer = WordListSerializer(words, many=True)
    
    return Response({
        'category_id': category_id,
        'category_name': category.name,
        'include_descendants': include_descendants,
        'count': words.count(),
        'words': serializer.data
    })


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def word_categories_view(request, word_id):
    """
    POST: Добавить слово в категорию
    DELETE: Удалить слово из категории
    
    Body: {"category_id": 123}
    """
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    category_id = request.data.get('category_id')
    if not category_id:
        return Response(
            {'error': 'category_id обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    category = get_object_or_404(
        Category,
        id=category_id,
        user=request.user
    )
    
    if request.method == 'POST':
        word.categories.add(category)
        return Response({
            'message': f'Слово добавлено в категорию "{category.name}"',
            'word_id': word.id,
            'category_id': category.id
        })
    
    elif request.method == 'DELETE':
        word.categories.remove(category)
        return Response({
            'message': f'Слово удалено из категории "{category.name}"',
            'word_id': word.id,
            'category_id': category.id
        })


# ═══════════════════════════════════════════════════════════════
# ЭТАП 3: Card views (через слова)
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_cards_list_view(request, word_id):
    """
    GET /api/words/{word_id}/cards/ — Все карточки слова
    """
    word = get_object_or_404(Word, id=word_id, user=request.user)
    cards = Card.objects.filter(word=word).select_related('word')
    serializer = CardListSerializer(cards, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_inverted_view(request, word_id):
    """
    POST /api/words/{word_id}/cards/inverted/ — Создать инвертированную карточку
    """
    word = get_object_or_404(Word.objects.select_related('user'), id=word_id, user=request.user)
    
    # Проверяем, нет ли уже инвертированной
    if Card.objects.filter(word=word, card_type='inverted').exists():
        return Response(
            {'error': 'Инвертированная карточка уже существует'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    card = Card.create_inverted(word)
    serializer = CardSerializer(card)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_empty_view(request, word_id):
    """
    POST /api/words/{word_id}/cards/empty/ — Создать пустую карточку
    """
    word = get_object_or_404(Word.objects.select_related('user'), id=word_id, user=request.user)
    
    # Проверяем наличие медиа
    if not word.image_file and not word.audio_file:
        return Response(
            {'error': 'Для empty-карточки нужно изображение или аудио'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем, нет ли уже пустой
    if Card.objects.filter(word=word, card_type='empty').exists():
        return Response(
            {'error': 'Пустая карточка уже существует'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        card = Card.create_empty(word)
        serializer = CardSerializer(card)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_cloze_view(request, word_id):
    """
    POST /api/words/{word_id}/cards/cloze/ — Создать cloze-карточку
    
    Body:
        - sentence: str — Предложение с целевым словом
        - word_index: int — Индекс слова для пропуска (0-based)
    """
    word = get_object_or_404(Word.objects.select_related('user'), id=word_id, user=request.user)
    
    serializer = CardCreateClozeSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    sentence = serializer.validated_data['sentence']
    word_index = serializer.validated_data.get('word_index', 0)
    
    # Проверяем, нет ли уже такой cloze
    if Card.objects.filter(word=word, card_type='cloze', cloze_sentence=sentence).exists():
        return Response(
            {'error': 'Cloze-карточка с этим предложением уже существует'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        card = Card.create_cloze(word, sentence, word_index)
        serializer = CardSerializer(card)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ═══════════════════════════════════════════════════════════════
# ЭТАП 8: Words Catalog API
# ═══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_stats_view(request, word_id):
    """
    GET /api/words/{word_id}/stats/
    Получение статистики по слову
    """
    word = get_object_or_404(Word.objects.select_related('user'), id=word_id, user=request.user)
    
    # Обновляем статус на основе карточек
    update_word_learning_status(word)
    word.refresh_from_db()
    
    # Получаем статистику по карточкам
    cards_stats = get_word_cards_stats(word)
    
    # Статистика по связям
    synonyms_count = word.get_synonyms().count()
    antonyms_count = word.get_antonyms().count()
    
    # Статистика по категориям и колодам
    categories_count = word.categories.count()
    decks_count = word.decks.count()
    
    # Статистика по контенту
    has_etymology = bool(word.etymology)
    has_hint = bool(word.hint_text)
    has_sentences = bool(word.sentences and len(word.sentences) > 0)
    sentences_count = len(word.sentences) if word.sentences else 0
    
    response_data = {
        'word_id': word.id,
        'cards_stats': cards_stats,
        'learning_status': word.learning_status,
        'has_etymology': has_etymology,
        'has_hint': has_hint,
        'has_sentences': has_sentences,
        'sentences_count': sentences_count,
        'relations_count': {
            'synonyms': synonyms_count,
            'antonyms': antonyms_count
        },
        'categories_count': categories_count,
        'decks_count': decks_count
    }
    
    serializer = WordStatsSerializer(response_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def words_stats_view(request):
    """
    GET /api/words/stats/
    Получение общей статистики по словам пользователя
    """
    words = Word.objects.filter(user=request.user).select_related('user')
    cards = Card.objects.filter(user=request.user, word__user=request.user)
    now = timezone.now()
    
    # Общее количество слов
    total_words = words.count()
    
    # По языкам
    by_language = {}
    for lang_code, lang_name in Word.LANGUAGE_CHOICES:
        count = words.filter(language=lang_code).count()
        if count > 0:
            by_language[lang_code] = count
    
    # По статусам (обновляем статусы перед подсчётом)
    # Используем iterator() для оптимизации памяти при большом количестве слов
    words_list = list(words)
    for word in words_list:
        update_word_learning_status(word)
    
    # Обновляем QuerySet после изменения статусов
    words = Word.objects.filter(id__in=[w.id for w in words_list])
    
    by_status = {}
    for status_code, status_name in Word.LEARNING_STATUS_CHOICES:
        count = words.filter(learning_status=status_code).count()
        if count > 0:
            by_status[status_code] = count
    
    # По частям речи
    by_part_of_speech = {}
    for pos_code, pos_name in Word.PART_OF_SPEECH_CHOICES:
        count = words.filter(part_of_speech=pos_code).count()
        if count > 0:
            by_part_of_speech[pos_code] = count
    
    # По наличию контента
    with_etymology = words.exclude(etymology='').count()
    with_hint = words.exclude(hint_text='').count()
    with_sentences = words.exclude(sentences=[]).count()
    
    # Общее количество карточек
    total_cards = cards.count()
    
    # Карточки на повторении
    due_for_review = cards.filter(
        is_in_learning_mode=False,
        next_review__lte=now
    ).count()
    
    response_data = {
        'total_words': total_words,
        'by_language': by_language,
        'by_status': by_status,
        'by_part_of_speech': by_part_of_speech,
        'with_etymology': with_etymology,
        'with_hint': with_hint,
        'with_sentences': with_sentences,
        'total_cards': total_cards,
        'due_for_review': due_for_review
    }
    
    serializer = WordsStatsSerializer(response_data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def word_enter_learning_view(request, word_id):
    """
    POST /api/words/{word_id}/enter-learning/
    Отправить все карточки слова в режим изучения
    """
    word = get_object_or_404(Word.objects.select_related('user'), id=word_id, user=request.user)
    
    # Получаем все карточки слова
    cards = Card.objects.filter(word=word, user=request.user)
    
    if not cards.exists():
        return Response(
            {'error': 'У слова нет карточек'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Переводим все карточки в режим изучения
    updated_count = 0
    for card in cards:
        if not card.is_in_learning_mode:
            card.enter_learning_mode()
            card.save()
            updated_count += 1
    
    # Обновляем статус слова
    update_word_learning_status(word)
    word.refresh_from_db()
    
    return Response({
        'message': f'{updated_count} карточка(ок) переведена(ы) в режим изучения',
        'word_id': word.id,
        'cards_updated': updated_count,
        'learning_status': word.learning_status
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def words_bulk_action_view(request):
    """
    POST /api/words/bulk-action/
    Массовые действия со словами
    
    Body:
    {
        "word_ids": [1, 2, 3],
        "action": "enter_learning" | "delete" | "add_to_deck" | "add_to_category" | "remove_from_category",
        "params": {
            "deck_id": 123,  // для add_to_deck
            "category_id": 456  // для add_to_category/remove_from_category
        }
    }
    """
    serializer = BulkActionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word_ids = serializer.validated_data['word_ids']
    action = serializer.validated_data['action']
    params = serializer.validated_data.get('params', {})
    
    # Получаем слова пользователя
    words = Word.objects.filter(id__in=word_ids, user=request.user).select_related('user')
    
    if words.count() != len(word_ids):
        return Response(
            {'error': 'Некоторые слова не найдены или не принадлежат пользователю'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    processed = 0
    successful = 0
    failed = 0
    errors = []
    
    for word in words:
        try:
            processed += 1
            
            if action == 'enter_learning':
                # Отправляем все карточки в режим изучения
                cards = Card.objects.filter(word=word, user=request.user)
                for card in cards:
                    if not card.is_in_learning_mode:
                        card.enter_learning_mode()
                        card.save()
                update_word_learning_status(word)
                successful += 1
            
            elif action == 'delete':
                # Удаляем слово
                word.delete()
                successful += 1
            
            elif action == 'add_to_deck':
                deck_id = params.get('deck_id')
                if not deck_id:
                    errors.append({
                        'word_id': word.id,
                        'error': 'deck_id не указан в params'
                    })
                    failed += 1
                    continue
                
                from apps.cards.models import Deck
                deck = Deck.objects.filter(id=deck_id, user=request.user).first()
                if not deck:
                    errors.append({
                        'word_id': word.id,
                        'error': f'Колода {deck_id} не найдена'
                    })
                    failed += 1
                    continue
                
                word.decks.add(deck)
                successful += 1
            
            elif action == 'add_to_category':
                category_id = params.get('category_id')
                if not category_id:
                    errors.append({
                        'word_id': word.id,
                        'error': 'category_id не указан в params'
                    })
                    failed += 1
                    continue
                
                category = Category.objects.filter(id=category_id, user=request.user).first()
                if not category:
                    errors.append({
                        'word_id': word.id,
                        'error': f'Категория {category_id} не найдена'
                    })
                    failed += 1
                    continue
                
                word.categories.add(category)
                successful += 1
            
            elif action == 'remove_from_category':
                category_id = params.get('category_id')
                if not category_id:
                    errors.append({
                        'word_id': word.id,
                        'error': 'category_id не указан в params'
                    })
                    failed += 1
                    continue
                
                category = Category.objects.filter(id=category_id, user=request.user).first()
                if not category:
                    errors.append({
                        'word_id': word.id,
                        'error': f'Категория {category_id} не найдена'
                    })
                    failed += 1
                    continue
                
                word.categories.remove(category)
                successful += 1
            
            else:
                errors.append({
                    'word_id': word.id,
                    'error': f'Неизвестное действие: {action}'
                })
                failed += 1
        
        except Exception as e:
            errors.append({
                'word_id': word.id,
                'error': str(e)
            })
            failed += 1
    
    response_data = {
        'action': action,
        'processed': processed,
        'successful': successful,
        'failed': failed,
        'errors': errors
    }
    
    serializer = BulkActionResponseSerializer(response_data)
    return Response(serializer.data, status=status.HTTP_200_OK)
