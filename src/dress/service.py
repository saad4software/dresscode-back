import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.ai.client import analyze_image
from src.auth.models import User
from src.core.models import IPageResponse
from src.core.pagination import paginate
from src.dress.models import (
    Category,
    Dress,
    DressCreate,
    DressStatus,
    DressUpdate,
    Season,
)
from src.media.models import Media, ProcessingStatus
from src.media.service import MediaService

logger = logging.getLogger(__name__)


class DressService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User, data: DressCreate) -> Dress:
        dress = Dress(
            user_id=user.id,
            **data.model_dump(exclude_unset=False),
        )
        self.session.add(dress)
        await self.session.commit()
        await self.session.refresh(dress)
        return dress

    async def create_from_image(
        self,
        user: User,
        file: UploadFile,
        media_service: MediaService,
    ) -> tuple[list[Dress], int]:
        """Upload an image, analyze it with Gemma, and create one dress per garment."""
        media = await media_service.upload(user, file)
        media_id = media.id
        storage_path = media.storage_path
        mime_type = media.mime_type

        try:
            image_bytes = Path(storage_path).read_bytes()
            vision_multi = await analyze_image(image_bytes, mime_type)
        except HTTPException:
            await media_service.delete(user, media_id)
            raise
        except Exception as exc:
            logger.exception(
                "AI analysis failed during dress create for media %s", media_id
            )
            await media_service.delete(user, media_id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI analysis failed: {exc}",
            ) from exc

        media = await media_service.get_for_user(user, media_id)
        dresses: list[Dress] = []

        for index, vision in enumerate(vision_multi.items):
            data = vision.to_dress_create()
            dress = Dress(user_id=user.id, **data.model_dump())
            vision.apply_ai_metadata(dress)
            dress.updated_at = dress.ai_processed_at or datetime.now(timezone.utc)
            self.session.add(dress)
            await self.session.flush()

            if index == 0:
                media.dress_id = dress.id
                media.processing_status = ProcessingStatus.completed
                media.processing_error = None
                self.session.add(media)
            else:
                await media_service.clone_for_dress(user, media, dress.id)

            dresses.append(dress)

        await self.session.commit()
        for dress in dresses:
            await self.session.refresh(dress)
        return dresses, media_id

    async def get_for_user(self, user: User, dress_id: int) -> Dress:
        dress = await self.session.get(Dress, dress_id)
        if dress is None or dress.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dress not found",
            )
        return dress

    async def list_for_user(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        category: Optional[Category] = None,
        archived: bool = False,
    ) -> IPageResponse[list[Dress]]:
        stmt = select(Dress).where(Dress.user_id == user.id)
        if not archived:
            stmt = stmt.where(Dress.is_archived == False)  # noqa: E712
        if category is not None:
            stmt = stmt.where(Dress.category == category)
        stmt = stmt.order_by(Dress.created_at.desc())
        return await paginate(self.session, stmt, page, page_size)

    async def update(
        self, user: User, dress_id: int, data: DressUpdate
    ) -> Dress:
        dress = await self.get_for_user(user, dress_id)
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(dress, field, value)
        dress.updated_at = datetime.now(timezone.utc)
        self.session.add(dress)
        await self.session.commit()
        await self.session.refresh(dress)
        return dress

    async def delete(self, user: User, dress_id: int) -> None:
        dress = await self.get_for_user(user, dress_id)
        # Unlink media so wardrobe photos remain in the library.
        result = await self.session.execute(
            select(Media).where(Media.dress_id == dress.id)
        )
        for media in result.scalars().all():
            media.dress_id = None
            self.session.add(media)
        await self.session.delete(dress)
        await self.session.commit()

    async def list_media(
        self,
        user: User,
        dress_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> IPageResponse[list[Media]]:
        await self.get_for_user(user, dress_id)
        stmt = (
            select(Media)
            .where(Media.dress_id == dress_id)
            .order_by(Media.sort_order, Media.id)
        )
        return await paginate(self.session, stmt, page, page_size)

    async def _all_media_for_dress(self, dress_id: int) -> Sequence[Media]:
        stmt = (
            select(Media)
            .where(Media.dress_id == dress_id)
            .order_by(Media.sort_order, Media.id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def link_media(
        self, user: User, dress_id: int, media_ids: list[int]
    ) -> Sequence[Media]:
        dress = await self.get_for_user(user, dress_id)
        if not media_ids:
            return await self._all_media_for_dress(dress.id)

        stmt = select(Media).where(
            Media.id.in_(media_ids), Media.user_id == user.id
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        if len(items) != len(set(media_ids)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more media items not found",
            )
        for media in items:
            media.dress_id = dress.id
            self.session.add(media)
        await self.session.commit()
        return await self._all_media_for_dress(dress.id)

    async def list_for_outfit_suggestion(
        self,
        user: User,
        season: Season,
        limit: int = 200,
    ) -> list[Dress]:
        """Load wardrobe items suitable for picking outfits in `season`.

        Returns only ready, non-archived dresses. The JSON list column
        `season_suitability` is filtered in Python because SQLite has no
        native array containment operator.
        """
        stmt = (
            select(Dress)
            .where(Dress.user_id == user.id)
            .where(Dress.is_archived == False)  # noqa: E712
            .where(Dress.status == DressStatus.ready)
            .order_by(Dress.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        dresses = list(result.scalars().all())

        def matches(d: Dress) -> bool:
            seasons = list(d.season_suitability or [])
            if not seasons:
                return True
            return season in seasons or Season.all_season in seasons

        return [d for d in dresses if matches(d)]

    async def mark_status(self, dress: Dress, new_status: DressStatus) -> None:
        dress.status = new_status
        dress.updated_at = datetime.now(timezone.utc)
        self.session.add(dress)
        await self.session.commit()
