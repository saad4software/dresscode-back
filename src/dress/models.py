from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Category(str, Enum):
    top = "top"
    bottom = "bottom"
    outerwear = "outerwear"
    shoes = "shoes"
    accessory = "accessory"
    dress = "dress"
    underwear = "underwear"
    bag = "bag"
    hat = "hat"
    socks = "socks"
    other = "other"


class WarmthLevel(str, Enum):
    light = "light"
    medium = "medium"
    heavy = "heavy"


class Season(str, Enum):
    summer = "summer"
    winter = "winter"
    spring = "spring"
    fall = "fall"
    all_season = "all_season"


class Layering(str, Enum):
    base = "base"
    mid = "mid"
    outer = "outer"


class Pattern(str, Enum):
    solid = "solid"
    striped = "striped"
    plaid = "plaid"
    floral = "floral"
    graphic = "graphic"
    other = "other"


class Formality(str, Enum):
    casual = "casual"
    smart_casual = "smart_casual"
    business = "business"
    formal = "formal"


class Brightness(str, Enum):
    light = "light"
    dark = "dark"
    mixed = "mixed"


class DressStatus(str, Enum):
    draft = "draft"
    ready = "ready"
    needs_review = "needs_review"


class DressBase(SQLModel):
    item_name: Optional[str] = Field(default=None, max_length=255)
    category: Optional[Category] = None
    dominant_color: Optional[str] = Field(default=None, max_length=7)
    warmth_level: Optional[WarmthLevel] = None
    description: Optional[str] = None
    layering: Optional[Layering] = None
    pattern: Optional[Pattern] = None
    material: Optional[str] = Field(default=None, max_length=64)
    formality: Optional[Formality] = None
    brightness: Optional[Brightness] = None
    water_resistant: bool = False
    is_archived: bool = False
    user_notes: Optional[str] = None


class Dress(DressBase, table=True):
    __tablename__ = "dress"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    colors: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    season_suitability: list[Season] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    style: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    occasion_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    status: DressStatus = Field(default=DressStatus.draft)
    ai_confidence: Optional[float] = None
    ai_model_version: Optional[str] = Field(default=None, max_length=64)
    ai_processed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _validate_hex(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    v = value.strip()
    if not v.startswith("#") or len(v) != 7:
        raise ValueError("color must be a hex string like #RRGGBB")
    try:
        int(v[1:], 16)
    except ValueError as exc:
        raise ValueError("color must be a hex string like #RRGGBB") from exc
    return v.lower()


class DressCreate(SQLModel):
    item_name: Optional[str] = None
    category: Optional[Category] = None
    colors: list[str] = Field(default_factory=list)
    dominant_color: Optional[str] = None
    warmth_level: Optional[WarmthLevel] = None
    season_suitability: list[Season] = Field(default_factory=list)
    style: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    layering: Optional[Layering] = None
    pattern: Optional[Pattern] = None
    material: Optional[str] = None
    formality: Optional[Formality] = None
    brightness: Optional[Brightness] = None
    water_resistant: bool = False
    occasion_tags: list[str] = Field(default_factory=list)
    user_notes: Optional[str] = None

    @field_validator("dominant_color")
    @classmethod
    def _v_dominant(cls, v):
        return _validate_hex(v)

    @field_validator("colors")
    @classmethod
    def _v_colors(cls, v):
        return [_validate_hex(c) for c in v]


class DressUpdate(SQLModel):
    item_name: Optional[str] = None
    category: Optional[Category] = None
    colors: Optional[list[str]] = None
    dominant_color: Optional[str] = None
    warmth_level: Optional[WarmthLevel] = None
    season_suitability: Optional[list[Season]] = None
    style: Optional[list[str]] = None
    description: Optional[str] = None
    layering: Optional[Layering] = None
    pattern: Optional[Pattern] = None
    material: Optional[str] = None
    formality: Optional[Formality] = None
    brightness: Optional[Brightness] = None
    water_resistant: Optional[bool] = None
    occasion_tags: Optional[list[str]] = None
    is_archived: Optional[bool] = None
    user_notes: Optional[str] = None
    status: Optional[DressStatus] = None

    @field_validator("dominant_color")
    @classmethod
    def _v_dominant(cls, v):
        return _validate_hex(v)

    @field_validator("colors")
    @classmethod
    def _v_colors(cls, v):
        if v is None:
            return v
        return [_validate_hex(c) for c in v]


class DressRead(SQLModel):
    id: int
    user_id: int
    item_name: Optional[str]
    category: Optional[Category]
    colors: list[str]
    dominant_color: Optional[str]
    warmth_level: Optional[WarmthLevel]
    season_suitability: list[Season]
    style: list[str]
    description: Optional[str]
    layering: Optional[Layering]
    pattern: Optional[Pattern]
    material: Optional[str]
    formality: Optional[Formality]
    brightness: Optional[Brightness]
    water_resistant: bool
    occasion_tags: list[str]
    status: DressStatus
    ai_confidence: Optional[float]
    ai_model_version: Optional[str]
    ai_processed_at: Optional[datetime]
    is_archived: bool
    user_notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class LinkMediaRequest(SQLModel):
    media_ids: list[int]


class DressAnalyzeResponse(SQLModel):
    dress: DressRead
    analyzed_media_ids: list[int]
    failed_media_ids: list[int]


class DressCreateFromImageResponse(SQLModel):
    dresses: list[DressRead]
    media_id: int
