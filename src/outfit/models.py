from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from src.dress.models import Dress, DressRead


class OutfitDressLink(SQLModel, table=True):
    __tablename__ = "outfit_dress"

    outfit_id: int = Field(foreign_key="outfit.id", primary_key=True)
    dress_id: int = Field(foreign_key="dress.id", primary_key=True)


class Outfit(SQLModel, table=True):
    __tablename__ = "outfit"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=255)
    color_harmony: str
    reasoning: Optional[str] = None
    event_id: Optional[int] = Field(
        default=None, foreign_key="event.id", index=True, nullable=True
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    pieces: list[Dress] = Relationship(link_model=OutfitDressLink)


class OutfitCreate(SQLModel):
    name: str = Field(max_length=255)
    color_harmony: str
    reasoning: Optional[str] = None
    event_id: Optional[int] = None
    dress_ids: list[int]


class OutfitUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)
    color_harmony: Optional[str] = None
    reasoning: Optional[str] = None
    event_id: Optional[int] = None
    dress_ids: Optional[list[int]] = None


class OutfitRead(SQLModel):
    id: int
    user_id: int
    name: str
    color_harmony: str
    reasoning: Optional[str]
    event_id: Optional[int]
    pieces: list[DressRead]
    created_at: datetime
    updated_at: datetime


class OutfitFromImagesResponse(SQLModel):
    outfit: OutfitRead
    media_ids: list[int]
