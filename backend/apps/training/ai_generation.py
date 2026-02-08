"""
Функции генерации контента через AI (этимология, подсказки, предложения, синонимы)
"""
import json
import re
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Union
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.cards.token_utils import check_balance, spend_tokens
from apps.cards.llm_utils import get_openai_client
from apps.words.models import Word, WordRelation
from apps.cards.models import Card
from .prompts import (
    get_etymology_prompt,
    get_hint_prompt,
    get_sentence_prompt,
    get_synonym_prompt,
    format_prompt
)

User = get_user_model()
logger = logging.getLogger(__name__)


# Стоимость операций (в токенах)
ETYMOLOGY_COST = 1
HINT_TEXT_COST = 1
HINT_AUDIO_COST = 1  # Если используется OpenAI TTS
SENTENCE_COST = 1  # Для 1-5 предложений
SYNONYM_COST = 1


def generate_etymology(
    word: str,
    translation: str,
    language: str,
    user: User,
    force_regenerate: bool = False
) -> str:
    """
    Генерирует этимологию слова через AI
    
    Args:
        word: Исходное слово (на изучаемом языке)
        translation: Перевод слова (на родном языке)
        language: Язык слова (ru, en, de, es, fr, it, pt, tr)
        user: Пользователь (для проверки баланса и пользовательского промпта)
        force_regenerate: Перегенерировать, даже если уже есть этимология
    
    Returns:
        Строка с этимологией
    
    Raises:
        ValueError: Недостаточно токенов или неверные параметры
        Exception: Ошибка при вызове AI API
    """
    if not word or not translation or not language:
        raise ValueError("word, translation и language обязательны")
    
    # Проверка баланса
    balance = check_balance(user)
    if balance < ETYMOLOGY_COST:
        raise ValueError(f"Недостаточно токенов. Требуется: {ETYMOLOGY_COST} токен(ов), баланс: {balance} токен(ов)")
    
    # Определяем родной язык пользователя для объяснения
    from apps.cards.language_utils import LANGUAGE_NAMES
    native_lang_code = getattr(user, 'native_language', 'ru') or 'ru'
    native_language = LANGUAGE_NAMES.get(native_lang_code, 'Russian')
    
    logger.info(f"Генерация этимологии для слова '{word}' ({language}) пользователя {user.username}")
    
    try:
        # Получаем промпт
        prompt_template = get_etymology_prompt(user)
        prompt = format_prompt(
            prompt_template,
            word=word,
            translation=translation,
            language=language,
            native_language=native_language
        )
        
        # Получаем клиент OpenAI
        client = get_openai_client()
        
        # Вызываем LLM API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Ты помощник для объяснения этимологии слов. Отвечай точно и информативно на языке {native_language}."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        etymology = response.choices[0].message.content.strip()
        
        # Валидация: проверяем, что ответ не пустой
        if not etymology or len(etymology) < 10:
            raise ValueError("Получена пустая или слишком короткая этимология")
        
        # Списание токенов
        token, success = spend_tokens(
            user,
            ETYMOLOGY_COST,
            f"Генерация этимологии для слова '{word}'"
        )
        
        if not success:
            raise ValueError("Не удалось списать токены")
        
        logger.info(f"✅ Сгенерирована этимология для слова '{word}': {etymology[:50]}...")
        return etymology
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации этимологии для слова '{word}': {str(e)}")
        raise Exception(f"Ошибка при генерации этимологии: {str(e)}")


def generate_hint(
    word: str,
    translation: str,
    language: str,
    user: User,
    generate_audio: bool = True,
    force_regenerate: bool = False
) -> Tuple[str, Optional[str]]:
    """
    Генерирует текстовую и аудио подсказку
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова
        user: Пользователь
        generate_audio: Генерировать аудио подсказку
        force_regenerate: Перегенерировать, даже если уже есть подсказка
    
    Returns:
        Tuple[строка с текстовой подсказкой, путь к аудио файлу или None]
    
    Raises:
        ValueError: Недостаточно токенов
        Exception: Ошибка при генерации
    """
    if not word or not translation or not language:
        raise ValueError("word, translation и language обязательны")
    
    # Проверка баланса (текст + аудио)
    total_cost = HINT_TEXT_COST
    if generate_audio:
        total_cost += HINT_AUDIO_COST
    
    balance = check_balance(user)
    if balance < total_cost:
        raise ValueError(f"Недостаточно токенов. Требуется: {total_cost} токен(ов), баланс: {balance} токен(ов)")
    
    logger.info(f"Генерация подсказки для слова '{word}' ({language}) пользователя {user.username}")
    
    try:
        # 1. Генерация текстовой подсказки
        prompt_template = get_hint_prompt(user)
        prompt = format_prompt(
            prompt_template,
            word=word,
            translation=translation,
            language=language
        )
        
        client = get_openai_client()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Ты помощник для создания подсказок к словам. Отвечай на языке {language}. НЕ упоминай само слово и его перевод."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=150
        )
        
        hint_text = response.choices[0].message.content.strip()
        
        # Валидация
        if not hint_text or len(hint_text) < 10:
            raise ValueError("Получена пустая или слишком короткая подсказка")
        
        # Проверяем, что подсказка не содержит само слово и перевод
        word_lower = word.lower()
        translation_lower = translation.lower()
        hint_lower = hint_text.lower()
        
        if word_lower in hint_lower or translation_lower in hint_lower:
            logger.warning(f"Подсказка содержит слово или перевод, но продолжаем: '{hint_text}'")
        
        # Списание токенов за текст
        token, success = spend_tokens(
            user,
            HINT_TEXT_COST,
            f"Генерация текстовой подсказки для слова '{word}'"
        )
        
        if not success:
            raise ValueError("Не удалось списать токены")
        
        # 2. Генерация аудио подсказки (если требуется)
        hint_audio_path = None
        if generate_audio:
            try:
                # Генерируем аудио через существующую функцию
                # Используем OpenAI TTS для генерации аудио из текста подсказки
                from apps.cards.llm_utils import generate_audio_with_openai_tts
                from pathlib import Path
                from django.conf import settings
                import uuid
                
                # Создаем клиент OpenAI
                client = get_openai_client()
                
                # Генерируем аудио через OpenAI TTS-1-HD
                response = client.audio.speech.create(
                    model="tts-1-hd",
                    voice="nova",  # Используем мягкий голос
                    input=hint_text,
                )
                
                # Получаем аудио данные
                audio_data = response.content
                
                # Генерируем уникальное имя файла
                file_id = str(uuid.uuid4())
                filename = f"{file_id}.mp3"
                
                # Сохраняем аудио в папку hints/
                media_root = Path(settings.MEDIA_ROOT)
                hints_dir = media_root / "hints"
                hints_dir.mkdir(parents=True, exist_ok=True)
                
                audio_path = hints_dir / filename
                
                # Сохраняем аудиофайл
                with open(audio_path, 'wb') as f:
                    f.write(audio_data)
                
                hint_audio_path = str(audio_path)
                
                # Списание токенов за аудио (1 токен = 2 единицы)
                token, success = spend_tokens(
                    user,
                    HINT_AUDIO_COST,
                    f"Генерация аудио подсказки для слова '{word}'"
                )
                
                if not success:
                    logger.warning(f"Не удалось списать токены за аудио подсказки")
                
            except Exception as e:
                logger.warning(f"Не удалось сгенерировать аудио для подсказки: {str(e)}")
                # Не выбрасываем ошибку, просто возвращаем текст без аудио
        
        logger.info(f"✅ Сгенерирована подсказка для слова '{word}': {hint_text[:50]}...")
        return hint_text, hint_audio_path
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации подсказки для слова '{word}': {str(e)}")
        raise Exception(f"Ошибка при генерации подсказки: {str(e)}")


def generate_sentence(
    word: str,
    translation: str,
    language: str,
    user: User,
    context: Optional[str] = None,
    count: int = 1
) -> Union[str, List[str]]:
    """
    Генерирует пример(ы) предложения с использованием слова
    
    Args:
        word: Исходное слово
        translation: Перевод слова
        language: Язык слова
        user: Пользователь
        context: Дополнительный контекст (например, "формальное общение", "разговорная речь")
        count: Количество предложений (1-5)
    
    Returns:
        Если count=1: строка с предложением
        Если count>1: список строк с предложениями
    
    Raises:
        ValueError: Недостаточно токенов или неверный count
        Exception: Ошибка при генерации
    """
    if not word or not translation or not language:
        raise ValueError("word, translation и language обязательны")
    
    if count < 1 or count > 5:
        raise ValueError("count должен быть от 1 до 5")
    
    # Проверка баланса
    balance = check_balance(user)
    if balance < SENTENCE_COST:
        raise ValueError(f"Недостаточно токенов. Требуется: {SENTENCE_COST} токен(ов), баланс: {balance} токен(ов)")
    
    logger.info(f"Генерация {count} предложения(й) для слова '{word}' ({language}) пользователя {user.username}")
    
    try:
        # Получаем промпт
        prompt_template = get_sentence_prompt(user)
        context_text = context or "вседневное общение"
        prompt = format_prompt(
            prompt_template,
            word=word,
            translation=translation,
            language=language,
            count=count,
            context=context_text
        )
        
        client = get_openai_client()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Ты помощник для создания примеров предложений. Отвечай на языке {language}. Только предложения, без нумерации и комментариев."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=200 if count <= 3 else 300
        )
        
        content = response.choices[0].message.content.strip()
        
        # Парсим предложения (разделяем по строкам)
        sentences = [s.strip() for s in content.split('\n') if s.strip()]
        
        # Фильтруем пустые строки и строки с номерами/маркерами
        sentences = [
            re.sub(r'^[\d\.\-\*\)]+[\s]*', '', s).strip()  # Убираем номера, маркеры
            for s in sentences
            if s and len(s) > 3  # Минимальная длина предложения
        ]
        
        # Валидация: проверяем, что предложения содержат слово
        word_lower = word.lower()
        valid_sentences = [
            s for s in sentences
            if word_lower in s.lower()
        ]
        
        if not valid_sentences:
            # Если ни одно предложение не содержит слово, используем все предложения
            # (возможно, слово в другой форме)
            valid_sentences = sentences
        
        if not valid_sentences:
            raise ValueError("Не удалось сгенерировать валидные предложения")
        
        # Ограничиваем количество
        valid_sentences = valid_sentences[:count]
        
        # Списание токенов
        token, success = spend_tokens(
            user,
            SENTENCE_COST,
            f"Генерация {count} предложения(й) для слова '{word}'"
        )
        
        if not success:
            raise ValueError("Не удалось списать токены")
        
        # Возвращаем результат
        if count == 1:
            logger.info(f"✅ Сгенерировано предложение для слова '{word}': {valid_sentences[0][:50]}...")
            return valid_sentences[0]
        else:
            logger.info(f"✅ Сгенерировано {len(valid_sentences)} предложения(й) для слова '{word}'")
            return valid_sentences
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации предложения для слова '{word}': {str(e)}")
        raise Exception(f"Ошибка при генерации предложения: {str(e)}")


def generate_synonym_word(
    word: Word,
    user: User,
    create_card: bool = True
) -> Word:
    """
    Генерирует и создаёт новое слово-синоним
    
    Args:
        word: Исходное слово
        user: Пользователь
        create_card: Создать автоматически normal карточку для нового слова
    
    Returns:
        Объект Word (новое слово-синоним)
    
    Raises:
        ValueError: Недостаточно токенов или слово уже существует
        Exception: Ошибка при генерации
    
    Note:
        Автоматически создаёт двустороннюю связь через WordRelation
    """
    if word.user_id != user.id:
        raise ValueError("Слово не принадлежит пользователю")
    
    # Проверка баланса (синоним + автоматическая этимология)
    total_cost = SYNONYM_COST + ETYMOLOGY_COST  # 2 токена всего
    balance = check_balance(user)
    if balance < total_cost:
        raise ValueError(f"Недостаточно токенов. Требуется: {total_cost} токен(ов), баланс: {balance} токен(ов)")
    
    # Для инвертированных слов используем правильные поля
    if word.card_type == 'inverted':
        target_word = word.translation         # Изучаемое слово
        target_translation = word.original_word  # Перевод на родной язык
        target_language = getattr(user, 'learning_language', word.language)
        logger.info(
            f"Генерация синонима для инвертированного слова: "
            f"используем '{target_word}' ({target_language}) вместо '{word.original_word}' ({word.language})"
        )
    else:
        target_word = word.original_word
        target_translation = word.translation
        target_language = word.language
    
    logger.info(f"Генерация синонима для слова '{target_word}' ({target_language}) пользователя {user.username}")
    
    try:
        # 1. Генерация синонима через LLM
        prompt_template = get_synonym_prompt(user)
        prompt = format_prompt(
            prompt_template,
            word=target_word,
            translation=target_translation,
            language=target_language
        )
        
        client = get_openai_client()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Ты помощник для поиска синонимов. Отвечай ТОЛЬКО в формате: СИНОНИМ|ПЕРЕВОД_СИНОНИМА"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        content = response.choices[0].message.content.strip()
        
        # Парсим ответ (формат: СИНОНИМ|ПЕРЕВОД)
        if '|' not in content:
            # Пытаемся найти разделитель
            if '\n' in content:
                content = content.split('\n')[0]
            raise ValueError(f"Неверный формат ответа от LLM: {content}")
        
        synonym_word, synonym_translation = content.split('|', 1)
        synonym_word = synonym_word.strip()
        synonym_translation = synonym_translation.strip()
        
        if not synonym_word or not synonym_translation:
            raise ValueError("Получен пустой синоним или перевод")
        
        # 2. Проверяем, что слово не существует у пользователя
        existing_word = Word.objects.filter(
            user=user,
            original_word=synonym_word,
            language=target_language
        ).first()
        
        if existing_word:
            # Если слово уже существует, просто создаём связь
            logger.info(f"Слово '{synonym_word}' уже существует, создаём связь")
            WordRelation.create_bidirectional(word, existing_word, 'synonym')
            return existing_word
        
        # 3. Создаём новое слово
        new_word = Word.objects.create(
            user=user,
            original_word=synonym_word,
            translation=synonym_translation,
            language=target_language,
            part_of_speech=word.part_of_speech if word.part_of_speech else '',
            learning_status='new'
        )
        
        # 4. Автоматическая генерация этимологии
        try:
            etymology = generate_etymology(
                word=synonym_word,
                translation=synonym_translation,
                language=target_language,
                user=user
            )
            new_word.etymology = etymology
            new_word.save(update_fields=['etymology'])
        except Exception as e:
            logger.warning(f"Не удалось сгенерировать этимологию для синонима '{synonym_word}': {str(e)}")
            # Продолжаем без этимологии
        
        # 5. Создаём двустороннюю связь
        WordRelation.create_bidirectional(word, new_word, 'synonym')
        
        # 6. Создаём normal карточку (если требуется)
        if create_card:
            try:
                Card.create_from_word(new_word, user)
            except Exception as e:
                logger.warning(f"Не удалось создать карточку для синонима '{synonym_word}': {str(e)}")
        
        # 7. Списание токенов за синоним
        token, success = spend_tokens(
            user,
            SYNONYM_COST,
            f"Генерация синонима '{synonym_word}' для слова '{target_word}'"
        )
        
        if not success:
            logger.warning(f"Не удалось списать токены за синоним, но слово создано")
        
        logger.info(f"Создано слово-синоним '{synonym_word}' для слова '{target_word}'")
        return new_word
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации синонима для слова '{target_word}': {str(e)}")
        raise Exception(f"Ошибка при генерации синонима: {str(e)}")
