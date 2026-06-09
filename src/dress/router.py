from typing import Optional

from fastapi import APIRouter, File, Query, UploadFile, status

from src.auth.dependencies import CurrentUserDep
from src.core.models import IPageResponse
from src.dress.dependencies import DressServiceDep
from src.dress.models import (
    DressCreate,
    DressRead,
    DressUpdate,
    LinkMediaRequest,
)
from src.jobs.dependencies import JobServiceDep
from src.jobs.enqueue import enqueue_job
from src.jobs.models import JobRead, JobType
from src.jobs.service import job_to_read
from src.media.dependencies import MediaServiceDep
from src.media.models import MediaRead

router = APIRouter(prefix="/dresses", tags=["dresses"])


@router.post("", response_model=DressRead, status_code=status.HTTP_201_CREATED)
async def create_dress(
    data: DressCreate,
    service: DressServiceDep,
    current_user: CurrentUserDep,
) -> DressRead:
    dress = await service.create(current_user, data)
    return DressRead.model_validate(dress, from_attributes=True)


@router.post(
    "/from-image",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_dress_from_image(
    media_service: MediaServiceDep,
    job_service: JobServiceDep,
    current_user: CurrentUserDep,
    file: UploadFile = File(...),
) -> JobRead:
    media = await media_service.upload(current_user, file)
    job = await job_service.create(
        current_user,
        JobType.dress_from_image,
        {"media_id": media.id},
    )
    celery_task_id = enqueue_job(job)
    job = await job_service.set_celery_task_id(job, celery_task_id)
    return job_to_read(job)


@router.get("", response_model=IPageResponse[list[DressRead]])
async def list_dresses(
    service: DressServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    archived: bool = Query(default=False),
) -> IPageResponse[list[DressRead]]:

    result = await service.list_for_user(
        current_user,
        page=page,
        page_size=page_size,
        category=category,
        archived=archived,
    )
    return IPageResponse(
        page=result.page,
        total_items=result.total_items,
        total_pages=result.total_pages,
        results=[
            DressRead.model_validate(d, from_attributes=True)
            for d in result.results or []
        ],
    )


@router.get("/{dress_id}", response_model=DressRead)
async def get_dress(
    dress_id: int,
    service: DressServiceDep,
    current_user: CurrentUserDep,
) -> DressRead:
    dress = await service.get_for_user(current_user, dress_id)
    return DressRead.model_validate(dress, from_attributes=True)


@router.patch("/{dress_id}", response_model=DressRead)
async def update_dress(
    dress_id: int,
    data: DressUpdate,
    service: DressServiceDep,
    current_user: CurrentUserDep,
) -> DressRead:
    dress = await service.update(current_user, dress_id, data)
    return DressRead.model_validate(dress, from_attributes=True)


@router.delete("/{dress_id}", response_model=DressRead)
async def delete_dress(
    dress_id: int,
    media_service: MediaServiceDep,
    service: DressServiceDep,
    current_user: CurrentUserDep,
) -> DressRead:
    dress = await service.delete(current_user, dress_id, media_service)
    return DressRead.model_validate(dress, from_attributes=True)


@router.get("/{dress_id}/media", response_model=IPageResponse[list[MediaRead]])
async def list_dress_media(
    dress_id: int,
    service: DressServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> IPageResponse[list[MediaRead]]:
    result = await service.list_media(
        current_user, dress_id, page=page, page_size=page_size
    )
    return IPageResponse(
        page=result.page,
        total_items=result.total_items,
        total_pages=result.total_pages,
        results=[
            MediaRead.model_validate(m, from_attributes=True)
            for m in result.results or []
        ],
    )


@router.post("/{dress_id}/media", response_model=list[MediaRead])
async def link_dress_media(
    dress_id: int,
    data: LinkMediaRequest,
    service: DressServiceDep,
    current_user: CurrentUserDep,
) -> list[MediaRead]:
    items = await service.link_media(current_user, dress_id, data.media_ids)
    return [MediaRead.model_validate(m, from_attributes=True) for m in items]


@router.post(
    "/{dress_id}/analyze",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_dress(
    dress_id: int,
    dress_service: DressServiceDep,
    job_service: JobServiceDep,
    current_user: CurrentUserDep,
) -> JobRead:
    await dress_service.get_for_user(current_user, dress_id)
    job = await job_service.create(
        current_user,
        JobType.dress_analyze,
        {"dress_id": dress_id},
    )
    celery_task_id = enqueue_job(job)
    job = await job_service.set_celery_task_id(job, celery_task_id)
    return job_to_read(job)
