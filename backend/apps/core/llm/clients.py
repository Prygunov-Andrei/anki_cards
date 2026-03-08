"""
Centralized LLM client creation for OpenAI and Gemini.

All apps should import clients from here instead of creating their own.
"""
import os
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

# Gemini import (optional)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    logger.warning("google-generativeai не установлен. Gemini API недоступен.")


def get_openai_client() -> OpenAI:
    """Create and return an OpenAI client."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
    return OpenAI(api_key=api_key)


def get_gemini_client():
    """Configure and return the Gemini API client module."""
    if not GEMINI_AVAILABLE:
        raise ValueError(
            "google-generativeai не установлен. Установите: pip install google-generativeai"
        )
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    genai.configure(api_key=api_key)
    return genai
