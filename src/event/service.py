from datetime import datetime, time, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.admin.models import City, EventType
from src.auth.models import User
from src.core.models import IPageResponse
from src.core.pagination import paginate
from src.event.models import Event, EventCreate, EventUpdate

BERLIN_TZ = ZoneInfo("Europe/Berlin")


def _validate_times(
    start_time: Optional[time], end_time: Optional[time]
) -> None:
    if end_time is not None and start_time is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time is required when end_time is provided",
        )
    if start_time is not None and end_time is not None and end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time must be after start_time",
        )


def _validate_future(event_date, start_time: Optional[time]) -> None:
    start = datetime.combine(
        event_date, start_time or time.min, tzinfo=BERLIN_TZ
    )
    now_berlin = datetime.now(BERLIN_TZ)
    if start <= now_berlin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Event must start in the future",
        )


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User, data: EventCreate) -> Event:
        _validate_times(data.start_time, data.end_time)
        _validate_future(data.event_date, data.start_time)

        stmt_city = select(City).where(City.slug == data.city)
        res_city = await self.session.execute(stmt_city)
        city_obj = res_city.scalar_one_or_none()
        if not city_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"City '{data.city}' not found",
            )

        stmt_et = select(EventType).where(EventType.slug == data.event_type)
        res_et = await self.session.execute(stmt_et)
        et_obj = res_et.scalar_one_or_none()
        if not et_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Event type '{data.event_type}' not found",
            )

        fields = data.model_dump(exclude_unset=False)
        fields.pop("city", None)
        fields.pop("event_type", None)

        event = Event(
            user_id=user.id,
            city_id=city_obj.id,
            event_type_id=et_obj.id,
            **fields,
        )
        self.session.add(event)
        await self.session.commit()

        # Eagerly load relationship objects
        stmt = select(Event).where(Event.id == event.id).options(
            selectinload(Event.city_obj),
            selectinload(Event.event_type_obj)
        )
        res = await self.session.execute(stmt)
        event = res.scalar_one()
        return event

    async def get_for_user(self, user: User, event_id: int) -> Event:
        stmt = select(Event).where(Event.id == event_id).options(
            selectinload(Event.city_obj),
            selectinload(Event.event_type_obj)
        )
        res = await self.session.execute(stmt)
        event = res.scalar_one_or_none()
        if event is None or event.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return event

    async def list_for_user(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> IPageResponse[list[Event]]:
        now_berlin = datetime.now(BERLIN_TZ)
        today = now_berlin.date()
        current_time = now_berlin.time()

        stmt = (
            select(Event)
            .options(
                selectinload(Event.city_obj),
                selectinload(Event.event_type_obj)
            )
            .where(Event.user_id == user.id)
            .where(
                (Event.event_date > today)
                | (
                    (Event.event_date == today)
                    & (
                        (Event.start_time.is_(None))
                        | (Event.start_time >= current_time)
                    )
                )
            )
            .order_by(Event.event_date.asc(), Event.start_time.asc())
        )
        return await paginate(self.session, stmt, page, page_size)

    async def update(
        self, user: User, event_id: int, data: EventUpdate
    ) -> Event:
        event = await self.get_for_user(user, event_id)
        updates = data.model_dump(exclude_unset=True)

        new_date = updates.get("event_date", event.event_date)
        new_start = updates.get("start_time", event.start_time)
        new_end = updates.get("end_time", event.end_time)

        date_or_time_changed = (
            "event_date" in updates
            or "start_time" in updates
            or "end_time" in updates
        )

        if date_or_time_changed:
            _validate_times(new_start, new_end)
            _validate_future(new_date, new_start)

        if "city" in updates:
            city_slug = updates.pop("city")
            stmt_city = select(City).where(City.slug == city_slug)
            res_city = await self.session.execute(stmt_city)
            city_obj = res_city.scalar_one_or_none()
            if not city_obj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"City '{city_slug}' not found",
                )
            event.city_id = city_obj.id

        if "event_type" in updates:
            et_slug = updates.pop("event_type")
            stmt_et = select(EventType).where(EventType.slug == et_slug)
            res_et = await self.session.execute(stmt_et)
            et_obj = res_et.scalar_one_or_none()
            if not et_obj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Event type '{et_slug}' not found",
                )
            event.event_type_id = et_obj.id

        for field, value in updates.items():
            setattr(event, field, value)
        event.updated_at = datetime.now(timezone.utc)

        self.session.add(event)
        await self.session.commit()

        # Eagerly load relationship objects
        stmt = select(Event).where(Event.id == event.id).options(
            selectinload(Event.city_obj),
            selectinload(Event.event_type_obj)
        )
        res = await self.session.execute(stmt)
        event = res.scalar_one()
        return event

    async def delete(self, user: User, event_id: int) -> Event:
        event = await self.get_for_user(user, event_id)
        await self.session.delete(event)
        await self.session.commit()
        return event

    async def save_outfit_suggestions(
        self, event: Event, payload: dict
    ) -> Event:
        event.outfit_suggestions = payload
        event.outfits_generated_at = datetime.now(timezone.utc)
        event.updated_at = event.outfits_generated_at
        self.session.add(event)
        await self.session.commit()

        # Eagerly load relationship objects after update
        stmt = select(Event).where(Event.id == event.id).options(
            selectinload(Event.city_obj),
            selectinload(Event.event_type_obj)
        )
        res = await self.session.execute(stmt)
        event = res.scalar_one()
        return event

