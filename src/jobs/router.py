from typing import Optional

from fastapi import APIRouter, Query

from src.auth.dependencies import CurrentUserDep
from src.core.models import IPageResponse
from src.jobs.dependencies import JobServiceDep
from src.jobs.models import JobRead, JobStatus, JobType
from src.jobs.service import job_to_read

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: int,
    service: JobServiceDep,
    current_user: CurrentUserDep,
) -> JobRead:
    job = await service.get_for_user(current_user, job_id)
    return job_to_read(job)


@router.get("", response_model=IPageResponse[list[JobRead]])
async def list_jobs(
    service: JobServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    job_type: Optional[JobType] = Query(default=None),
    job_status: Optional[JobStatus] = Query(default=None),
) -> IPageResponse[list[JobRead]]:
    result = await service.list_for_user(
        current_user,
        page=page,
        page_size=page_size,
        job_type=job_type,
        job_status=job_status,
    )
    return IPageResponse(
        page=result.page,
        total_items=result.total_items,
        total_pages=result.total_pages,
        results=[job_to_read(j) for j in result.results or []],
    )
