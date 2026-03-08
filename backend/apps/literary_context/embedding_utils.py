"""
Embedding generation utilities for literary context semantic search.
"""
import logging
from typing import Optional

from apps.core.llm import get_openai_client
from .models import LiteraryContextSettings

logger = logging.getLogger(__name__)


def generate_embedding(
    text: str,
    config: Optional[LiteraryContextSettings] = None,
) -> list[float]:
    """
    Generate an embedding vector for a text using OpenAI embeddings API.

    Args:
        text: Text to embed.
        config: Settings (loaded from DB if None).

    Returns:
        List of floats (embedding vector).
    """
    config = config or LiteraryContextSettings.get()
    client = get_openai_client()

    response = client.embeddings.create(
        model=config.embedding_model,
        input=text,
        dimensions=config.embedding_dimensions,
    )

    return response.data[0].embedding


def generate_embeddings_batch(
    texts: list[str],
    config: Optional[LiteraryContextSettings] = None,
    batch_size: int = 100,
) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in batches.

    Args:
        texts: List of texts to embed.
        config: Settings (loaded from DB if None).
        batch_size: Max texts per API call.

    Returns:
        List of embedding vectors (same order as input texts).
    """
    if not texts:
        return []

    config = config or LiteraryContextSettings.get()
    client = get_openai_client()

    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        response = client.embeddings.create(
            model=config.embedding_model,
            input=batch,
            dimensions=config.embedding_dimensions,
        )

        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        all_embeddings.extend([item.embedding for item in sorted_data])

    return all_embeddings
