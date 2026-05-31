from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import computed_field
from src.media.models import Media


class City(SQLModel, table=True):
    __tablename__ = "city"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True, max_length=255)
    display_name: str = Field(max_length=255)
    latitude: float
    longitude: float
    media_id: Optional[int] = Field(default=None, foreign_key="media.id", nullable=True)

    media: Optional[Media] = Relationship()


class CityCreate(SQLModel):
    slug: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    latitude: float
    longitude: float
    media_id: Optional[int] = None


class CityRead(SQLModel):
    id: int
    slug: str
    display_name: str
    latitude: float
    longitude: float
    media_id: Optional[int]

    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        if self.media_id is not None:
            return f"/media/{self.media_id}/file"
        return None


class EventType(SQLModel, table=True):
    __tablename__ = "event_type"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True, max_length=255)
    display_name: str = Field(max_length=255)
    media_id: Optional[int] = Field(default=None, foreign_key="media.id", nullable=True)

    media: Optional[Media] = Relationship()


class EventTypeCreate(SQLModel):
    slug: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    media_id: Optional[int] = None


class EventTypeRead(SQLModel):
    id: int
    slug: str
    display_name: str
    media_id: Optional[int]

    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        if self.media_id is not None:
            return f"/media/{self.media_id}/file"
        return None


class DressCategory(SQLModel, table=True):
    __tablename__ = "dress_category"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True, max_length=255)
    display_name: str = Field(max_length=255)
    media_id: Optional[int] = Field(default=None, foreign_key="media.id", nullable=True)

    media: Optional[Media] = Relationship()


class DressCategoryCreate(SQLModel):
    slug: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    media_id: Optional[int] = None


class DressCategoryRead(SQLModel):
    id: int
    slug: str
    display_name: str
    media_id: Optional[int]

    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        if self.media_id is not None:
            return f"/media/{self.media_id}/file"
        return None
