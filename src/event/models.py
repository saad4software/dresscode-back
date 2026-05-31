from datetime import date, datetime, time, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel, Relationship

from src.admin.models import City, EventType


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

    outfit_suggestions: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    outfits_generated_at: Optional[datetime] = None

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
    outfit_suggestions: Optional[dict[str, Any]]
    outfits_generated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CityOption(SQLModel):
    slug: str
    display_name: str

