from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.models import User
from src.core.models import IPageResponse
from src.core.pagination import paginate
from src.jobs.models import Job, JobRead, JobStatus, JobType


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user: User,
        job_type: JobType,
        params: dict[str, Any],
    ) -> Job:
        job = Job(
            user_id=user.id,
            job_type=job_type,
            status=JobStatus.pending,
            params=params,
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_for_user(self, user: User, job_id: int) -> Job:
        job = await self.session.get(Job, job_id)
        if job is None or job.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )
        return job

    async def list_for_user(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        job_type: Optional[JobType] = None,
        job_status: Optional[JobStatus] = None,
    ) -> IPageResponse[list[Job]]:
        stmt = (
            select(Job)
            .where(Job.user_id == user.id)
            .order_by(Job.created_at.desc())
        )
        if job_type is not None:
            stmt = stmt.where(Job.job_type == job_type)
        if job_status is not None:
            stmt = stmt.where(Job.status == job_status)
        return await paginate(self.session, stmt, page, page_size)

    async def set_celery_task_id(self, job: Job, celery_task_id: str) -> Job:
        job.celery_task_id = celery_task_id
        job.updated_at = datetime.now(timezone.utc)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def mark_processing(self, job_id: int) -> Job:
        job = await self.session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job.status = JobStatus.processing
        job.started_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def mark_succeeded(self, job_id: int, result: dict[str, Any]) -> Job:
        job = await self.session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job.status = JobStatus.succeeded
        job.result = result
        job.error = None
        job.finished_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def mark_failed(self, job_id: int, error: str) -> Job:
        job = await self.session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job.status = JobStatus.failed
        job.error = error[:2000]
        job.finished_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job


def job_to_read(job: Job) -> JobRead:
    return JobRead.model_validate(job, from_attributes=True)
