"""
Scene image generation for literary context.
Uses Gemini (gemini-2.5-flash-image) for image generation.
"""
import io
import uuid
import logging
from pathlib import Path
from typing import Optional

from PIL import Image
from django.conf import settings

from .models import SceneAnchor, LiteraryContextSettings

logger = logging.getLogger(__name__)


def generate_scene_image(
    anchor: SceneAnchor,
    config: Optional[LiteraryContextSettings] = None,
) -> str:
    """
    Generate a scene image for a SceneAnchor using Gemini.

    Args:
        anchor: SceneAnchor instance with scene_description filled.
        config: Settings (loaded from DB if None).

    Returns:
        Relative path to the saved image file.
    """
    config = config or LiteraryContextSettings.get()

    # Build prompt
    prompt = config.image_prompt_template.format(
        scene_description=anchor.scene_description
    )

    # Add character/mood context
    if anchor.characters:
        chars = ', '.join(anchor.characters)
        prompt += f' Characters present: {chars}.'
    if anchor.mood and anchor.mood != 'neutral':
        prompt += f' Mood: {anchor.mood}.'

    # Use Gemini for image generation
    try:
        import google.generativeai as genai
    except ImportError:
        raise ValueError("google-generativeai not installed")

    from apps.core.llm import get_gemini_client
    get_gemini_client()  # ensures genai is configured

    model = genai.GenerativeModel('gemini-3.1-flash-image-preview')
    response = model.generate_content(
        prompt,
        generation_config={'temperature': 0.4},
    )

    if not response.candidates or not response.candidates[0].content.parts:
        raise Exception("Gemini did not return an image")

    # Extract image data from response
    image_data = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'inline_data') and part.inline_data:
            image_data = part.inline_data.data
            break
        elif hasattr(part, 'image') and part.image:
            if hasattr(part.image, 'data'):
                image_data = part.image.data

    if not image_data:
        raise Exception("Could not extract image from Gemini response")

    # Validate
    image = Image.open(io.BytesIO(image_data))
    image.verify()
    image = Image.open(io.BytesIO(image_data))

    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Save
    file_id = str(uuid.uuid4())
    filename = f'{file_id}.jpg'

    media_root = Path(settings.MEDIA_ROOT)
    scenes_dir = media_root / 'literary_scenes'
    scenes_dir.mkdir(parents=True, exist_ok=True)

    file_path = scenes_dir / filename
    image.save(file_path, 'JPEG', quality=95)

    # Update anchor
    relative_path = f'literary_scenes/{filename}'
    anchor.image_file = relative_path
    anchor.image_prompt = prompt
    anchor.is_generated = True
    anchor.save(update_fields=['image_file', 'image_prompt', 'is_generated'])

    logger.info(f'Scene image generated for anchor {anchor.id}: {relative_path}')
    return relative_path
