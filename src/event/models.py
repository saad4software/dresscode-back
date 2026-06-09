from datetime import date, datetime, time, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship

from src.admin.models import City, EventType
from src.outfit.models import OutfitRead


class Event(SQLModel, table=True):
    __tablename__ = "event"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    title: Optional[str] = Field(default=None, max_length=255)
    event_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    notes: Optional[str] = None

    city_id: int = Field(foreign_key="city.id")
    event_type_id: int = Field(foreign_key="event_type.id")

    weather_summary: Optional[str] = None
    season: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    city_obj: Optional[City] = Relationship()
    event_type_obj: Optional[EventType] = Relationship()

    @property
    def city(self) -> str:
        return self.city_obj.slug if self.city_obj else ""

    @property
    def event_type(self) -> str:
        return self.event_type_obj.slug if self.event_type_obj else ""


class EventCreate(SQLModel):
    title: Optional[str] = None
    event_type: str
    event_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    city: str = "berlin"
    notes: Optional[str] = None


class EventUpdate(SQLModel):
    title: Optional[str] = None
    event_type: Optional[str] = None
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    city: Optional[str] = None
    notes: Optional[str] = None


class EventRead(SQLModel):
    id: int
    user_id: int
    title: Optional[str]
    event_type: str
    event_type_id: int
    event_date: date
    start_time: Optional[time]
    end_time: Optional[time]
    city: str
    city_id: int
    notes: Optional[str]
    weather_summary: Optional[str]
    season: Optional[str]
    has_outfit_suggestions: bool = False
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_event(
        cls, event: "Event", *, has_outfit_suggestions: bool = False
    ) -> "EventRead":
        return cls(
            id=event.id,
            user_id=event.user_id,
            title=event.title,
            event_type=event.event_type,
            event_type_id=event.event_type_id,
            event_date=event.event_date,
            start_time=event.start_time,
            end_time=event.end_time,
            city=event.city,
            city_id=event.city_id,
            notes=event.notes,
            weather_summary=event.weather_summary,
            season=event.season,
            has_outfit_suggestions=has_outfit_suggestions,
            created_at=event.created_at,
            updated_at=event.updated_at,
        )


class EventDetailRead(EventRead):
    outfit_suggestions: list[OutfitRead] = []

    @classmethod
    def from_event(
        cls,
        event: "Event",
        outfit_suggestions: list[OutfitRead],
    ) -> "EventDetailRead":
        return cls(
            **EventRead.from_event(
                event,
                has_outfit_suggestions=bool(outfit_suggestions),
            ).model_dump(),
            outfit_suggestions=outfit_suggestions,
        )


class CityOption(SQLModel):
    slug: str
    display_name: str
