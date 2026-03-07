"""
Scene image generation for literary context.
Reuses DALL-E pattern from cards/llm_utils.py.
"""
import io
import uuid
import logging
from pathlib import Path
from typing import Optional

import requests
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile

from apps.cards.llm_utils import get_openai_client
from .models import SceneAnchor, LiteraryContextSettings

logger = logging.getLogger(__name__)


def generate_scene_image(
    anchor: SceneAnchor,
    config: Optional[LiteraryContextSettings] = None,
) -> str:
    """
    Generate a scene image for a SceneAnchor using DALL-E.

    Args:
        anchor: SceneAnchor instance.
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

    client = get_openai_client()

    response = client.images.generate(
        model='dall-e-3',
        prompt=prompt,
        size='1024x1024',
        quality='standard',
        n=1,
    )

    image_url = response.data[0].url

    # Download image
    image_response = requests.get(image_url)
    image_response.raise_for_status()

    # Validate then re-open (verify() invalidates the image object)
    image = Image.open(io.BytesIO(image_response.content))
    image.verify()
    image = Image.open(io.BytesIO(image_response.content))

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

    return relative_path
