from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.auth.models import User
from src.core.models import IPageResponse
from src.core.pagination import paginate
from src.dress.models import Dress, DressRead
from src.dress.service import DressService
from src.event.models import Event
from src.media.service import MediaService
from src.outfit.models import (
    Outfit,
    OutfitCreate,
    OutfitRead,
    OutfitUpdate,
)


def outfit_to_read(outfit: Outfit) -> OutfitRead:
    return OutfitRead(
        id=outfit.id,
        user_id=outfit.user_id,
        name=outfit.name,
        color_harmony=outfit.color_harmony,
        reasoning=outfit.reasoning,
        event_id=outfit.event_id,
        pieces=[
            DressRead.model_validate(piece, from_attributes=True)
            for piece in outfit.pieces
        ],
        created_at=outfit.created_at,
        updated_at=outfit.updated_at,
    )


class OutfitService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _load_options(self):
        return selectinload(Outfit.pieces).selectinload(Dress.category_obj)

    async def _get_dresses_for_user(
        self, user: User, dress_ids: list[int]
    ) -> list[Dress]:
        if not dress_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one dress is required",
            )
        unique_ids = list(dict.fromkeys(dress_ids))
        stmt = (
            select(Dress)
            .where(Dress.id.in_(unique_ids), Dress.user_id == user.id)
            .options(selectinload(Dress.category_obj))
        )
        res = await self.session.execute(stmt)
        dresses = list(res.scalars().all())
        if len(dresses) != len(unique_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more dresses not found",
            )
        dresses_by_id = {dress.id: dress for dress in dresses}
        return [dresses_by_id[dress_id] for dress_id in unique_ids]

    async def _validate_event_for_user(
        self, user: User, event_id: Optional[int]
    ) -> None:
        if event_id is None:
            return
        event = await self.session.get(Event, event_id)
        if event is None or event.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

    async def _load_outfit(self, outfit_id: int) -> Outfit:
        stmt = (
            select(Outfit)
            .where(Outfit.id == outfit_id)
            .options(self._load_options())
        )
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def list_for_event(self, user: User, event_id: int) -> list[Outfit]:
        stmt = (
            select(Outfit)
            .where(Outfit.user_id == user.id, Outfit.event_id == event_id)
            .options(self._load_options())
            .order_by(Outfit.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def has_for_event(self, user: User, event_id: int) -> bool:
        stmt = select(
            exists().where(
                Outfit.user_id == user.id,
                Outfit.event_id == event_id,
            )
        )
        res = await self.session.execute(stmt)
        return bool(res.scalar())

    async def event_ids_with_suggestions(
        self, user: User, event_ids: list[int]
    ) -> set[int]:
        if not event_ids:
            return set()
        stmt = (
            select(Outfit.event_id)
            .where(
                Outfit.user_id == user.id,
                Outfit.event_id.in_(event_ids),
            )
            .distinct()
        )
        res = await self.session.execute(stmt)
        return set(res.scalars().all())

    async def list_for_user(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        event_id: Optional[int] = None,
    ) -> IPageResponse[list[Outfit]]:
        stmt = (
            select(Outfit)
            .where(Outfit.user_id == user.id)
            .options(self._load_options())
            .order_by(Outfit.created_at.desc())
        )
        if event_id is not None:
            stmt = stmt.where(Outfit.event_id == event_id)
        return await paginate(self.session, stmt, page, page_size)

    async def get_for_user(self, user: User, outfit_id: int) -> Outfit:
        stmt = (
            select(Outfit)
            .where(Outfit.id == outfit_id)
            .options(self._load_options())
        )
        res = await self.session.execute(stmt)
        outfit = res.scalar_one_or_none()
        if outfit is None or outfit.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Outfit not found",
            )
        return outfit

    async def create(self, user: User, data: OutfitCreate) -> Outfit:
        await self._validate_event_for_user(user, data.event_id)
        dresses = await self._get_dresses_for_user(user, data.dress_ids)

        outfit = Outfit(
            user_id=user.id,
            name=data.name,
            color_harmony=data.color_harmony,
            reasoning=data.reasoning,
            event_id=data.event_id,
            pieces=dresses,
        )
        self.session.add(outfit)
        await self.session.commit()
        return await self._load_outfit(outfit.id)

    async def update(
        self, user: User, outfit_id: int, data: OutfitUpdate
    ) -> Outfit:
        outfit = await self.get_for_user(user, outfit_id)
        updates = data.model_dump(exclude_unset=True)
        dress_ids = updates.pop("dress_ids", None)

        if "event_id" in updates:
            await self._validate_event_for_user(user, updates["event_id"])

        for field, value in updates.items():
            setattr(outfit, field, value)

        if dress_ids is not None:
            outfit.pieces = await self._get_dresses_for_user(user, dress_ids)

        outfit.updated_at = datetime.now(timezone.utc)
        self.session.add(outfit)
        await self.session.commit()
        return await self._load_outfit(outfit.id)

    async def delete(self, user: User, outfit_id: int) -> Outfit:
        outfit = await self.get_for_user(user, outfit_id)
        await self.session.delete(outfit)
        await self.session.commit()
        return outfit

    async def delete_for_event(self, user: User, event_id: int) -> None:
        stmt = select(Outfit).where(
            Outfit.user_id == user.id,
            Outfit.event_id == event_id,
        )
        res = await self.session.execute(stmt)
        for outfit in res.scalars().all():
            await self.session.delete(outfit)
        await self.session.flush()

    async def create_from_suggestion(
        self,
        user: User,
        *,
        name: str,
        color_harmony: str,
        reasoning: Optional[str],
        event_id: int,
        dress_ids: list[int],
    ) -> Outfit:
        dresses = await self._get_dresses_for_user(user, dress_ids)
        outfit = Outfit(
            user_id=user.id,
            name=name,
            color_harmony=color_harmony,
            reasoning=reasoning,
            event_id=event_id,
            pieces=dresses,
        )
        self.session.add(outfit)
        await self.session.flush()
        return await self._load_outfit(outfit.id)

    async def create_from_images(
        self,
        user: User,
        files: list[UploadFile],
        dress_service: DressService,
        media_service: MediaService,
    ) -> tuple[Outfit, list[int]]:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one image is required",
            )

        media_ids: list[int] = []
        for file in files:
            media = await media_service.upload(user, file)
            media_ids.append(media.id)

        return await self.create_from_uploaded_media(
            user.id, media_ids, dress_service, media_service
        )

    async def create_from_uploaded_media(
        self,
        user_id: int,
        media_ids: list[int],
        dress_service: DressService,
        media_service: MediaService,
    ) -> tuple[Outfit, list[int]]:
        if not media_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one image is required",
            )

        user = await self.session.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        from src.ai.client import describe_outfit

        all_dresses: list[Dress] = []

        for media_id in media_ids:
            dresses, _ = await dress_service.analyze_from_image(
                user_id, media_id, media_service
            )
            all_dresses.extend(dresses)

        if not all_dresses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No clothing items detected in the uploaded images",
            )

        dress_ids = [dress.id for dress in all_dresses]
        dresses = await self._get_dresses_for_user(user, dress_ids)
        description = await describe_outfit(dresses)
        outfit = Outfit(
            user_id=user.id,
            name=description.name,
            color_harmony=description.color_harmony,
            reasoning=description.reasoning,
            pieces=dresses,
        )
        self.session.add(outfit)
        await self.session.commit()
        return await self._load_outfit(outfit.id), media_ids
