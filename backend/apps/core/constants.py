"""
Общие константы проекта.

Единый источник истины для всех choices, стоимостей и магических чисел,
которые используются в нескольких приложениях.
"""

# ═══════════════════════════════════════════════════════════════
# Языки
# ═══════════════════════════════════════════════════════════════

LANGUAGE_CHOICES = [
    ('ru', 'Russian'),
    ('en', 'English'),
    ('pt', 'Portuguese'),
    ('de', 'German'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('it', 'Italian'),
    ('tr', 'Turkish'),
]

# Коды языков для быстрой валидации
LANGUAGE_CODES = {code for code, _ in LANGUAGE_CHOICES}


# ═══════════════════════════════════════════════════════════════
# Провайдеры и модели
# ═══════════════════════════════════════════════════════════════

IMAGE_PROVIDER_CHOICES = [
    ('openai', 'OpenAI DALL-E 3'),
    ('gemini', 'Google Gemini'),
]

AUDIO_PROVIDER_CHOICES = [
    ('elevenlabs', 'ElevenLabs'),
    ('openai', 'OpenAI TTS'),
    ('gtts', 'Google TTS (gTTS)'),
]

IMAGE_STYLE_CHOICES = [
    ('minimalistic', 'Минималистичный'),
    ('balanced', 'Сбалансированный'),
    ('creative', 'Креативный'),
]

GEMINI_MODEL_CHOICES = [
    ('gemini-2.5-flash-image', 'Gemini Flash (быстрая, 0.5 токена)'),
    ('gemini-3.1-flash-image-preview', 'NanoBanana-2 (новая, 1 токен)'),
]

MODE_CHOICES = [
    ('simple', 'Простой'),
    ('advanced', 'Расширенный'),
]

THEME_CHOICES = [
    ('light', 'Светлая'),
    ('dark', 'Темная'),
]


# ═══════════════════════════════════════════════════════════════
# Стоимости операций (в токенах)
# ═══════════════════════════════════════════════════════════════

# Медиа-генерация
IMAGE_GENERATION_COST = 1
AUDIO_GENERATION_COST = 1
PHOTO_OCR_COST = 1
IMAGE_EDIT_COST = 1

# Стоимость для разных моделей Gemini
GEMINI_FLASH_IMAGE_COST = 1  # gemini-2.5-flash-image (было 0.5 float — исправлено на int)
GEMINI_PRO_IMAGE_COST = 1    # gemini-3.1-flash-image-preview

# AI-генерация (training)
ETYMOLOGY_COST = 1
HINT_TEXT_COST = 1
HINT_AUDIO_COST = 1
SENTENCE_COST = 1
SYNONYM_COST = 1

# Стартовый баланс при регистрации
INITIAL_TOKEN_BALANCE = 100


# ═══════════════════════════════════════════════════════════════
# SM-2 константы
# ═══════════════════════════════════════════════════════════════

MAX_EASE_FACTOR = 5.0

# Оценка времени на карточку (в минутах)
TIME_PER_LEARNING_CARD = 1.5
TIME_PER_REVIEW_CARD = 0.25
TIME_PER_NEW_CARD = 0.5


# ═══════════════════════════════════════════════════════════════
# Типы карточек и статусы обучения
# ═══════════════════════════════════════════════════════════════

CARD_TYPE_CHOICES = [
    ('normal', 'Обычная карточка'),
    ('inverted', 'Инвертированная карточка'),
    ('empty', 'Пустая карточка'),
    ('cloze', 'Карточка-пропуск'),
]

LEARNING_STATUS_CHOICES = [
    ('new', 'Новое'),
    ('learning', 'В изучении'),
    ('reviewing', 'На повторении'),
    ('mastered', 'Освоено'),
]

PART_OF_SPEECH_CHOICES = [
    ('noun', 'Существительное'),
    ('verb', 'Глагол'),
    ('adjective', 'Прилагательное'),
    ('adverb', 'Наречие'),
    ('pronoun', 'Местоимение'),
    ('preposition', 'Предлог'),
    ('conjunction', 'Союз'),
    ('interjection', 'Междометие'),
    ('article', 'Артикль'),
    ('numeral', 'Числительное'),
    ('particle', 'Частица'),
    ('other', 'Другое'),
]
