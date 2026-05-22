from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from src.event.cities import GermanCity


class EventType(str, Enum):
    business = "business"
    casual = "casual"
    smart_casual = "smart_casual"
    formal = "formal"
    outdoor = "outdoor"
    party = "party"
    sports = "sports"
    date_night = "date_night"
    other = "other"


class EventBase(SQLModel):
    title: Optional[str] = Field(default=None, max_length=255)
    event_type: EventType
    event_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    city: GermanCity = Field(default=GermanCity.berlin)
    notes: Optional[str] = None


class Event(EventBase, table=True):
    __tablename__ = "event"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    outfit_suggestions: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    outfits_generated_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventCreate(SQLModel):
    title: Optional[str] = None
    event_type: EventType
    event_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    city: GermanCity = GermanCity.berlin
    notes: Optional[str] = None


class EventUpdate(SQLModel):
    title: Optional[str] = None
    event_type: Optional[EventType] = None
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    city: Optional[GermanCity] = None
    notes: Optional[str] = None


class EventRead(SQLModel):
    id: int
    user_id: int
    title: Optional[str]
    event_type: EventType
    event_date: date
    start_time: Optional[time]
    end_time: Optional[time]
    city: GermanCity
    notes: Optional[str]
    outfit_suggestions: Optional[dict[str, Any]]
    outfits_generated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CityOption(SQLModel):
    slug: GermanCity
    display_name: str
