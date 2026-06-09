from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from src.admin.models import City
from src.auth.constants import USER_ID_FOREIGN_KEY


class Gender(str, Enum):
    male = "male"
    female = "female"
    non_binary = "non_binary"
    prefer_not_to_say = "prefer_not_to_say"


class ProfilePersonalStyleLink(SQLModel, table=True):
    __tablename__ = "profile_personal_style"

    profile_user_id: int = Field(
        foreign_key="profile.user_id",
        primary_key=True,
    )
    personal_style_id: int = Field(
        foreign_key="personal_style.id",
        primary_key=True,
    )


class PersonalStyle(SQLModel, table=True):
    __tablename__ = "personal_style"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True, max_length=255)
    display_name: str = Field(max_length=255)
    description: Optional[str] = None


class Profile(SQLModel, table=True):
    __tablename__ = "profile"

    user_id: int = Field(foreign_key=USER_ID_FOREIGN_KEY, primary_key=True)
    name: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = None
    gender: Optional[Gender] = None
    city_id: Optional[int] = Field(default=None, foreign_key="city.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    city_obj: Optional[City] = Relationship()
    personal_styles: list[PersonalStyle] = Relationship(
        link_model=ProfilePersonalStyleLink,
    )


class PersonalStyleRead(SQLModel):
    id: int
    slug: str
    display_name: str
    description: Optional[str]


class ProfileRead(SQLModel):
    user_id: int
    name: Optional[str]
    bio: Optional[str]
    gender: Optional[Gender]
    city: Optional[str]
    city_id: Optional[int]
    personal_styles: list[PersonalStyleRead]
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = None
    gender: Optional[Gender] = None
    city: Optional[str] = None
    personal_style_slugs: Optional[list[str]] = None
