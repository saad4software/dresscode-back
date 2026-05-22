import logging

from src.ai.service import AIService
from src.core.dependencies import SessionLocal
from src.dress.models import Dress

logger = logging.getLogger(__name__)


async def analyze_dress_task(dress_id: int, user_id: int) -> None:
    """Background-task entry point: opens its own DB session.

    The request-scoped session is closed by the time FastAPI runs background
    tasks, so we open a fresh one here.
    """
    async with SessionLocal() as session:
        dress = await session.get(Dress, dress_id)
        if dress is None or dress.user_id != user_id:
            logger.warning(
                "analyze_dress_task: dress %s not found for user %s",
                dress_id,
                user_id,
            )
            return
        service = AIService(session)
        try:
            await service.analyze_dress(dress)
        except Exception:
            logger.exception("Background dress analysis failed for %s", dress_id)
