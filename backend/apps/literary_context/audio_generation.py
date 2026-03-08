"""
Audio generation for literary context.
Supports: ElevenLabs -> OpenAI TTS -> gTTS fallback chain.
"""
import io
import uuid
import logging
from pathlib import Path
from typing import Optional

from django.conf import settings as django_settings

from .models import LiteraryContextSettings

logger = logging.getLogger(__name__)

# Graceful ElevenLabs import
try:
    from elevenlabs import ElevenLabs
    HAS_ELEVENLABS = True
except ImportError:
    HAS_ELEVENLABS = False
    logger.info('elevenlabs not installed, ElevenLabs TTS unavailable')


# Language code to ElevenLabs voice ID mapping (defaults)
DEFAULT_VOICES = {
    'de': 'pNInz6obpgDQGcFmaJgB',  # Adam (German)
    'ru': 'ErXwobaYiN019PkySvjV',  # Antoni
    'en': '21m00Tcm4TlvDq8ikWAM',  # Rachel
    'pt': 'pNInz6obpgDQGcFmaJgB',  # Adam
    'es': 'pNInz6obpgDQGcFmaJgB',  # Adam
    'fr': 'pNInz6obpgDQGcFmaJgB',  # Adam
    'it': 'pNInz6obpgDQGcFmaJgB',  # Adam
    'tr': 'pNInz6obpgDQGcFmaJgB',  # Adam
}


def _save_audio_bytes(audio_bytes: bytes, subdir: str = 'literary_audio') -> str:
    """Save audio bytes to media and return relative path."""
    file_id = str(uuid.uuid4())
    filename = f'{file_id}.mp3'

    media_root = Path(django_settings.MEDIA_ROOT)
    audio_dir = media_root / subdir
    audio_dir.mkdir(parents=True, exist_ok=True)

    file_path = audio_dir / filename
    file_path.write_bytes(audio_bytes)

    return f'{subdir}/{filename}'


def generate_audio_elevenlabs(
    text: str,
    language: str,
    voice_id: Optional[str] = None,
) -> Optional[bytes]:
    """Generate audio via ElevenLabs API."""
    if not HAS_ELEVENLABS:
        return None

    import os
    api_key = os.environ.get('ELEVENLABS_API_KEY')
    if not api_key:
        logger.warning('ELEVENLABS_API_KEY not set')
        return None

    voice_id = voice_id or DEFAULT_VOICES.get(language, DEFAULT_VOICES['en'])

    try:
        client = ElevenLabs(api_key=api_key)
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id='eleven_multilingual_v2',
        )
        # audio is a generator of bytes
        return b''.join(audio)
    except Exception as e:
        logger.warning(f'ElevenLabs TTS failed: {e}')
        return None


def generate_audio_openai(text: str, language: str) -> Optional[bytes]:
    """Generate audio via OpenAI TTS."""
    try:
        from apps.core.llm import get_openai_client
        client = get_openai_client()

        response = client.audio.speech.create(
            model='tts-1',
            voice='alloy',
            input=text,
        )
        return response.content
    except Exception as e:
        logger.warning(f'OpenAI TTS failed: {e}')
        return None


def generate_audio_gtts(text: str, language: str) -> Optional[bytes]:
    """Generate audio via gTTS (Google TTS)."""
    try:
        from gtts import gTTS as _gTTS
        tts = _gTTS(text=text, lang=language)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception as e:
        logger.warning(f'gTTS failed: {e}')
        return None


def generate_literary_audio(
    text: str,
    language: str,
    voice_id: Optional[str] = None,
    subdir: str = 'literary_audio',
) -> Optional[str]:
    """
    Generate audio with fallback chain: ElevenLabs -> OpenAI TTS -> gTTS.

    Args:
        text: Text to speak.
        language: Language code.
        voice_id: Optional ElevenLabs voice ID override.
        subdir: Media subdirectory.

    Returns:
        Relative path to saved audio file, or None if all providers fail.
    """
    # Tier 1: ElevenLabs
    audio_bytes = generate_audio_elevenlabs(text, language, voice_id)
    if audio_bytes:
        return _save_audio_bytes(audio_bytes, subdir)

    # Tier 2: OpenAI TTS
    audio_bytes = generate_audio_openai(text, language)
    if audio_bytes:
        return _save_audio_bytes(audio_bytes, subdir)

    # Tier 3: gTTS
    audio_bytes = generate_audio_gtts(text, language)
    if audio_bytes:
        return _save_audio_bytes(audio_bytes, subdir)

    logger.error(f'All audio providers failed for text: {text[:50]}')
    return None
