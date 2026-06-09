from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class DevicePlatform(str, Enum):
    ios = "ios"
    android = "android"
    web = "web"


class DeviceToken(SQLModel, table=True):
    __tablename__ = "device_token"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token: str = Field(max_length=512, unique=True, index=True)
    platform: DevicePlatform
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Notification(SQLModel, table=True):
    __tablename__ = "notification"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str = Field(max_length=255)
    body: str = Field(max_length=1024)
    data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    is_read: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeviceTokenCreate(SQLModel):
    token: str = Field(max_length=512)
    platform: DevicePlatform


class DeviceTokenRead(SQLModel):
    id: int
    user_id: int
    token: str
    platform: DevicePlatform
    created_at: datetime
    last_used_at: datetime


class NotificationRead(SQLModel):
    id: int
    user_id: int
    title: str
    body: str
    data: dict[str, Any]
    is_read: bool
    created_at: datetime
