import uuid

from django.conf import settings
from django.db import models
from django.core.cache import cache

from apps.core.constants import LANGUAGE_CHOICES


class LiterarySource(models.Model):
    """A literary corpus: 'chekhov', 'bible', etc."""
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    cover = models.ImageField(upload_to='literary_sources/', null=True, blank=True)
    source_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    available_languages = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Literary Source'
        verbose_name_plural = 'Literary Sources'
        ordering = ['name']

    def __str__(self):
        return self.name


class LiteraryText(models.Model):
    """Individual work within a source (e.g. one story by Chekhov)."""
    source = models.ForeignKey(
        LiterarySource, on_delete=models.CASCADE, related_name='texts'
    )
    slug = models.SlugField(max_length=100)
    title = models.CharField(max_length=300)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    full_text = models.TextField()
    year = models.IntegerField(null=True, blank=True, help_text='Year of original publication')
    sort_order = models.IntegerField(default=0, help_text='Order within source for TOC')
    word_count = models.IntegerField(default=0, help_text='Approximate word count')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Literary Text'
        verbose_name_plural = 'Literary Texts'
        unique_together = [['source', 'slug', 'language']]
        ordering = ['source', 'slug', 'language']

    def __str__(self):
        return f"{self.title} ({self.language})"


MOOD_CHOICES = [
    ('comedic', 'Comedic'),
    ('dramatic', 'Dramatic'),
    ('calm', 'Calm'),
    ('tense', 'Tense'),
    ('melancholic', 'Melancholic'),
    ('joyful', 'Joyful'),
    ('mysterious', 'Mysterious'),
    ('romantic', 'Romantic'),
    ('dark', 'Dark'),
    ('neutral', 'Neutral'),
]


class SceneAnchor(models.Model):
    """Language-independent scene point. ONE image for ALL languages."""
    source = models.ForeignKey(
        LiterarySource, on_delete=models.CASCADE, related_name='scene_anchors'
    )
    text_slug = models.SlugField(max_length=100)
    fragment_index = models.IntegerField()
    scene_description = models.TextField(
        blank=True, default='',
        help_text='AI-generated scene description in English (for image prompt)'
    )
    characters = models.JSONField(
        default=list,
        help_text='Characters in the scene, Latin script: ["Ochumelov", "Khryukin"]'
    )
    mood = models.CharField(
        max_length=20, choices=MOOD_CHOICES, default='neutral'
    )
    image_file = models.ImageField(
        upload_to='literary_scenes/', null=True, blank=True
    )
    image_prompt = models.TextField(
        blank=True, default='',
        help_text='The actual prompt sent to DALL-E/Gemini'
    )
    is_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Scene Anchor'
        verbose_name_plural = 'Scene Anchors'
        unique_together = [['source', 'text_slug', 'fragment_index']]
        ordering = ['source', 'text_slug', 'fragment_index']

    def __str__(self):
        return f"{self.source.slug}/{self.text_slug} #{self.fragment_index}"


class LiteraryFragment(models.Model):
    """Language-dependent text fragment linked to a SceneAnchor."""
    anchor = models.ForeignKey(
        SceneAnchor, on_delete=models.CASCADE, related_name='fragments'
    )
    text = models.ForeignKey(
        LiteraryText, on_delete=models.CASCADE, related_name='fragments'
    )
    content = models.TextField(help_text='The actual text passage in this language')
    key_words = models.JSONField(
        default=list,
        help_text='Key words in this language: ["Hund", "Platz", "Menge"]'
    )
    embedding = models.JSONField(
        null=True, blank=True,
        help_text='Embedding vector as JSON list. Use pgvector VectorField in production.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Literary Fragment'
        verbose_name_plural = 'Literary Fragments'
        unique_together = [['anchor', 'text']]
        ordering = ['anchor__fragment_index']

    def __str__(self):
        return f"{self.text.title} [{self.anchor.fragment_index}] ({self.text.language})"


class WordContextMedia(models.Model):
    """Per-word, per-source literary context media."""
    word = models.ForeignKey(
        'words.Word', on_delete=models.CASCADE, related_name='context_media'
    )
    source = models.ForeignKey(
        LiterarySource, on_delete=models.CASCADE, related_name='word_media'
    )
    anchor = models.ForeignKey(
        SceneAnchor, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='word_media'
    )
    fragment = models.ForeignKey(
        LiteraryFragment, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='word_media'
    )

    # Generated content
    hint_text = models.TextField(blank=True, default='')
    hint_audio = models.FileField(
        upload_to='literary_hints/', null=True, blank=True
    )
    sentences = models.JSONField(
        default=list,
        help_text='Sentences from the literary work: [{"text": "...", "source": "chekhov"}]'
    )
    audio_file = models.FileField(
        upload_to='literary_audio/', null=True, blank=True
    )

    # Matching metadata
    is_fallback = models.BooleanField(
        default=False,
        help_text='True if no matching fragment found in the literary source'
    )
    match_method = models.CharField(
        max_length=20, blank=True, default='',
        help_text='How the word was matched: keyword, semantic, llm, fallback'
    )
    match_score = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Word Context Media'
        verbose_name_plural = 'Word Context Media'
        unique_together = [['word', 'source']]
        indexes = [
            models.Index(fields=['word', 'source']),
            models.Index(fields=['source', 'anchor']),
        ]

    def __str__(self):
        status = 'fallback' if self.is_fallback else self.match_method
        return f"{self.word} @ {self.source.slug} ({status})"


JOB_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('running', 'Running'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]


class DeckContextJob(models.Model):
    """Tracks async literary context generation for a deck."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deck = models.ForeignKey(
        'cards.Deck', on_delete=models.CASCADE, related_name='context_jobs'
    )
    source = models.ForeignKey(
        LiterarySource, on_delete=models.CASCADE, related_name='context_jobs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='context_jobs'
    )
    status = models.CharField(
        max_length=20, choices=JOB_STATUS_CHOICES, default='pending'
    )
    progress = models.IntegerField(default=0, help_text='0-100 percent')
    current_word = models.CharField(max_length=200, blank=True, default='')
    stats = models.JSONField(default=dict, blank=True)
    unmatched_words = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Deck Context Job'
        verbose_name_plural = 'Deck Context Jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id} [{self.status}] {self.deck} → {self.source.slug}"


SETTINGS_CACHE_KEY = 'literary_context_settings'
SETTINGS_CACHE_TIMEOUT = 300  # 5 minutes


class LiteraryContextSettings(models.Model):
    """Singleton configuration for all tunable parameters. Admin-editable."""

    # --- Matching thresholds ---
    semantic_match_min_score = models.FloatField(
        default=0.7,
        help_text='Minimum cosine similarity for semantic search (0.0-1.0)'
    )
    llm_match_enabled = models.BooleanField(
        default=True,
        help_text='Enable LLM-based matching as Tier C fallback'
    )

    # --- Prompt templates ---
    image_prompt_template = models.TextField(
        default=(
            "Illustration of a scene from a literary work: {scene_description}. "
            "Style: classic book illustration, warm tones, detailed. "
            "NO text, letters, words, signs, or symbols anywhere in the image."
        ),
        help_text='Template for scene image generation. Variables: {scene_description}'
    )
    hint_prompt_template = models.TextField(
        default=(
            "Based on this literary passage:\n{fragment_content}\n\n"
            "Create a short hint (1-2 sentences) for the word '{word}' "
            "that references this scene. "
            "Do NOT use the word itself or its translation '{translation}'. "
            "Write the hint in {language_name}."
        ),
        help_text='Template for hint generation. Variables: {fragment_content}, {word}, {translation}, {language_name}'
    )
    sentence_extraction_prompt = models.TextField(
        default=(
            "From the following literary passage, extract sentences that contain "
            "the word '{word}' (or its grammatical forms). Return only the sentences, "
            "one per line. If no sentences contain the word, return the most relevant "
            "sentence from the passage.\n\nPassage:\n{fragment_content}"
        ),
        help_text='Template for sentence extraction. Variables: {word}, {fragment_content}'
    )
    keyword_extraction_prompt = models.TextField(
        default=(
            "Extract key words from this text fragment. Return as a JSON array of strings. "
            "Include nouns, verbs, adjectives that describe the main objects, actions, "
            "and qualities in the scene. Return 5-15 words.\n\nText:\n{fragment_content}"
        ),
        help_text='Template for keyword extraction during indexing. Variables: {fragment_content}'
    )
    scene_description_prompt = models.TextField(
        default=(
            "Describe the visual scene from this literary passage in English. "
            "Focus on what can be SEEN: characters, their actions, surroundings, "
            "mood, lighting, colors. Keep it to 2-3 sentences. "
            "Also extract: 1) character names (Latin script), 2) scene mood.\n\n"
            "Return as JSON: {{\"description\": \"...\", \"characters\": [...], \"mood\": \"...\"}}\n\n"
            "Passage:\n{fragment_content}"
        ),
        help_text='Template for scene description generation. Variables: {fragment_content}'
    )

    # --- LLM model settings ---
    keyword_extraction_model = models.CharField(
        max_length=50, default='gpt-4o-mini',
        help_text='Model for keyword extraction during indexing'
    )
    scene_description_model = models.CharField(
        max_length=50, default='gpt-4o-mini',
        help_text='Model for scene description generation'
    )
    hint_generation_model = models.CharField(
        max_length=50, default='gpt-4o-mini',
        help_text='Model for hint text generation'
    )
    matching_model = models.CharField(
        max_length=50, default='gpt-4o',
        help_text='Model for Tier C LLM matching (complex cases)'
    )
    embedding_model = models.CharField(
        max_length=50, default='text-embedding-3-small',
        help_text='Model for generating embeddings'
    )
    embedding_dimensions = models.IntegerField(
        default=1536,
        help_text='Embedding vector dimensions'
    )

    # --- Token costs ---
    scene_image_cost = models.IntegerField(
        default=4, help_text='Token cost for scene image (internal units, 2=1 real token)'
    )
    hint_generation_cost = models.IntegerField(
        default=2, help_text='Token cost for hint text generation'
    )
    audio_generation_cost = models.IntegerField(
        default=2, help_text='Token cost for audio via ElevenLabs'
    )
    llm_matching_cost = models.IntegerField(
        default=2, help_text='Token cost for Tier C LLM matching'
    )

    # --- Fragment splitting settings ---
    default_fragment_size = models.IntegerField(
        default=500,
        help_text='Target fragment size in characters'
    )
    fragment_overlap = models.IntegerField(
        default=50,
        help_text='Overlap between fragments in characters'
    )

    # --- LLM generation parameters ---
    hint_temperature = models.FloatField(default=0.8)
    keyword_temperature = models.FloatField(default=0.3)
    scene_description_temperature = models.FloatField(default=0.5)
    matching_temperature = models.FloatField(default=0.2)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Literary Context Settings'
        verbose_name_plural = 'Literary Context Settings'

    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton
        super().save(*args, **kwargs)
        cache.delete(SETTINGS_CACHE_KEY)

    @classmethod
    def get(cls):
        cached = cache.get(SETTINGS_CACHE_KEY)
        if cached is not None:
            return cached
        obj, _ = cls.objects.get_or_create(pk=1)
        cache.set(SETTINGS_CACHE_KEY, obj, SETTINGS_CACHE_TIMEOUT)
        return obj

    def __str__(self):
        return 'Literary Context Settings'
