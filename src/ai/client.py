import logging
from functools import lru_cache

from fastapi import HTTPException, status

import json

from src.ai.prompts import DRESS_VISION_PROMPT, OUTFIT_DESCRIPTION_PROMPT
from src.ai.schemas import DressCatalogItem, DressVisionMultiResult, OutfitDescriptionResult
from src.dress.models import Dress
from src.core.config import config

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client():
    if not config.google_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GOOGLE_API_KEY is not configured",
        )
    try:
        from google import genai
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="google-genai package is not installed",
        ) from exc
    return genai.Client(api_key=config.google_api_key)


async def analyze_image(
    image_bytes: bytes, mime_type: str
) -> DressVisionMultiResult:
    """Send a single image to Gemma and return structured vision metadata."""
    client = _get_client()

    from google.genai import types

    response = await client.aio.models.generate_content(
        model=config.gemma_model_id,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            DRESS_VISION_PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DressVisionMultiResult,
        ),
    )

    text = response.text.replace('`', '') or ""
    if not text:
        raise ValueError("Empty response from model")

    try:
        return DressVisionMultiResult.model_validate_json(text)
    except ValueError as exc:
        logger.error("Model returned invalid JSON: %s", text[:500])
        raise ValueError(f"Model returned invalid JSON: {exc}") from exc


async def describe_outfit(pieces: list[Dress]) -> OutfitDescriptionResult:
    """Generate outfit metadata from a set of wardrobe pieces."""
    client = _get_client()

    from google.genai import types

    catalog = [DressCatalogItem.from_dress(d) for d in pieces]
    user_prompt = (
        f"{OUTFIT_DESCRIPTION_PROMPT}\n\n"
        f"Pieces ({len(catalog)} items):\n"
        f"{json.dumps([c.model_dump(mode='json') for c in catalog], indent=2)}"
    )

    response = await client.aio.models.generate_content(
        model=config.gemma_model_id,
        contents=[user_prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OutfitDescriptionResult,
        ),
    )

    text = (response.text or "").replace("`", "")
    if not text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an empty outfit description response",
        )

    try:
        return OutfitDescriptionResult.model_validate_json(text)
    except ValueError as exc:
        logger.error("Outfit description invalid JSON: %s", text[:500])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI returned invalid outfit description JSON: {exc}",
        ) from exc
