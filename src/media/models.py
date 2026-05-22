from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class ProcessingStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Media(SQLModel, table=True):
    __tablename__ = "media"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    dress_id: Optional[int] = Field(
        default=None, foreign_key="dress.id", index=True, nullable=True
    )

    storage_path: str = Field(max_length=512)
    original_filename: str = Field(max_length=255)
    mime_type: str = Field(max_length=64)
    size_bytes: int

    width: Optional[int] = None
    height: Optional[int] = None
    sort_order: int = Field(default=0)

    processing_status: ProcessingStatus = Field(default=ProcessingStatus.pending)
    processing_error: Optional[str] = Field(default=None, max_length=512)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MediaRead(SQLModel):
    id: int
    user_id: int
    dress_id: Optional[int]
    storage_path: str
    original_filename: str
    mime_type: str
    size_bytes: int
    width: Optional[int]
    height: Optional[int]
    sort_order: int
    processing_status: ProcessingStatus
    processing_error: Optional[str]
    created_at: datetime


class MediaUpdate(SQLModel):
    dress_id: Optional[int] = None
    sort_order: Optional[int] = None
    unassign: Optional[bool] = None
