import os
import uuid
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.storage import default_storage

from apps.words.models import Word
from django.shortcuts import get_object_or_404
from .models import GeneratedDeck, UserPrompt, Deck
from .serializers import (
    CardGenerationSerializer,
    ImageGenerationSerializer,
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
    DeckWordAddSerializer,
    DeckWordRemoveSerializer,
    DeckMergeSerializer,
    DeckInvertWordSerializer,
    DeckCreateEmptyCardSerializer
)
from .utils import generate_apkg, parse_words_input
from .llm_utils import (
    generate_image,
    generate_images_batch,
    generate_audio_with_tts,
    detect_word_language,
    analyze_mixed_languages,
    translate_words,
    process_german_word,
    generate_deck_name,
    detect_category,
    select_image_style
)
from .prompt_utils import get_or_create_user_prompt, reset_user_prompt_to_default
from .token_utils import (
    get_or_create_token,
    add_tokens,
    spend_tokens,
    refund_tokens,
    check_balance,
    get_image_generation_cost,
    IMAGE_GENERATION_COST,
    AUDIO_GENERATION_COST
)


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
    image_style = serializer.validated_data.get('image_style', 'balanced')
    save_to_decks = serializer.validated_data.get('save_to_decks', True)
    
    # Проверяем режим пользователя (простой или расширенный)
    user_mode = getattr(request.user, 'mode', 'advanced')
    
    # Если простой режим, используем автоматизацию
    if user_mode == 'simple':
        try:
            # Автоматически определяем язык изучения из профиля пользователя
            learning_language = request.user.learning_language or language
            native_language = request.user.native_language or 'ru'
            
            # Автоматически переводим слова, если переводы не предоставлены
            if not translations or len(translations) < len(words_list):
                auto_translations = translate_words(
                    words_list=words_list,
                    learning_language=learning_language,
                    native_language=native_language,
                    user=request.user
                )
                # Объединяем с существующими переводами
                translations = {**auto_translations, **translations}
            
            # Автоматически генерируем название колоды
            if not deck_name or deck_name == 'Новая колода':
                deck_name = generate_deck_name(
                    words_list=words_list,
                    learning_language=learning_language,
                    native_language=native_language,
                    user=request.user
                )
            
            # Автоматически определяем категорию и выбираем стиль изображения
            category = detect_category(
                words_list=words_list,
                language=learning_language,
                native_language=native_language,
                user=request.user
            )
            image_style = select_image_style(category)
            
        except Exception as e:
            logger.error(f"Ошибка в простом режиме: {str(e)}")
            # В случае ошибки продолжаем с предоставленными данными
    
    # Подготавливаем данные для генерации
    words_data = []
    media_files = []
    
    # Логируем критическую операцию
    logger.info(f"Начало генерации колоды для пользователя {request.user.username}: {len(words_list)} слов, название: {deck_name}")
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
            # Преобразуем путь в абсолютный (обрабатываем относительные пути и полные URL)
            normalized_audio_path = None
            if audio_path.startswith('http://') or audio_path.startswith('https://'):
                # Полный URL - извлекаем относительный путь
                if '/media/audio/' in audio_path:
                    relative_path = 'audio/' + audio_path.split('/media/audio/')[-1]
                    normalized_audio_path = Path(settings.MEDIA_ROOT) / relative_path
                elif '/media/' in audio_path:
                    relative_path = audio_path.split('/media/')[-1]
                    normalized_audio_path = Path(settings.MEDIA_ROOT) / relative_path
            elif audio_path.startswith('/media/'):
                # Относительный путь, начинающийся с /media/
                relative_path = audio_path.replace('/media/', '')
                normalized_audio_path = Path(settings.MEDIA_ROOT) / relative_path
            elif not Path(audio_path).is_absolute():
                # Относительный путь без /media/
                normalized_audio_path = Path(settings.MEDIA_ROOT) / audio_path
            else:
                # Уже абсолютный путь
                normalized_audio_path = Path(audio_path)
            
            # Проверяем существование файла
            if normalized_audio_path and normalized_audio_path.exists():
                word_data['audio_file'] = str(normalized_audio_path)
                if str(normalized_audio_path) not in media_files:
                    media_files.append(str(normalized_audio_path))
                
                # Сохраняем аудио в модель Word (относительный путь от MEDIA_ROOT)
                relative_audio_path = str(normalized_audio_path.relative_to(Path(settings.MEDIA_ROOT)))
                word_obj.audio_file = relative_audio_path
                word_obj.save(update_fields=['audio_file'])
                
                logger.info(f"✅ Добавлено аудио для '{word}': {normalized_audio_path} (сохранено в БД: {relative_audio_path})")
            else:
                logger.error(f"❌ Файл аудио не существует: {normalized_audio_path} (исходный путь: {audio_path})")
        else:
            # Если новое аудио не предоставлено, используем существующее из БД (если есть)
            if word_obj.audio_file:
                existing_audio_path = Path(settings.MEDIA_ROOT) / word_obj.audio_file.name
                if existing_audio_path.exists():
                    word_data['audio_file'] = str(existing_audio_path)
                    if str(existing_audio_path) not in media_files:
                        media_files.append(str(existing_audio_path))
                    logger.info(f"✅ Использовано существующее аудио для '{word}': {existing_audio_path}")
                else:
                    logger.warning(f"⚠️ Существующее аудио не найдено: {existing_audio_path}")
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
            # Преобразуем путь в абсолютный (обрабатываем относительные пути и полные URL)
            normalized_image_path = None
            if image_path.startswith('http://') or image_path.startswith('https://'):
                # Полный URL - извлекаем относительный путь
                if '/media/images/' in image_path:
                    relative_path = 'images/' + image_path.split('/media/images/')[-1]
                    normalized_image_path = Path(settings.MEDIA_ROOT) / relative_path
                elif '/media/' in image_path:
                    relative_path = image_path.split('/media/')[-1]
                    normalized_image_path = Path(settings.MEDIA_ROOT) / relative_path
            elif image_path.startswith('/media/'):
                # Относительный путь, начинающийся с /media/
                relative_path = image_path.replace('/media/', '')
                normalized_image_path = Path(settings.MEDIA_ROOT) / relative_path
            elif not Path(image_path).is_absolute():
                # Относительный путь без /media/
                normalized_image_path = Path(settings.MEDIA_ROOT) / image_path
            else:
                # Уже абсолютный путь
                normalized_image_path = Path(image_path)
            
            # Проверяем существование файла
            if normalized_image_path and normalized_image_path.exists():
                word_data['image_file'] = str(normalized_image_path)
                if str(normalized_image_path) not in media_files:
                    media_files.append(str(normalized_image_path))
                
                # Сохраняем изображение в модель Word (относительный путь от MEDIA_ROOT)
                relative_image_path = str(normalized_image_path.relative_to(Path(settings.MEDIA_ROOT)))
                word_obj.image_file = relative_image_path
                word_obj.save(update_fields=['image_file'])
                
                logger.info(f"✅ Добавлено изображение для '{word}': {normalized_image_path} (сохранено в БД: {relative_image_path})")
            else:
                logger.error(f"❌ Файл изображения не существует: {normalized_image_path} (исходный путь: {image_path})")
        else:
            # Если новое изображение не предоставлено, используем существующее из БД (если есть)
            if word_obj.image_file:
                existing_image_path = Path(settings.MEDIA_ROOT) / word_obj.image_file.name
                if existing_image_path.exists():
                    word_data['image_file'] = str(existing_image_path)
                    if str(existing_image_path) not in media_files:
                        media_files.append(str(existing_image_path))
                    logger.info(f"✅ Использовано существующее изображение для '{word}': {existing_image_path}")
                else:
                    logger.warning(f"⚠️ Существующее изображение не найдено: {existing_image_path}")
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
        
        logger.info(f"Колода успешно сгенерирована: {deck_name}, файл: {file_id}, карточек: {generated_deck.cards_count}")
        
        # Автоматически импортируем колоду в базу синхронизации Anki
        try:
            from apps.anki_sync.utils import import_apkg_to_anki_collection
            import_result = import_apkg_to_anki_collection(
                user=request.user,
                apkg_path=output_path
            )
            logger.info(f"Колода импортирована в базу синхронизации: {import_result}")
        except Exception as e:
            # Не прерываем выполнение, если импорт не удался
            logger.warning(f"Не удалось импортировать колоду в базу синхронизации: {str(e)}")
        
        # Если нужно сохранить в "Мои колоды"
        deck_id = None
        if save_to_decks:
            # Создаём колоду для редактирования
            deck = Deck.objects.create(
                user=request.user,
                name=deck_name,
                target_lang=language,
                source_lang=request.user.native_language or 'ru'
            )
            # Добавляем слова в колоду
            word_objects = Word.objects.filter(
                user=request.user,
                original_word__in=words_list,
                language=language
            )
            deck.words.set(word_objects)
            deck_id = deck.id
            logger.info(f"Колода сохранена в 'Мои колоды': {deck_name}, ID: {deck_id}")
        
        response_data = {
            'file_id': file_id,
            'download_url': f'/api/cards/download/{file_id}/',
            'deck_name': deck_name,
            'cards_count': generated_deck.cards_count
        }
        
        if deck_id:
            response_data['deck_id'] = deck_id
            response_data['deck_url'] = f'/decks/{deck_id}'
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Ошибка при генерации карточек для пользователя {request.user.username}: {str(e)}", exc_info=True)
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
    provider = serializer.validated_data.get('provider')  # Опционально, если не указан - берется из user.image_provider
    gemini_model = serializer.validated_data.get('gemini_model')  # Опционально, если не указан - берется из user.gemini_model
    
    # Определяем провайдер и модель для расчета стоимости
    # 'auto' или None означает "использовать настройки пользователя"
    if not provider or provider == 'auto':
        provider = request.user.image_provider if hasattr(request.user, 'image_provider') else 'openai'
    
    if provider == 'gemini' and not gemini_model:
        gemini_model = request.user.gemini_model if hasattr(request.user, 'gemini_model') else 'gemini-2.5-flash-image'
    
    # Рассчитываем стоимость генерации
    cost = get_image_generation_cost(provider=provider, gemini_model=gemini_model)
    
    # Проверяем баланс токенов
    balance = check_balance(request.user)
    # Для дробных значений (0.5) конвертируем: 0.5 токена = 1 единица в БД, 1 токен = 2 единицы
    cost_in_units = int(cost * 2)  # 0.5 -> 1, 1.0 -> 2
    
    if balance < cost_in_units:
        balance_display = balance / 2.0  # Для отображения пользователю
        return Response({
            'error': f'Недостаточно токенов. Требуется: {cost}, доступно: {balance_display}'
        }, status=status.HTTP_402_PAYMENT_REQUIRED)
    
    try:
        # Списываем токены перед генерацией
        token, success = spend_tokens(
            request.user,
            cost_in_units,
            description=f"Генерация изображения для слова '{word}' ({provider}, модель: {gemini_model or 'N/A'}, стоимость: {cost} токенов)"
        )
        
        if not success:
            return Response({
                'error': f'Недостаточно токенов для генерации изображения. Требуется: {cost}'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Генерируем изображение с использованием выбранного стиля и провайдера
        image_path, prompt = generate_image(
            word=word,
            translation=translation,
            language=language,
            user=request.user,
            native_language='русском',  # TODO: получить из профиля пользователя
            english_translation=None,  # TODO: получить из перевода или API
            image_style=image_style,
            provider=provider,  # Если указан в запросе, иначе берется из user.image_provider
            gemini_model=gemini_model  # Если указан в запросе, иначе берется из user.gemini_model
        )
        
        # Получаем относительный путь для URL
        media_root = Path(settings.MEDIA_ROOT)
        relative_path = image_path.relative_to(media_root)
        image_url = f"{settings.MEDIA_URL}{relative_path}"
        
        # Получаем ID файла из имени
        image_id = image_path.stem
        
        # Если передан word_id — привязываем изображение к слову
        word_id = serializer.validated_data.get('word_id')
        if word_id:
            try:
                word_obj = Word.objects.get(id=word_id, user=request.user)
                # Сохраняем относительный путь
                word_obj.image_file.name = str(relative_path)
                word_obj.save()
                logger.info(f"Изображение привязано к слову ID={word_id}")
            except Word.DoesNotExist:
                logger.warning(f"Слово с ID={word_id} не найдено для привязки изображения")
        
        return Response({
            'image_url': image_url,
            'image_id': image_id,
            'file_path': str(image_path),
            'prompt': prompt  # Для отладки - показываем промпт в ответе
        }, status=status.HTTP_201_CREATED)
    
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        # При ошибке возвращаем токены
        refund_tokens(
            request.user,
            IMAGE_GENERATION_COST,
            description=f"Возврат токенов за ошибку генерации изображения для слова '{word}'"
        )
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
    provider = serializer.validated_data.get('provider')  # Опционально, если не указан - берется из user.audio_provider
    
    # Определяем провайдер
    if not provider:
        provider = request.user.audio_provider if hasattr(request.user, 'audio_provider') else 'openai'
    
    # Для португальского по умолчанию используем gTTS
    if language == 'pt' and provider == 'openai':
        if not hasattr(request.user, 'audio_provider') or request.user.audio_provider == 'openai':
            logger.info(f"[Audio] Для португальского языка используем gTTS (лучшее качество)")
            provider = 'gtts'
    
    # Проверяем баланс токенов (только для OpenAI, gTTS бесплатный)
    if provider == 'openai':
        balance = check_balance(request.user)
        if balance < AUDIO_GENERATION_COST:
            return Response({
                'error': f'Недостаточно токенов. Требуется: {AUDIO_GENERATION_COST}, доступно: {balance}'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
    
    try:
        # Списываем токены перед генерацией (только для OpenAI)
        if provider == 'openai':
            token, success = spend_tokens(
                request.user,
                AUDIO_GENERATION_COST,
                description=f"Генерация аудио для слова '{word}' (OpenAI TTS)"
            )
            
            if not success:
                return Response({
                    'error': 'Недостаточно токенов для генерации аудио'
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Генерируем аудио с использованием выбранного провайдера
        audio_path = generate_audio_with_tts(
            word=word,
            language=language,
            user=request.user,
            provider=provider
        )
        
        # Получаем относительный путь для URL
        media_root = Path(settings.MEDIA_ROOT)
        relative_path = audio_path.relative_to(media_root)
        audio_url = f"{settings.MEDIA_URL}{relative_path}"
        
        # Получаем ID файла из имени
        audio_id = audio_path.stem
        
        # Если передан word_id — привязываем аудио к слову
        word_id = serializer.validated_data.get('word_id')
        if word_id:
            try:
                word_obj = Word.objects.get(id=word_id, user=request.user)
                # Сохраняем относительный путь
                word_obj.audio_file.name = str(relative_path)
                word_obj.save()
                logger.info(f"Аудио привязано к слову ID={word_id}")
            except Word.DoesNotExist:
                logger.warning(f"Слово с ID={word_id} не найдено для привязки аудио")
        
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
        # При ошибке возвращаем токены (только для OpenAI)
        if provider == 'openai':
            refund_tokens(
                request.user,
                AUDIO_GENERATION_COST,
                description=f"Возврат токенов за ошибку генерации аудио для слова '{word}'"
            )
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_words_view(request):
    """
    Анализ смешанных языков: определяет, какие слова на изучаемом языке,
    а какие на родном, и возвращает пары слово-перевод
    """
    serializer = WordAnalysisSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    words_list = serializer.validated_data['words']
    learning_language = serializer.validated_data['learning_language']
    native_language = serializer.validated_data['native_language']
    
    try:
        result = analyze_mixed_languages(
            words_list=words_list,
            learning_language=learning_language,
            native_language=native_language,
            user=request.user
        )
        
        return Response({
            'translations': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при анализе слов: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def translate_words_view(request):
    """
    Перевод слов с изучаемого языка на родной
    """
    serializer = WordTranslationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    words_list = serializer.validated_data['words']
    learning_language = serializer.validated_data['learning_language']
    native_language = serializer.validated_data['native_language']
    
    try:
        result = translate_words(
            words_list=words_list,
            learning_language=learning_language,
            native_language=native_language,
            user=request.user
        )
        
        return Response({
            'translations': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при переводе слов: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_german_words_view(request):
    """
    Обработка немецкого слова: добавляет артикль для существительных,
    исправляет регистр
    """
    serializer = GermanWordProcessingSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word = serializer.validated_data['word']
    
    try:
        processed_word = process_german_word(word, user=request.user)
        
        return Response({
            'processed_word': processed_word
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при обработке немецкого слова: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== ЭТАП 7: Управление колодами и карточками ==========

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def deck_list_create_view(request):
    """
    GET: Список колод пользователя
    POST: Создание новой колоды
    """
    if request.method == 'GET':
        # Оптимизация: используем select_related для user
        decks = Deck.objects.filter(user=request.user).select_related('user')
        serializer = DeckSerializer(decks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = DeckCreateSerializer(data=request.data)
        if serializer.is_valid():
            deck = serializer.save(user=request.user)
            result_serializer = DeckSerializer(deck)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def deck_detail_view(request, deck_id):
    """
    GET: Детали колоды со списком слов
    PATCH: Обновление колоды
    DELETE: Удаление колоды
    """
    # Оптимизация: используем select_related для user и prefetch_related для words
    deck = get_object_or_404(
        Deck.objects.select_related('user').prefetch_related('words'),
        id=deck_id,
        user=request.user
    )
    
    if request.method == 'GET':
        serializer = DeckDetailSerializer(deck)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = DeckUpdateSerializer(deck, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            result_serializer = DeckDetailSerializer(deck)
            return Response(result_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        deck.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_add_words_view(request, deck_id):
    """
    Добавление слова(ов) в колоду
    
    Поддерживаемые форматы:
    1. { "words": [ {...}, {...} ] }
    2. [ {...}, {...} ]
    3. { "original_word": "...", ... }
    """
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    
    # Поддерживаем разные форматы входных данных
    if isinstance(request.data, list):
        # Формат 2: массив напрямую
        words_data = request.data
    elif isinstance(request.data, dict) and 'words' in request.data:
        # Формат 1: { "words": [...] }
        words_data = request.data['words']
    else:
        # Формат 3: один объект
        words_data = [request.data]
    
    added_words = []
    errors = []
    
    for word_data in words_data:
        serializer = DeckWordAddSerializer(data=word_data)
        if not serializer.is_valid():
            errors.append(serializer.errors)
            continue
        
        word_id = serializer.validated_data.get('word_id')
        
        if word_id:
            # Добавляем существующее слово
            try:
                word = Word.objects.get(id=word_id, user=request.user)
                if word not in deck.words.all():
                    deck.words.add(word)
                    added_words.append(word.id)
            except Word.DoesNotExist:
                errors.append({'word_id': f'Слово с ID {word_id} не найдено'})
        else:
            # Создаем новое слово
            original_word = serializer.validated_data['original_word']
            translation = serializer.validated_data['translation']
            language = serializer.validated_data['language']
            image_url = serializer.validated_data.get('image_url', '')
            audio_url = serializer.validated_data.get('audio_url', '')
            
            # Проверяем, не существует ли уже такое слово
            word, created = Word.objects.get_or_create(
                user=request.user,
                original_word=original_word,
                language=language,
                defaults={'translation': translation}
            )
            
            if not created:
                # Обновляем перевод, если слово уже существовало
                word.translation = translation
            
            # Обновляем медиа-файлы, если переданы
            if image_url:
                # Извлекаем относительный путь из URL (убираем /media/)
                relative_path = image_url.replace('/media/', '') if image_url.startswith('/media/') else image_url
                word.image_file.name = relative_path
            
            if audio_url:
                # Извлекаем относительный путь из URL
                relative_path = audio_url.replace('/media/', '') if audio_url.startswith('/media/') else audio_url
                word.audio_file.name = relative_path
            
            word.save()
            
            if word not in deck.words.all():
                deck.words.add(word)
                added_words.append(word.id)
    
    if errors:
        return Response({
            'added_words': added_words,
            'errors': errors
        }, status=status.HTTP_207_MULTI_STATUS)
    
    return Response({
        'added_words': added_words,
        'message': f'Добавлено слов: {len(added_words)}'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_remove_word_view(request, deck_id):
    """
    Удаление слова из колоды
    """
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    
    serializer = DeckWordRemoveSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word_id = serializer.validated_data['word_id']
    
    try:
        word = Word.objects.get(id=word_id, user=request.user)
        if word in deck.words.all():
            deck.words.remove(word)
            return Response({
                'message': 'Слово удалено из колоды'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Слово не найдено в колоде'
            }, status=status.HTTP_404_NOT_FOUND)
    except Word.DoesNotExist:
        return Response({
            'error': f'Слово с ID {word_id} не найдено'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def deck_update_word_view(request, deck_id, word_id):
    """
    Обновление слова в колоде (слово, перевод, медиа-файлы)
    
    PATCH /api/cards/decks/{deck_id}/words/{word_id}/
    {
        "original_word": "новое слово",        // опционально, max 200 символов
        "translation": "новый перевод",        // опционально, max 200 символов
        "image_file": "/media/images/xxx.jpg", // опционально
        "audio_file": "/media/audio/yyy.mp3"   // опционально
    }
    
    Можно отправлять одно или несколько полей одновременно.
    """
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    
    # Проверяем, что слово принадлежит колоде
    try:
        word = deck.words.get(id=word_id)
    except Word.DoesNotExist:
        return Response({
            'error': f'Слово с ID {word_id} не найдено в колоде'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Обновляем поля
    updated_fields = []
    errors = {}
    
    # Обновление исходного слова
    original_word = request.data.get('original_word')
    if original_word is not None:
        original_word = original_word.strip()
        if not original_word:
            errors['original_word'] = 'Поле не может быть пустым'
        elif len(original_word) > 200:
            errors['original_word'] = 'Максимальная длина: 200 символов'
        else:
            # Проверяем уникальность (user, original_word, language)
            existing_word = Word.objects.filter(
                user=request.user,
                original_word=original_word,
                language=word.language
            ).exclude(id=word_id).first()
            
            if existing_word:
                errors['original_word'] = f'Слово "{original_word}" уже существует для этого языка'
            else:
                word.original_word = original_word
                updated_fields.append('original_word')
    
    # Обновление перевода
    translation = request.data.get('translation')
    if translation is not None:
        translation = translation.strip()
        if not translation:
            errors['translation'] = 'Поле не может быть пустым'
        elif len(translation) > 200:
            errors['translation'] = 'Максимальная длина: 200 символов'
        else:
            word.translation = translation
            updated_fields.append('translation')
    
    # Обновление изображения
    image_file = request.data.get('image_file')
    if image_file is not None:
        if image_file == '' or image_file is None:
            # Удаление изображения
            word.image_file = None
            updated_fields.append('image_file')
        else:
            relative_path = image_file.replace('/media/', '') if image_file.startswith('/media/') else image_file
            word.image_file.name = relative_path
            updated_fields.append('image_file')
    
    # Обновление аудио
    audio_file = request.data.get('audio_file')
    if audio_file is not None:
        if audio_file == '' or audio_file is None:
            # Удаление аудио
            word.audio_file = None
            updated_fields.append('audio_file')
        else:
            relative_path = audio_file.replace('/media/', '') if audio_file.startswith('/media/') else audio_file
            word.audio_file.name = relative_path
            updated_fields.append('audio_file')
    
    # Если есть ошибки валидации
    if errors:
        return Response({
            'error': 'Ошибки валидации',
            'errors': errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Если есть поля для обновления
    if updated_fields:
        try:
            word.save()
            logger.info(f"Слово ID={word_id} обновлено. Поля: {updated_fields}")
            
            return Response({
                'id': word.id,
                'original_word': word.original_word,
                'translation': word.translation,
                'language': word.language,
                'image_file': word.image_file.url if word.image_file else None,
                'audio_file': word.audio_file.url if word.audio_file else None,
                'updated_fields': updated_fields
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Ошибка при обновлении слова ID={word_id}: {str(e)}")
            return Response({
                'error': f'Ошибка при сохранении: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({
            'error': 'Не указаны поля для обновления'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_merge_view(request):
    """
    Объединение нескольких колод в одну
    
    Параметры:
    - deck_ids: список ID колод для объединения (минимум 2)
    - target_deck_id: ID целевой колоды (опционально, если не указан - создается новая)
    - new_deck_name: название новой колоды (используется только если target_deck_id не указан)
    - delete_source_decks: удалить исходные колоды после объединения (по умолчанию False)
    """
    serializer = DeckMergeSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    deck_ids = serializer.validated_data['deck_ids']
    target_deck_id = serializer.validated_data.get('target_deck_id')
    new_deck_name = serializer.validated_data.get('new_deck_name', 'Объединенная колода')
    delete_source_decks = serializer.validated_data.get('delete_source_decks', False)
    
    # Проверяем, что все колоды принадлежат пользователю
    decks = Deck.objects.filter(id__in=deck_ids, user=request.user)
    
    if decks.count() != len(deck_ids):
        return Response({
            'error': 'Некоторые колоды не найдены или не принадлежат вам'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Проверяем, что колоды не дублируются
    if len(set(deck_ids)) != len(deck_ids):
        return Response({
            'error': 'В списке есть дублирующиеся ID колод'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Собираем все слова из всех колод
    all_words = set()
    for deck in decks:
        all_words.update(deck.words.all())
    
    if not all_words:
        return Response({
            'error': 'Все указанные колоды пусты'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Определяем целевую колоду
    if target_deck_id:
        # Используем существующую колоду
        target_deck = get_object_or_404(Deck, id=target_deck_id, user=request.user)
        
        # Проверяем, что целевая колода не в списке исходных (если не удаляем исходные)
        if not delete_source_decks and target_deck_id in deck_ids:
            return Response({
                'error': 'Целевая колода не может быть в списке исходных колод, если исходные колоды не удаляются'
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Создаем новую колоду
        # Определяем язык из первой колоды (предполагаем, что все колоды одного языка)
        first_deck = decks.first()
        target_deck = Deck.objects.create(
            user=request.user,
            name=new_deck_name,
            target_lang=first_deck.target_lang,
            source_lang=first_deck.source_lang
        )
        logger.info(f"Создана новая колода для объединения: {target_deck.name} (ID: {target_deck.id})")
    
    # Добавляем все слова в целевую колоду
    target_deck.words.add(*all_words)
    
    # Удаляем исходные колоды, если нужно
    deleted_decks = []
    if delete_source_decks:
        # Не удаляем целевую колоду, если она была в списке
        decks_to_delete = decks.exclude(id=target_deck.id)
        for deck in decks_to_delete:
            deleted_decks.append({
                'id': deck.id,
                'name': deck.name
            })
            deck.delete()
        logger.info(f"Удалено исходных колод: {len(deleted_decks)}")
    
    # Обновляем целевую колоду
    target_deck.save()
    
    result_serializer = DeckDetailSerializer(target_deck)
    
    return Response({
        'message': f'Колоды успешно объединены в "{target_deck.name}"',
        'target_deck': result_serializer.data,
        'words_count': len(all_words),
        'source_decks_count': len(deck_ids),
        'deleted_decks': deleted_decks if delete_source_decks else None
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_generate_apkg_view(request, deck_id):
    """
    Генерация .apkg файла из колоды
    """
    # Оптимизация: используем prefetch_related для words
    deck = get_object_or_404(
        Deck.objects.select_related('user').prefetch_related('words'),
        id=deck_id,
        user=request.user
    )
    
    # Получаем все слова колоды (уже загружены через prefetch_related)
    words = deck.words.all()
    
    if not words.exists():
        return Response({
            'error': 'Колода пуста. Добавьте слова перед генерацией.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Подготавливаем данные для генерации
        words_data = []
        media_files = []
        
        logger.info(f"📦 Начало генерации .apkg из колоды '{deck.name}' (ID: {deck_id})")
        logger.info(f"📝 Количество слов в колоде: {words.count()}")
        
        for word in words:
            word_data = {
                'original_word': word.original_word,
                'translation': word.translation,
            }
            
            if word.audio_file:
                # Получаем путь к файлу (может быть относительным или абсолютным)
                audio_name = word.audio_file.name
                
                # Если это URL, извлекаем имя файла
                if audio_name.startswith('http://') or audio_name.startswith('https://'):
                    # Извлекаем имя файла из URL: https://.../media/audio/filename.mp3 -> audio/filename.mp3
                    if '/media/audio/' in audio_name:
                        audio_name = 'audio/' + audio_name.split('/media/audio/')[-1]
                    elif '/media/' in audio_name:
                        audio_name = audio_name.split('/media/')[-1]
                    else:
                        # Если не можем извлечь, берем последнюю часть URL
                        audio_name = 'audio/' + audio_name.split('/')[-1]
                
                # Формируем полный путь к файлу
                # Если путь уже абсолютный, используем его, иначе добавляем MEDIA_ROOT
                if Path(audio_name).is_absolute():
                    audio_path = Path(audio_name)
                else:
                    audio_path = Path(settings.MEDIA_ROOT) / audio_name
                
                if audio_path.exists():
                    word_data['audio_file'] = str(audio_path)
                    media_files.append(str(audio_path))
                    logger.info(f"  🔊 Слово '{word.original_word}': аудио = {audio_path} ✅")
                else:
                    logger.warning(f"  🔊 Слово '{word.original_word}': аудио не найдено: {audio_path} ❌")
            
            if word.image_file:
                # Получаем путь к файлу (может быть относительным или абсолютным)
                image_name = word.image_file.name
                
                # Если это URL, извлекаем имя файла
                if image_name.startswith('http://') or image_name.startswith('https://'):
                    # Извлекаем имя файла из URL: https://.../media/images/filename.jpg -> images/filename.jpg
                    if '/media/images/' in image_name:
                        image_name = 'images/' + image_name.split('/media/images/')[-1]
                    elif '/media/' in image_name:
                        image_name = image_name.split('/media/')[-1]
                    else:
                        # Если не можем извлечь, берем последнюю часть URL
                        image_name = 'images/' + image_name.split('/')[-1]
                
                # Формируем полный путь к файлу
                # Если путь уже абсолютный, используем его, иначе добавляем MEDIA_ROOT
                if Path(image_name).is_absolute():
                    image_path = Path(image_name)
                else:
                    image_path = Path(settings.MEDIA_ROOT) / image_name
                
                if image_path.exists():
                    word_data['image_file'] = str(image_path)
                    media_files.append(str(image_path))
                    logger.info(f"  🖼️ Слово '{word.original_word}': изображение = {image_path} ✅")
                else:
                    logger.warning(f"  🖼️ Слово '{word.original_word}': изображение не найдено: {image_path} ❌")
            
            words_data.append(word_data)
        
        logger.info(f"📊 Итого подготовлено:")
        logger.info(f"  - Слов: {len(words_data)}")
        logger.info(f"  - Медиафайлов: {len(media_files)}")
        logger.info(f"  - Пути к медиафайлам: {media_files}")
        
        # Генерируем .apkg файл
        file_id = str(uuid.uuid4())
        output_path = Path(settings.MEDIA_ROOT) / "temp_files" / f"{file_id}.apkg"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🎯 Вызов generate_apkg с {len(words_data)} словами и {len(media_files)} медиафайлами")
        
        generate_apkg(
            words_data=words_data,
            deck_name=deck.name,
            media_files=media_files if media_files else None,
            output_path=output_path
        )
        
        # Проверяем размер созданного файла
        file_size = output_path.stat().st_size if output_path.exists() else 0
        logger.info(f"✅ .apkg файл создан: {output_path} (размер: {file_size / 1024:.2f} KB)")
        
        # Сохраняем информацию о сгенерированной колоде
        generated_deck = GeneratedDeck.objects.create(
            user=request.user,
            deck_name=deck.name,
            file_path=str(output_path),
            cards_count=len(words_data)
        )
        
        # Автоматически импортируем колоду в базу синхронизации Anki
        try:
            from apps.anki_sync.utils import import_apkg_to_anki_collection
            import_result = import_apkg_to_anki_collection(
                user=request.user,
                apkg_path=output_path
            )
            logger.info(f"Колода импортирована в базу синхронизации: {import_result}")
        except Exception as e:
            # Не прерываем выполнение, если импорт не удался
            logger.warning(f"Не удалось импортировать колоду в базу синхронизации: {str(e)}")
        
        return Response({
            'file_id': str(generated_deck.id),
            'message': 'Колода успешно сгенерирована'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при генерации колоды: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== ЭТАП 9: Система токенов ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_token_balance_view(request):
    """
    Получение баланса токенов пользователя
    """
    try:
        balance_internal = check_balance(request.user)
        # Конвертируем из внутреннего формата (где 2 = 1 токен) в реальные токены для отображения
        balance_display = balance_internal / 2.0
        return Response({
            'balance': balance_display
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Ошибка при получении баланса: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_token_transactions_view(request):
    """
    Получение истории транзакций токенов пользователя
    """
    from .models import TokenTransaction
    
    try:
        # Оптимизация: используем select_related для user (хотя это не нужно, так как user уже известен)
        transactions = TokenTransaction.objects.filter(user=request.user)[:50]  # Последние 50 транзакций
        
        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                'id': transaction.id,
                'transaction_type': transaction.transaction_type,
                'transaction_type_display': transaction.get_transaction_type_display(),
                'amount': transaction.amount,
                'description': transaction.description,
                'created_at': transaction.created_at
            })
        
        return Response({
            'transactions': transactions_data,
            'count': len(transactions_data)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Ошибка при получении транзакций: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_tokens_view(request):
    """
    Начисление токенов (только для администраторов)
    """
    from rest_framework.permissions import IsAdminUser
    
    if not request.user.is_staff:
        return Response({
            'error': 'Только администраторы могут начислять токены'
        }, status=status.HTTP_403_FORBIDDEN)
    
    amount = request.data.get('amount')
    description = request.data.get('description', '')
    user_id = request.data.get('user_id')
    
    # Преобразуем amount в int
    try:
        amount = int(amount) if amount else 0
    except (ValueError, TypeError):
        return Response({
            'error': 'Количество токенов должно быть числом'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not amount or amount <= 0:
        return Response({
            'error': 'Количество токенов должно быть положительным числом'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not user_id:
        return Response({
            'error': 'Необходимо указать user_id'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        target_user = UserModel.objects.get(id=user_id)
        
        # amount уже в токенах, add_tokens конвертирует в внутренний формат
        token = add_tokens(
            target_user,
            amount,  # Передаем как есть, функция сама конвертирует
            description or f"Начислено администратором {request.user.username}"
        )
        
        # Конвертируем баланс для отображения (из внутреннего формата)
        balance_display = token.balance / 2.0
        
        return Response({
            'message': f'Начислено {amount} токенов пользователю {target_user.username}',
            'balance': balance_display
        }, status=status.HTTP_200_OK)
    except UserModel.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Ошибка при начислении токенов: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_invert_all_words_view(request, deck_id):
    """
    Инвертирование всех слов в колоде
    
    Создает инвертированные версии всех слов колоды:
    - original_word и translation меняются местами
    - language меняется на source_lang колоды
    - Медиафайлы остаются теми же
    - Инвертированные слова добавляются в ту же колоду
    """
    deck = get_object_or_404(
        Deck.objects.select_related('user').prefetch_related('words'),
        id=deck_id,
        user=request.user
    )
    
    words = deck.words.all()
    if not words.exists():
        return Response({
            'error': 'Колода пуста'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    inverted_words = []
    skipped_words = []
    errors = []
    
    for word in words:
        try:
            # Создаем инвертированное слово
            # original_word становится translation, translation становится original_word
            # language становится source_lang колоды
            inverted_original = word.translation
            inverted_translation = word.original_word
            inverted_language = deck.source_lang
            
            # Используем update_or_create для обновления, если слово уже существует
            inverted_word, created = Word.objects.update_or_create(
                user=request.user,
                original_word=inverted_original,
                language=inverted_language,
                defaults={
                    'translation': inverted_translation,
                    'audio_file': word.audio_file,  # Используем те же медиафайлы
                    'image_file': word.image_file,
                }
            )
            
            # Добавляем инвертированное слово в колоду, если его там еще нет
            if inverted_word not in deck.words.all():
                deck.words.add(inverted_word)
                inverted_words.append({
                    'id': inverted_word.id,
                    'original_word': inverted_word.original_word,
                    'translation': inverted_word.translation,
                    'language': inverted_word.language,
                    'created': created
                })
            else:
                skipped_words.append({
                    'id': inverted_word.id,
                    'original_word': inverted_word.original_word,
                    'reason': 'Уже в колоде'
                })
                
        except Exception as e:
            errors.append({
                'word_id': word.id,
                'original_word': word.original_word,
                'error': str(e)
            })
            logger.error(f"Ошибка при инвертировании слова {word.id}: {str(e)}")
    
    logger.info(
        f"Инвертирование всех слов колоды {deck_id}: "
        f"создано {len(inverted_words)}, пропущено {len(skipped_words)}, ошибок {len(errors)}"
    )
    
    return Response({
        'message': f'Инвертировано {len(inverted_words)} слов',
        'deck_id': deck_id,
        'deck_name': deck.name,
        'inverted_words_count': len(inverted_words),
        'inverted_words': inverted_words,
        'skipped_words': skipped_words if skipped_words else None,
        'errors': errors if errors else None
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_invert_word_view(request, deck_id):
    """
    Инвертирование одного слова в колоде
    
    Создает инвертированную версию указанного слова:
    - original_word и translation меняются местами
    - language меняется на source_lang колоды
    - Медиафайлы остаются теми же
    - Инвертированное слово добавляется в колоду
    """
    deck = get_object_or_404(
        Deck.objects.select_related('user').prefetch_related('words'),
        id=deck_id,
        user=request.user
    )
    
    serializer = DeckInvertWordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word_id = serializer.validated_data['word_id']
    
    # Проверяем, что слово принадлежит колоде
    try:
        word = deck.words.get(id=word_id)
    except Word.DoesNotExist:
        return Response({
            'error': f'Слово с ID {word_id} не найдено в колоде'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # Создаем инвертированное слово
        inverted_original = word.translation
        inverted_translation = word.original_word
        inverted_language = deck.source_lang
        
        # Используем update_or_create для обновления, если слово уже существует
        inverted_word, created = Word.objects.update_or_create(
            user=request.user,
            original_word=inverted_original,
            language=inverted_language,
            defaults={
                'translation': inverted_translation,
                'audio_file': word.audio_file,  # Используем те же медиафайлы
                'image_file': word.image_file,
            }
        )
        
        # Добавляем инвертированное слово в колоду, если его там еще нет
        was_in_deck = inverted_word in deck.words.all()
        if not was_in_deck:
            deck.words.add(inverted_word)
        
        logger.info(
            f"Инвертирование слова {word_id} в колоде {deck_id}: "
            f"создано новое слово {inverted_word.id} (created={created}, was_in_deck={was_in_deck})"
        )
        
        return Response({
            'message': 'Слово успешно инвертировано',
            'original_word': {
                'id': word.id,
                'original_word': word.original_word,
                'translation': word.translation,
                'language': word.language
            },
            'inverted_word': {
                'id': inverted_word.id,
                'original_word': inverted_word.original_word,
                'translation': inverted_word.translation,
                'language': inverted_word.language,
                'created': created,
                'added_to_deck': not was_in_deck
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Ошибка при инвертировании слова {word_id}: {str(e)}")
        return Response({
            'error': f'Ошибка при инвертировании слова: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_create_empty_cards_view(request, deck_id):
    """
    Создание пустых карточек для всех слов в колоде
    
    Создает пустые карточки (original_word='') для всех слов колоды:
    - original_word = '' (пусто)
    - translation = '<слово на изучаемом языке> // <перевод>'
    - language = target_lang колоды (изучаемый язык)
    - Медиафайлы остаются теми же
    - Пустые карточки добавляются в ту же колоду
    """
    deck = get_object_or_404(
        Deck.objects.select_related('user').prefetch_related('words'),
        id=deck_id,
        user=request.user
    )
    
    words = deck.words.all()
    if not words.exists():
        return Response({
            'error': 'Колода пуста'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    empty_cards = []
    skipped_cards = []
    errors = []
    
    for word in words:
        try:
            # Создаем пустую карточку
            # original_word = '_empty_{word_id}' (уникальный идентификатор для пустой карточки)
            # translation = '<слово на изучаемом языке> // <перевод>'
            # language = target_lang колоды (изучаемый язык)
            # Используем уникальный идентификатор, чтобы избежать нарушения unique_together
            empty_original = f"_empty_{word.id}"
            empty_translation = f"{word.original_word} // {word.translation}"
            empty_language = deck.target_lang
            
            # Ищем существующую пустую карточку для этого слова
            # Используем уникальный original_word на основе word.id
            empty_card = Word.objects.filter(
                user=request.user,
                original_word=empty_original,
                language=empty_language
            ).first()
            
            if empty_card:
                # Обновляем медиафайлы и translation, если карточка уже существует
                empty_card.translation = empty_translation
                empty_card.audio_file = word.audio_file
                empty_card.image_file = word.image_file
                empty_card.save()
                created = False
            else:
                # Создаем новую пустую карточку
                empty_card = Word.objects.create(
                    user=request.user,
                    original_word=empty_original,
                    translation=empty_translation,
                    language=empty_language,
                    audio_file=word.audio_file,
                    image_file=word.image_file
                )
                created = True
            
            # Добавляем пустую карточку в колоду, если её там еще нет
            if empty_card not in deck.words.all():
                deck.words.add(empty_card)
                empty_cards.append({
                    'id': empty_card.id,
                    'original_word': empty_card.original_word,
                    'translation': empty_card.translation,
                    'language': empty_card.language,
                    'created': created
                })
            else:
                skipped_cards.append({
                    'id': empty_card.id,
                    'translation': empty_card.translation,
                    'reason': 'Уже в колоде'
                })
                
        except Exception as e:
            errors.append({
                'word_id': word.id,
                'original_word': word.original_word,
                'error': str(e)
            })
            logger.error(f"Ошибка при создании пустой карточки для слова {word.id}: {str(e)}")
    
    logger.info(
        f"Создание пустых карточек для колоды {deck_id}: "
        f"создано {len(empty_cards)}, пропущено {len(skipped_cards)}, ошибок {len(errors)}"
    )
    
    return Response({
        'message': f'Создано {len(empty_cards)} пустых карточек',
        'deck_id': deck_id,
        'deck_name': deck.name,
        'empty_cards_count': len(empty_cards),
        'empty_cards': empty_cards,
        'skipped_cards': skipped_cards if skipped_cards else None,
        'errors': errors if errors else None
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deck_create_empty_card_view(request, deck_id):
    """
    Создание пустой карточки для одного слова в колоде
    
    Создает пустую карточку (original_word='') для указанного слова:
    - original_word = '' (пусто)
    - translation = '<слово на изучаемом языке> // <перевод>'
    - language = target_lang колоды (изучаемый язык)
    - Медиафайлы остаются теми же
    - Пустая карточка добавляется в колоду
    """
    deck = get_object_or_404(
        Deck.objects.select_related('user').prefetch_related('words'),
        id=deck_id,
        user=request.user
    )
    
    serializer = DeckCreateEmptyCardSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    word_id = serializer.validated_data['word_id']
    
    # Проверяем, что слово принадлежит колоде
    try:
        word = deck.words.get(id=word_id)
    except Word.DoesNotExist:
        return Response({
            'error': f'Слово с ID {word_id} не найдено в колоде'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # Создаем пустую карточку
        # original_word = '_empty_{word_id}' (уникальный идентификатор для пустой карточки)
        # translation = '<слово на изучаемом языке> // <перевод>'
        # language = target_lang колоды (изучаемый язык)
        # Используем уникальный идентификатор, чтобы избежать нарушения unique_together
        empty_original = f"_empty_{word.id}"
        empty_translation = f"{word.original_word} // {word.translation}"
        empty_language = deck.target_lang
        
        # Ищем существующую пустую карточку для этого слова
        # Используем уникальный original_word на основе word.id
        empty_card = Word.objects.filter(
            user=request.user,
            original_word=empty_original,
            language=empty_language
        ).first()
        
        if empty_card:
            # Обновляем медиафайлы и translation, если карточка уже существует
            empty_card.translation = empty_translation
            empty_card.audio_file = word.audio_file
            empty_card.image_file = word.image_file
            empty_card.save()
            created = False
        else:
            # Создаем новую пустую карточку
            empty_card = Word.objects.create(
                user=request.user,
                original_word=empty_original,
                translation=empty_translation,
                language=empty_language,
                audio_file=word.audio_file,
                image_file=word.image_file
            )
            created = True
        
        # Добавляем пустую карточку в колоду, если её там еще нет
        was_in_deck = empty_card in deck.words.all()
        if not was_in_deck:
            deck.words.add(empty_card)
        
        logger.info(
            f"Создание пустой карточки для слова {word_id} в колоде {deck_id}: "
            f"создана карточка {empty_card.id} (created={created}, was_in_deck={was_in_deck})"
        )
        
        return Response({
            'message': 'Пустая карточка успешно создана',
            'original_word': {
                'id': word.id,
                'original_word': word.original_word,
                'translation': word.translation,
                'language': word.language
            },
            'empty_card': {
                'id': empty_card.id,
                'original_word': empty_card.original_word,
                'translation': empty_card.translation,
                'language': empty_card.language,
                'created': created,
                'added_to_deck': not was_in_deck
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Ошибка при создании пустой карточки для слова {word_id}: {str(e)}")
        return Response({
            'error': f'Ошибка при создании пустой карточки: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
