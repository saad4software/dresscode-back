from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.admin.models import (
    City, CityCreate,
    EventType, EventTypeCreate,
    DressCategory, DressCategoryCreate
)
from src.media.models import Media


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _validate_media(self, media_id: int | None) -> None:
        if media_id is not None:
            media = await self.session.get(Media, media_id)
            if not media:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Media item with ID {media_id} not found",
                )

    # City
    async def create_city(self, data: CityCreate) -> City:
        await self._validate_media(data.media_id)
        stmt = select(City).where(City.slug == data.slug)
        res = await self.session.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"City slug '{data.slug}' already exists",
            )
        city = City(**data.model_dump())
        self.session.add(city)
        await self.session.commit()
        await self.session.refresh(city)
        return city

    async def list_cities(self) -> list[City]:
        stmt = select(City).order_by(City.display_name)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    # EventType
    async def create_event_type(self, data: EventTypeCreate) -> EventType:
        await self._validate_media(data.media_id)
        stmt = select(EventType).where(EventType.slug == data.slug)
        res = await self.session.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Event type slug '{data.slug}' already exists",
            )
        et = EventType(**data.model_dump())
        self.session.add(et)
        await self.session.commit()
        await self.session.refresh(et)
        return et

    async def list_event_types(self) -> list[EventType]:
        stmt = select(EventType).order_by(EventType.display_name)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    # DressCategory
    async def create_dress_category(self, data: DressCategoryCreate) -> DressCategory:
        await self._validate_media(data.media_id)
        stmt = select(DressCategory).where(DressCategory.slug == data.slug)
        res = await self.session.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dress category slug '{data.slug}' already exists",
            )
        dc = DressCategory(**data.model_dump())
        self.session.add(dc)
        await self.session.commit()
        await self.session.refresh(dc)
        return dc

    async def list_dress_categories(self) -> list[DressCategory]:
        stmt = select(DressCategory).order_by(DressCategory.display_name)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
