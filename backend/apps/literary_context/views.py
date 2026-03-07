import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from django.db.models import Count

from apps.words.models import Word
from apps.cards.models import Deck
from apps.cards.llm_utils import translate_words
from .models import LiterarySource, LiteraryText, WordContextMedia
from .serializers import (
    LiterarySourceSerializer,
    LiteraryTextListSerializer,
    LiteraryTextDetailSerializer,
    WordContextMediaSerializer,
)
from .generation import generate_word_context, generate_batch_context

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sources_list_view(request):
    """GET /api/literary-context/sources/ -- list active literary sources."""
    sources = LiterarySource.objects.filter(is_active=True)
    serializer = LiterarySourceSerializer(sources, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_context_view(request):
    """
    POST /api/literary-context/generate/
    Body: {word_id: int, source_slug: str}
    """
    word_id = request.data.get('word_id')
    source_slug = request.data.get('source_slug')

    if not word_id or not source_slug:
        return Response(
            {'error': 'word_id and source_slug are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    word = get_object_or_404(Word, id=word_id, user=request.user)
    source = get_object_or_404(LiterarySource, slug=source_slug, is_active=True)

    try:
        context_media = generate_word_context(word, source)
    except Exception as e:
        logger.error(f'Context generation failed for word {word_id}: {e}')
        return Response(
            {'error': 'Failed to generate literary context. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    serializer = WordContextMediaSerializer(context_media, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_batch_context_view(request):
    """
    POST /api/literary-context/generate-batch/
    Body: {word_ids: [int], source_slug: str, skip_existing: bool}
    """
    word_ids = request.data.get('word_ids', [])
    source_slug = request.data.get('source_slug')
    skip_existing = request.data.get('skip_existing', True)

    if not word_ids or not source_slug:
        return Response(
            {'error': 'word_ids and source_slug are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    source = get_object_or_404(LiterarySource, slug=source_slug, is_active=True)
    words = Word.objects.filter(id__in=word_ids, user=request.user)

    try:
        stats = generate_batch_context(words, source, skip_existing=skip_existing)
    except Exception as e:
        logger.error(f'Batch context generation failed: {e}')
        return Response(
            {'error': 'Batch generation failed. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_context_media_view(request, word_id):
    """GET /api/literary-context/word/<word_id>/media/ -- all context media for a word."""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    context_media = WordContextMedia.objects.filter(word=word).select_related(
        'source', 'anchor', 'fragment'
    )
    serializer = WordContextMediaSerializer(
        context_media, many=True, context={'request': request}
    )
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_deck_context_view(request):
    """
    POST /api/literary-context/generate-deck-context/
    Body: {deck_id: int, source_slug: str}
    Generates literary context for all words in the deck using the specified source.
    """
    deck_id = request.data.get('deck_id')
    source_slug = request.data.get('source_slug')

    if not deck_id or not source_slug:
        return Response(
            {'error': 'deck_id and source_slug are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    source = get_object_or_404(LiterarySource, slug=source_slug, is_active=True)

    words = deck.words.all()
    if not words.exists():
        return Response({'generated': 0, 'skipped': 0, 'errors': 0})

    try:
        stats = generate_batch_context(words, source, skip_existing=True)
    except Exception as e:
        logger.error(f'Deck context generation failed for deck {deck_id}: {e}')
        return Response(
            {'error': 'Generation failed. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Auto-set deck literary source to the generated source
    deck.literary_source = source
    deck.literary_source_override = True
    deck.save(update_fields=['literary_source', 'literary_source_override', 'updated_at'])

    return Response(stats, status=status.HTTP_200_OK)


# --- Reader API ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def texts_list_view(request, source_slug):
    """
    GET /api/literary-context/sources/{slug}/texts/
    Returns table-of-contents for a source. Groups by slug, shows available languages.
    """
    source = get_object_or_404(LiterarySource, slug=source_slug, is_active=True)

    search = request.query_params.get('search', '').strip()
    sort_by = request.query_params.get('sort', 'sort_order')

    texts = LiteraryText.objects.filter(source=source)
    if search:
        texts = texts.filter(title__icontains=search)

    # Group by slug, collect available languages
    from collections import defaultdict
    slug_map = defaultdict(lambda: {'languages': [], 'obj': None})
    for text in texts:
        entry = slug_map[text.slug]
        entry['languages'].append(text.language)
        if text.language == source.source_language or entry['obj'] is None:
            entry['obj'] = text

    result_texts = []
    for slug, data in slug_map.items():
        obj = data['obj']
        obj._languages = sorted(data['languages'])
        result_texts.append(obj)

    if sort_by == 'year':
        result_texts.sort(key=lambda t: t.year or 9999)
    elif sort_by == 'title':
        result_texts.sort(key=lambda t: t.title)
    elif sort_by == 'word_count':
        result_texts.sort(key=lambda t: t.word_count, reverse=True)
    else:
        result_texts.sort(key=lambda t: t.sort_order)

    serializer = LiteraryTextListSerializer(result_texts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def text_detail_view(request, source_slug, text_slug):
    """
    GET /api/literary-context/sources/{slug}/texts/{text_slug}/
    Returns full text for reading. Query: ?language=de (default: de)
    """
    source = get_object_or_404(LiterarySource, slug=source_slug, is_active=True)
    language = request.query_params.get('language', 'de')
    text = get_object_or_404(
        LiteraryText, source=source, slug=text_slug, language=language
    )
    serializer = LiteraryTextDetailSerializer(text)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def word_from_reader_view(request):
    """
    POST /api/literary-context/word-from-reader/
    Body: {original_word, source_slug?, language?}
    Creates/finds a word, auto-translates, optionally generates literary context.
    """
    original_word = request.data.get('original_word', '').strip()
    source_slug = request.data.get('source_slug', '')
    language = request.data.get('language', 'de')

    if not original_word:
        return Response(
            {'error': 'original_word is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Auto-translate
    translation = ''
    try:
        user_profile = request.user.profile
        native_lang = getattr(user_profile, 'native_language', 'ru')
    except Exception:
        native_lang = 'ru'

    try:
        translations = translate_words([original_word], language, native_lang, user=request.user)
        translation = translations.get(original_word, '')
    except Exception as e:
        logger.warning(f'Auto-translate failed for "{original_word}": {e}')

    # Get or create word
    word, is_new = Word.objects.get_or_create(
        user=request.user,
        original_word=original_word,
        language=language,
        defaults={'translation': translation},
    )
    if not is_new and translation and not word.translation:
        word.translation = translation
        word.save(update_fields=['translation'])

    result = {
        'word': {
            'id': word.id,
            'original_word': word.original_word,
            'translation': word.translation,
            'is_new': is_new,
        },
        'context_media': None,
    }

    # Generate literary context if source provided
    if source_slug:
        try:
            source = LiterarySource.objects.get(slug=source_slug, is_active=True)
            context_media = generate_word_context(word, source)
            result['context_media'] = {
                'hint_text': context_media.hint_text,
                'sentences': context_media.sentences,
                'match_method': context_media.match_method,
                'is_fallback': context_media.is_fallback,
            }
        except LiterarySource.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f'Context generation failed for reader word "{original_word}": {e}')

    return Response(result, status=status.HTTP_201_CREATED if is_new else status.HTTP_200_OK)
