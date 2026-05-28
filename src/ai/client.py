import logging
from functools import lru_cache

from fastapi import HTTPException, status

from src.ai.prompts import DRESS_VISION_PROMPT
from src.ai.schemas import DressVisionMultiResult
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

    text = response.text or ""
    if not text:
        raise ValueError("Empty response from model")

    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence (e.g., ```json or ```)
        text = text.lstrip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

        # Remove closing fence (```)
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        return DressVisionMultiResult.model_validate_json(text)
    except ValueError as exc:
        logger.error("Model returned invalid JSON: %s", text[:500])
        raise ValueError(f"Model returned invalid JSON: {exc}") from exc
