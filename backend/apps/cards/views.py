import logging
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.words.models import Word
from django.shortcuts import get_object_or_404

from .models import GeneratedDeck, UserPrompt, Deck, Card
from .serializers import (
    CardGenerationSerializer,
    ImageGenerationSerializer,
    ImageEditSerializer,
    AudioGenerationSerializer,
    ImageUploadSerializer,
    AudioUploadSerializer,
    UserPromptSerializer,
    UserPromptUpdateSerializer,
    WordAnalysisSerializer,
    WordTranslationSerializer,
    GermanWordProcessingSerializer,
    DeckSerializer,
    DeckDetailSerializer,
    DeckCreateSerializer,
    DeckUpdateSerializer,
    DeckWordRemoveSerializer,
    DeckMergeSerializer,
    DeckInvertWordSerializer,
    DeckCreateEmptyCardSerializer,
    CardSerializer,
    CardListSerializer,
    CardCreateClozeSerializer,
    CardReviewSerializer,
    CardAnswerSerializer,
)
from .llm_utils import analyze_mixed_languages, translate_words, process_german_word
from .prompt_utils import get_or_create_user_prompt, reset_user_prompt_to_default
from .token_utils import get_or_create_token, add_tokens, check_balance

from .services.media_service import (
    generate_image_for_word,
    edit_image_for_word,
    generate_audio_for_word,
    extract_words_from_photo_service,
    save_uploaded_file,
    get_relative_media_path,
    get_media_url,
)
from .services.generation_service import (
    generate_cards,
    auto_enrich_simple_mode,
    generate_apkg_from_deck,
)
from .services.deck_service import (
    add_words_to_deck,
    update_word_in_deck,
    merge_decks,
    invert_all_words,
    invert_single_word,
    create_empty_cards_for_deck,
    create_empty_card_for_word,
    set_literary_source,
)

logger = logging.getLogger(__name__)


# ========== Card Generation ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_cards_view(request):
    """Generate Anki cards."""
    serializer = CardGenerationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    words_list = serializer.validated_data['words']
    language = serializer.validated_data['language']
    translations = serializer.validated_data['translations']
    audio_files = serializer.validated_data.get('audio_files', {})
    image_files = serializer.validated_data.get('image_files', {})
    deck_name = serializer.validated_data['deck_name']
    image_style = serializer.validated_data.get('image_style', 'balanced')
    save_to_decks = serializer.validated_data.get('save_to_decks', True)

    # Simple mode auto-enrichment
    user_mode = getattr(request.user, 'mode', 'advanced')
    if user_mode == 'simple':
        try:
            translations, deck_name, image_style = auto_enrich_simple_mode(
                request.user, words_list, language, translations, deck_name)
        except Exception as e:
            logger.error(f"Simple mode enrichment error: {e}")

    try:
        result = generate_cards(
            user=request.user,
            words_list=words_list,
            language=language,
            translations=translations,
            audio_files=audio_files,
            image_files=image_files,
            deck_name=deck_name,
            image_style=image_style,
            save_to_decks=save_to_decks,
        )
        return Response(result, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Card generation error for {request.user.username}: {e}", exc_info=True)
        return Response(
            {'error': f'Card generation error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_cards_view(request, file_id):
    """Download generated .apkg file."""
    try:
        generated_deck = GeneratedDeck.objects.get(id=file_id, user=request.user)
    except GeneratedDeck.DoesNotExist:
        raise Http404("File not found")

    file_path = Path(generated_deck.file_path)
    if not file_path.exists():
        raise Http404("File not found on server")

    response = FileResponse(open(file_path, 'rb'), content_type='application/apkg')
    response['Content-Disposition'] = f'attachment; filename="{generated_deck.deck_name}.apkg"'
    return response


# ========== Media Generation ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_image_view(request):
    """Generate image for a word."""
    serializer = ImageGenerationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = generate_image_for_word(
            user=request.user,
            word=serializer.validated_data['word'],
            translation=serializer.validated_data['translation'],
            language=serializer.validated_data['language'],
            word_id=serializer.validated_data.get('word_id'),
            image_style=serializer.validated_data.get('image_style', 'balanced'),
            provider=serializer.validated_data.get('provider'),
            gemini_model=serializer.validated_data.get('gemini_model'),
        )
        return Response(result, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
    except Exception as e:
        return Response(
            {'error': f'Image generation error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_image_view(request):
    """Edit existing word image via mixin."""
    serializer = ImageEditSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = edit_image_for_word(
            user=request.user,
            word_id=serializer.validated_data['word_id'],
            mixin=serializer.validated_data['mixin'],
        )
        return Response(result, status=status.HTTP_200_OK)
    except Word.DoesNotExist:
        return Response(
            {'error': f'Word with ID={serializer.validated_data["word_id"]} not found'},
            status=status.HTTP_404_NOT_FOUND)
    except FileNotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Image edit error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_audio_view(request):
    """Generate audio for a word."""
    serializer = AudioGenerationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = generate_audio_for_word(
            user=request.user,
            word=serializer.validated_data['word'],
            language=serializer.validated_data['language'],
            word_id=serializer.validated_data.get('word_id'),
            provider=serializer.validated_data.get('provider'),
        )
        return Response(result, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
    except Exception as e:
        return Response(
            {'error': f'Audio generation error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image_view(request):
    """Upload custom image."""
    serializer = ImageUploadSerializer(data=request.FILES)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        file_path, file_id = save_uploaded_file(
            serializer.validated_data['image'], 'images',
            allowed_extensions=['.jpg', '.jpeg', '.png'])

        relative_path = get_relative_media_path(file_path)
        return Response({
            'image_url': get_media_url(relative_path),
            'image_id': file_id,
            'file_path': str(file_path),
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'error': f'Image upload error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_audio_view(request):
    """Upload custom audio."""
    serializer = AudioUploadSerializer(data=request.FILES)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        file_path, file_id = save_uploaded_file(
            serializer.validated_data['audio'], 'audio')

        relative_path = get_relative_media_path(file_path)
        return Response({
            'audio_url': get_media_url(relative_path),
            'audio_id': file_id,
            'file_path': str(file_path),
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'error': f'Audio upload error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== User Prompts ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_prompts_view(request):
    """Get all user prompts."""
    prompt_types = [choice[0] for choice in UserPrompt.PROMPT_TYPE_CHOICES]
    prompts = [get_or_create_user_prompt(request.user, pt) for pt in prompt_types]
    serializer = UserPromptSerializer(prompts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_prompt_view(request, prompt_type):
    """Get specific user prompt."""
    valid_types = [choice[0] for choice in UserPrompt.PROMPT_TYPE_CHOICES]
    if prompt_type not in valid_types:
        return Response(
            {'error': f'Invalid prompt type. Available: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST)

    user_prompt = get_or_create_user_prompt(request.user, prompt_type)
    serializer = UserPromptSerializer(user_prompt)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_prompt_view(request, prompt_type):
    """Update user prompt."""
    valid_types = [choice[0] for choice in UserPrompt.PROMPT_TYPE_CHOICES]
    if prompt_type not in valid_types:
        return Response(
            {'error': f'Invalid prompt type. Available: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST)

    user_prompt = get_or_create_user_prompt(request.user, prompt_type)
    serializer = UserPromptUpdateSerializer(user_prompt, data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_prompt.custom_prompt = serializer.validated_data['custom_prompt']
        user_prompt.is_custom = True
        user_prompt.full_clean()
        user_prompt.save()
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    result_serializer = UserPromptSerializer(user_prompt)
    return Response(result_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_user_prompt_view(request, prompt_type):
    """Reset prompt to default."""
    valid_types = [choice[0] for choice in UserPrompt.PROMPT_TYPE_CHOICES]
    if prompt_type not in valid_types:
        return Response(
            {'error': f'Invalid prompt type. Available: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST)

    user_prompt = reset_user_prompt_to_default(request.user, prompt_type)
    serializer = UserPromptSerializer(user_prompt)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ========== Word Analysis & Translation ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_words_view(request):
    """Analyze mixed languages and return word-translation pairs."""
    serializer = WordAnalysisSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = analyze_mixed_languages(
            words_list=serializer.validated_data['words'],
            learning_language=serializer.validated_data['learning_language'],
            native_language=serializer.validated_data['native_language'],
            user=request.user,
        )
        return Response({'translations': result}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Word analysis error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def translate_words_view(request):
    """Translate words from learning language to native."""
    serializer = WordTranslationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = translate_words(
            words_list=serializer.validated_data['words'],
            learning_language=serializer.validated_data['learning_language'],
            native_language=serializer.validated_data['native_language'],
            user=request.user,
        )

        if not result:
            return Response({
                'error': 'Failed to get translations.',
                'translations': {},
            }, status=status.HTTP_200_OK)

        return Response({'translations': result}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response(
            {'error': str(e), 'translations': {}},
            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Translation error: {e}', 'translations': {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_german_words_view(request):
    """Process German word: add article for nouns, fix capitalization."""
    serializer = GermanWordProcessingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        processed_word = process_german_word(
            serializer.validated_data['word'], user=request.user)
        return Response({'processed_word': processed_word}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'German word processing error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_words_from_photo_view(request):
    """Extract words from photo via LLM vision."""
    image_file = request.FILES.get('image')
    target_lang = request.data.get('target_lang')
    source_lang = request.data.get('source_lang')

    if not image_file:
        return Response({'error': 'image field is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not target_lang or not source_lang:
        return Response(
            {'error': 'target_lang and source_lang are required'},
            status=status.HTTP_400_BAD_REQUEST)

    allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
    if image_file.content_type not in allowed_types:
        return Response(
            {'error': f'Unsupported format: {image_file.content_type}. Allowed: JPEG, PNG'},
            status=status.HTTP_400_BAD_REQUEST)

    max_size = 10 * 1024 * 1024
    if image_file.size > max_size:
        return Response(
            {'error': f'File too large ({image_file.size} bytes). Max: 10 MB'},
            status=status.HTTP_400_BAD_REQUEST)

    try:
        words = extract_words_from_photo_service(
            user=request.user,
            image_data=image_file.read(),
            target_lang=target_lang,
            source_lang=source_lang,
        )
        return Response({'words': words}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
    except Exception as e:
        return Response(
            {'error': f'Photo extraction error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== Deck Management ==========

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def deck_list_create_view(request):
    """GET: List decks. POST: Create deck."""
    if request.method == 'GET':
        decks = Deck.objects.filter(user=request.user).select_related('user')
        serializer = DeckSerializer(decks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = DeckCreateSerializer(data=request.data)
    if serializer.is_valid():
        deck = serializer.save(user=request.user)
        result_serializer = DeckSerializer(deck)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def deck_detail_view(request, deck_id):
    """GET: Deck details. PATCH: Update deck. DELETE: Delete deck."""
    deck = get_object_or_404(
        Deck.objects.select_related('user').prefetch_related('words'),
        id=deck_id, user=request.user)

    if request.method == 'GET':
        serializer = DeckDetailSerializer(deck, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PATCH':
        serializer = DeckUpdateSerializer(deck, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            result_serializer = DeckDetailSerializer(deck, context={'request': request})
            return Response(result_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    deck.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def deck_set_literary_source_view(request, deck_id):
    """Set literary source for a deck."""
    try:
        result = set_literary_source(
            user=request.user,
            deck_id=deck_id,
            source_slug=request.data.get('source_slug'),
            use_global=request.data.get('use_global', False),
        )
        return Response(result)
    except Deck.DoesNotExist:
        return Response({'error': 'Deck not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_add_words_view(request, deck_id):
    """Add words to a deck."""
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)

    # Support multiple input formats
    if isinstance(request.data, list):
        words_data = request.data
    elif isinstance(request.data, dict) and 'words' in request.data:
        words_data = request.data['words']
    else:
        words_data = [request.data]

    added_words, errors = add_words_to_deck(request.user, deck, words_data)

    if errors:
        return Response(
            {'added_words': added_words, 'errors': errors},
            status=status.HTTP_207_MULTI_STATUS)

    return Response({
        'added_words': added_words,
        'message': f'Added {len(added_words)} words',
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_remove_word_view(request, deck_id):
    """Remove word from a deck."""
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)

    serializer = DeckWordRemoveSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    word_id = serializer.validated_data['word_id']
    try:
        word = Word.objects.get(id=word_id, user=request.user)
        if word in deck.words.all():
            deck.words.remove(word)
            return Response({'message': 'Word removed from deck'}, status=status.HTTP_200_OK)
        return Response({'error': 'Word not found in deck'}, status=status.HTTP_404_NOT_FOUND)
    except Word.DoesNotExist:
        return Response(
            {'error': f'Word with ID {word_id} not found'},
            status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def deck_update_word_view(request, deck_id, word_id):
    """Update word in a deck."""
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)

    try:
        result = update_word_in_deck(request.user, deck, word_id, request.data)
        return Response(result, status=status.HTTP_200_OK)
    except Word.DoesNotExist as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        error_data = e.args[0] if e.args and isinstance(e.args[0], dict) else str(e)
        if isinstance(error_data, dict):
            return Response(
                {'error': 'Validation errors', 'errors': error_data},
                status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': error_data}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Error saving: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_merge_view(request):
    """Merge multiple decks into one."""
    serializer = DeckMergeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = merge_decks(
            user=request.user,
            deck_ids=serializer.validated_data['deck_ids'],
            target_deck_id=serializer.validated_data.get('target_deck_id'),
            new_deck_name=serializer.validated_data.get('new_deck_name', 'Merged deck'),
            delete_source_decks=serializer.validated_data.get('delete_source_decks', False),
        )
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Deck.DoesNotExist:
        return Response({'error': 'Target deck not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_generate_apkg_view(request, deck_id):
    """Generate .apkg file from a deck."""
    try:
        result = generate_apkg_from_deck(request.user, deck_id)
        return Response(result, status=status.HTTP_201_CREATED)
    except Deck.DoesNotExist:
        return Response({'error': 'Deck not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Deck generation error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== Token System ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_token_balance_view(request):
    """Get user token balance."""
    balance = check_balance(request.user)
    return Response({'balance': balance}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_token_transactions_view(request):
    """Get token transaction history."""
    from .models import TokenTransaction

    transactions = TokenTransaction.objects.filter(user=request.user)[:50]
    transactions_data = [{
        'id': t.id,
        'transaction_type': t.transaction_type,
        'transaction_type_display': t.get_transaction_type_display(),
        'amount': t.amount,
        'description': t.description,
        'created_at': t.created_at,
    } for t in transactions]

    return Response({
        'transactions': transactions_data,
        'count': len(transactions_data),
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_tokens_view(request):
    """Add tokens (admin only)."""
    if not request.user.is_staff:
        return Response(
            {'error': 'Only admins can add tokens'},
            status=status.HTTP_403_FORBIDDEN)

    amount = request.data.get('amount')
    description = request.data.get('description', '')
    user_id = request.data.get('user_id')

    try:
        amount = int(amount) if amount else 0
    except (ValueError, TypeError):
        return Response(
            {'error': 'Amount must be a number'},
            status=status.HTTP_400_BAD_REQUEST)

    if not amount or amount <= 0:
        return Response(
            {'error': 'Amount must be positive'},
            status=status.HTTP_400_BAD_REQUEST)

    if not user_id:
        return Response(
            {'error': 'user_id is required'},
            status=status.HTTP_400_BAD_REQUEST)

    from django.contrib.auth import get_user_model
    UserModel = get_user_model()
    try:
        target_user = UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    token = add_tokens(
        target_user, amount,
        description or f"Added by admin {request.user.username}")

    return Response({
        'message': f'Added {amount} tokens to {target_user.username}',
        'balance': token.balance,
    }, status=status.HTTP_200_OK)


# ========== Deck Invert & Empty Cards ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_invert_all_words_view(request, deck_id):
    """Create inverted cards for all words in a deck."""
    try:
        result = invert_all_words(request.user, deck_id)
        return Response({
            'message': f'Created {result["inverted_cards_count"]} inverted cards',
            **result,
        }, status=status.HTTP_200_OK)
    except Deck.DoesNotExist:
        return Response({'error': 'Deck not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_invert_word_view(request, deck_id):
    """Create inverted card for a single word."""
    serializer = DeckInvertWordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = invert_single_word(
            request.user, deck_id, serializer.validated_data['word_id'])
        return Response({
            'message': 'Inverted card created',
            **result,
        }, status=status.HTTP_200_OK)
    except Deck.DoesNotExist:
        return Response({'error': 'Deck not found'}, status=status.HTTP_404_NOT_FOUND)
    except Word.DoesNotExist as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Inversion error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_create_empty_cards_view(request, deck_id):
    """Create empty cards for all words in a deck."""
    try:
        result = create_empty_cards_for_deck(request.user, deck_id)
        return Response({
            'message': f'Created {result["empty_cards_count"]} empty cards',
            **result,
        }, status=status.HTTP_200_OK)
    except Deck.DoesNotExist:
        return Response({'error': 'Deck not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_create_empty_card_view(request, deck_id):
    """Create empty card for a single word."""
    serializer = DeckCreateEmptyCardSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = create_empty_card_for_word(
            request.user, deck_id, serializer.validated_data['word_id'])
        return Response({
            'message': 'Empty card created',
            **result,
        }, status=status.HTTP_200_OK)
    except Deck.DoesNotExist:
        return Response({'error': 'Deck not found'}, status=status.HTTP_404_NOT_FOUND)
    except Word.DoesNotExist as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {'error': f'Empty card creation error: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== Card API ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def card_list_view(request):
    """List user's cards with filters."""
    cards = Card.objects.filter(user=request.user).select_related('word')

    card_type = request.query_params.get('type')
    if card_type:
        cards = cards.filter(card_type=card_type)

    learning = request.query_params.get('learning')
    if learning == 'true':
        cards = cards.filter(is_in_learning_mode=True)
    elif learning == 'false':
        cards = cards.filter(is_in_learning_mode=False)

    suspended = request.query_params.get('suspended')
    if suspended != 'true':
        cards = cards.filter(is_suspended=False)

    word_id = request.query_params.get('word_id')
    if word_id:
        cards = cards.filter(word_id=word_id)

    serializer = CardListSerializer(cards, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def card_detail_view(request, card_id):
    """GET: Card details. DELETE: Delete card."""
    card = get_object_or_404(
        Card.objects.select_related('word'), id=card_id, user=request.user)

    if request.method == 'GET':
        serializer = CardSerializer(card)
        return Response(serializer.data)

    # DELETE
    if card.card_type == 'normal':
        other_cards = Card.objects.filter(word=card.word).exclude(id=card.id).count()
        if other_cards == 0:
            return Response(
                {'error': 'Cannot delete the only card for a word'},
                status=status.HTTP_400_BAD_REQUEST)

    card.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_inverted_view(request, word_id):
    """Create inverted card for a word."""
    word = get_object_or_404(Word, id=word_id, user=request.user)

    if Card.objects.filter(word=word, card_type='inverted').exists():
        return Response(
            {'error': 'Inverted card already exists'},
            status=status.HTTP_400_BAD_REQUEST)

    card = Card.create_inverted(word)
    serializer = CardSerializer(card)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_empty_view(request, word_id):
    """Create empty card for a word."""
    word = get_object_or_404(Word, id=word_id, user=request.user)

    if not word.image_file and not word.audio_file:
        return Response(
            {'error': 'Empty card requires image or audio'},
            status=status.HTTP_400_BAD_REQUEST)

    if Card.objects.filter(word=word, card_type='empty').exists():
        return Response(
            {'error': 'Empty card already exists'},
            status=status.HTTP_400_BAD_REQUEST)

    try:
        card = Card.create_empty(word)
        serializer = CardSerializer(card)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_cloze_view(request, word_id):
    """Create cloze card for a word."""
    word = get_object_or_404(Word, id=word_id, user=request.user)

    serializer = CardCreateClozeSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    sentence = serializer.validated_data['sentence']
    word_index = serializer.validated_data.get('word_index', 0)

    if Card.objects.filter(word=word, card_type='cloze', cloze_sentence=sentence).exists():
        return Response(
            {'error': 'Cloze card with this sentence already exists'},
            status=status.HTTP_400_BAD_REQUEST)

    try:
        card = Card.create_cloze(word, sentence, word_index)
        serializer = CardSerializer(card)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_suspend_view(request, card_id):
    """Suspend a card."""
    card = get_object_or_404(Card, id=card_id, user=request.user)
    card.suspend()
    return Response({'status': 'suspended'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_unsuspend_view(request, card_id):
    """Unsuspend a card."""
    card = get_object_or_404(Card, id=card_id, user=request.user)
    card.unsuspend()
    return Response({'status': 'unsuspended'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_enter_learning_view(request, card_id):
    """Enter learning mode for a card."""
    card = get_object_or_404(Card, id=card_id, user=request.user)
    card.enter_learning_mode()
    return Response({'status': 'in_learning_mode'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_cards_list_view(request, word_id):
    """List all cards for a word."""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    cards = Card.objects.filter(word=word).select_related('word')
    serializer = CardListSerializer(cards, many=True, context={'request': request})
    return Response(serializer.data)
