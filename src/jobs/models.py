from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class JobType(str, Enum):
    dress_from_image = "dress_from_image"
    dress_analyze = "dress_analyze"
    outfit_from_images = "outfit_from_images"
    event_suggest_outfits = "event_suggest_outfits"


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"


class Job(SQLModel, table=True):
    __tablename__ = "job"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    job_type: JobType = Field(index=True)
    status: JobStatus = Field(default=JobStatus.pending, index=True)
    params: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    result: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    error: Optional[str] = Field(default=None, max_length=2000)
    celery_task_id: Optional[str] = Field(default=None, max_length=255, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class JobRead(SQLModel):
    id: int
    user_id: int
    job_type: JobType
    status: JobStatus
    params: dict[str, Any]
    result: Optional[dict[str, Any]]
    error: Optional[str]
    celery_task_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
