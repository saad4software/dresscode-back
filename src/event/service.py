from datetime import datetime, time, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

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

        event = Event(user_id=user.id, **data.model_dump())
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_for_user(self, user: User, event_id: int) -> Event:
        event = await self.session.get(Event, event_id)
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

        for field, value in updates.items():
            setattr(event, field, value)
        event.updated_at = datetime.now(timezone.utc)

        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def delete(self, user: User, event_id: int) -> None:
        event = await self.get_for_user(user, event_id)
        await self.session.delete(event)
        await self.session.commit()

    async def save_outfit_suggestions(
        self, event: Event, payload: dict
    ) -> Event:
        event.outfit_suggestions = payload
        event.outfits_generated_at = datetime.now(timezone.utc)
        event.updated_at = event.outfits_generated_at
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event
