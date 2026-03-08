"""
AI service for training: etymology, hints, sentences, synonyms.

Wraps the AI generation functions with word resolution and response formatting.
"""
import logging
from pathlib import Path

from django.conf import settings

from apps.cards.token_utils import check_balance
from apps.words.models import Word
from apps.words.serializers import WordSerializer
from ..ai_generation import (
    generate_etymology,
    generate_hint,
    generate_sentence,
    generate_synonym_word,
)
from .session_service import _resolve_word_fields

logger = logging.getLogger(__name__)


def generate_etymology_for_word(user, word_id, force_regenerate=False):
    """
    Generate etymology for a word.

    Returns:
        dict with word_id, etymology, tokens_spent, balance_after.
    Raises:
        Word.DoesNotExist, ValueError, Exception.
    """
    word = Word.objects.get(id=word_id, user=user)

    if word.etymology and not force_regenerate:
        raise ValueError(
            'Этимология уже существует. Используйте force_regenerate=true для перегенерации'
        )

    target_word, target_translation, target_language = _resolve_word_fields(word, user)

    etymology = generate_etymology(
        word=target_word,
        translation=target_translation,
        language=target_language,
        user=user,
        force_regenerate=force_regenerate,
    )

    word.etymology = etymology
    word.save(update_fields=['etymology'])

    return {
        'word_id': word.id,
        'etymology': etymology,
        'tokens_spent': 1,
        'balance_after': check_balance(user),
    }


def generate_hint_for_word(user, word_id, force_regenerate=False, generate_audio=True):
    """
    Generate hint (text + optional audio) for a word.

    Returns:
        dict with word_id, hint_text, hint_audio_url, tokens_spent, balance_after.
    Raises:
        Word.DoesNotExist, ValueError, Exception.
    """
    word = Word.objects.get(id=word_id, user=user)

    if word.hint_text and not force_regenerate:
        hint_audio_url = word.hint_audio.url if word.hint_audio else None
        return {
            'word_id': word.id,
            'hint_text': word.hint_text,
            'hint_audio_url': hint_audio_url,
            'tokens_spent': 0,
            'balance_after': check_balance(user),
        }

    target_word, target_translation, target_language = _resolve_word_fields(word, user)

    hint_text, hint_audio_path = generate_hint(
        word=target_word,
        translation=target_translation,
        language=target_language,
        user=user,
        generate_audio=generate_audio,
        force_regenerate=force_regenerate,
    )

    word.hint_text = hint_text

    if hint_audio_path:
        audio_path = Path(hint_audio_path)
        if audio_path.is_absolute():
            media_root = Path(settings.MEDIA_ROOT)
            try:
                relative_path = audio_path.relative_to(media_root)
                word.hint_audio = str(relative_path)
            except ValueError:
                word.hint_audio = hint_audio_path
        else:
            word.hint_audio = hint_audio_path

    word.save(update_fields=['hint_text', 'hint_audio'])

    hint_audio_url = word.hint_audio.url if word.hint_audio else None
    tokens_spent = 2 if generate_audio and hint_audio_path else 1

    return {
        'word_id': word.id,
        'hint_text': hint_text,
        'hint_audio_url': hint_audio_url,
        'tokens_spent': tokens_spent,
        'balance_after': check_balance(user),
    }


def generate_sentences_for_word(user, word_id, count=1, context=None):
    """
    Generate example sentences for a word.

    Returns:
        dict with word_id, sentences, tokens_spent, balance_after.
    Raises:
        Word.DoesNotExist, ValueError, Exception.
    """
    word = Word.objects.get(id=word_id, user=user)

    target_word, target_translation, target_language = _resolve_word_fields(word, user)

    sentences_result = generate_sentence(
        word=target_word,
        translation=target_translation,
        language=target_language,
        user=user,
        context=context,
        count=count,
    )

    if isinstance(sentences_result, str):
        sentences_list = [sentences_result]
    else:
        sentences_list = sentences_result

    for sentence_text in sentences_list:
        word.add_sentence(sentence_text, source='ai')

    return {
        'word_id': word.id,
        'sentences': sentences_list,
        'tokens_spent': 1,
        'balance_after': check_balance(user),
    }


def generate_synonym_for_word(user, word_id, create_card=True):
    """
    Generate a synonym word.

    Returns:
        dict with original_word_id, synonym_word, relation_created,
        tokens_spent, balance_after.
    Raises:
        Word.DoesNotExist, ValueError, Exception.
    """
    word = Word.objects.get(id=word_id, user=user)

    synonym_word = generate_synonym_word(
        word=word,
        user=user,
        create_card=create_card,
    )

    synonym_data = WordSerializer(synonym_word).data

    return {
        'original_word_id': word.id,
        'synonym_word': synonym_data,
        'relation_created': True,
        'tokens_spent': 2,
        'balance_after': check_balance(user),
    }
