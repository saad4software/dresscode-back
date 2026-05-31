import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.ai.client import analyze_image
from src.ai.schemas import DressVisionResult
from src.admin.models import DressCategory
from src.dress.models import Dress
from src.media.models import Media, ProcessingStatus

logger = logging.getLogger(__name__)


@dataclass
class AnalyzeResult:
    analyzed_media_ids: list[int] = field(default_factory=list)
    failed_media_ids: list[int] = field(default_factory=list)


class AIService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def analyze_dress(self, dress: Dress) -> AnalyzeResult:
        """Run vision analysis on every pending/failed media linked to the dress.

        Each image's parsed result is merged into the dress. Base fields are
        set from the first successful image; subsequent images only extend
        `colors` and `occasion_tags` so additional photos refine rather than
        overwrite.
        """
        result_query = await self.session.execute(
            select(Media)
            .where(Media.dress_id == dress.id)
            .order_by(Media.sort_order, Media.id)
        )
        media_items = list(result_query.scalars().all())

        if not media_items:
            return AnalyzeResult()

        pending = [
            m for m in media_items
            if m.processing_status in (ProcessingStatus.pending, ProcessingStatus.failed)
        ]
        if not pending:
            return AnalyzeResult()

        outcome = AnalyzeResult()
        first_success_applied = self._has_ai_data(dress)

        for media in pending:
            media.processing_status = ProcessingStatus.processing
            media.processing_error = None
            self.session.add(media)
        await self.session.commit()

        for media in pending:
            try:
                path = Path(media.storage_path)
                image_bytes = path.read_bytes()
                vision_multi = await analyze_image(image_bytes, media.mime_type)
                vision = vision_multi.items[0]
            except Exception as exc:
                logger.exception("AI analysis failed for media %s", media.id)
                media.processing_status = ProcessingStatus.failed
                media.processing_error = str(exc)[:500]
                self.session.add(media)
                outcome.failed_media_ids.append(media.id)
                continue

            if not first_success_applied:
                await self._apply_base_fields(dress, vision)
                vision.apply_ai_metadata(dress)
                first_success_applied = True
            self._merge_additional(dress, vision)

            media.processing_status = ProcessingStatus.completed
            media.processing_error = None
            self.session.add(media)
            outcome.analyzed_media_ids.append(media.id)

        if outcome.analyzed_media_ids:
            dress.updated_at = datetime.now(timezone.utc)
            self.session.add(dress)

        await self.session.commit()
        return outcome

    @staticmethod
    def _has_ai_data(dress: Dress) -> bool:
        return dress.ai_processed_at is not None

    async def _apply_base_fields(self, dress: Dress, vision: DressVisionResult) -> None:
        if not dress.item_name:
            dress.item_name = vision.item_name

        # Resolve category_id by querying the DressCategory model:
        stmt = select(DressCategory).where(DressCategory.slug == vision.category.value)
        res = await self.session.execute(stmt)
        cat = res.scalar_one_or_none()
        if cat:
            dress.category_id = cat.id

        dress.dominant_color = vision.dominant_color
        dress.warmth_level = vision.warmth_level
        dress.layering = vision.layering

        dress.description = vision.description
        dress.season_suitability = list(vision.season_suitability)
        dress.style = list(vision.style)
        dress.pattern = vision.pattern
        dress.material = vision.material
        dress.formality = vision.formality
        dress.brightness = vision.brightness
        dress.water_resistant = vision.water_resistant
        dress.ai_confidence = vision.confidence

    @staticmethod
    def _merge_additional(dress: Dress, vision: DressVisionResult) -> None:
        dress.colors = _merge_unique(dress.colors, vision.colors)
        dress.occasion_tags = _merge_unique(dress.occasion_tags, vision.occasion_tags)


def _merge_unique(existing: Iterable, incoming: Iterable) -> list:
    seen = set()
    out = []
    for item in list(existing) + list(incoming):
        key = item.value if hasattr(item, "value") else item
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
