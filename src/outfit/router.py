from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from src.auth.dependencies import CurrentUserDep
from src.core.models import IPageResponse
from src.dress.dependencies import DressServiceDep
from src.media.dependencies import MediaServiceDep
from src.jobs.dependencies import JobServiceDep
from src.jobs.enqueue import enqueue_job
from src.jobs.models import JobRead, JobType
from src.jobs.service import job_to_read
from src.outfit.dependencies import OutfitServiceDep
from src.outfit.models import (
    OutfitCreate,
    OutfitRead,
    OutfitUpdate,
)
from src.outfit.service import outfit_to_read

router = APIRouter(prefix="/outfits", tags=["outfits"])


@router.post("", response_model=OutfitRead, status_code=status.HTTP_201_CREATED)
async def create_outfit(
    data: OutfitCreate,
    service: OutfitServiceDep,
    current_user: CurrentUserDep,
) -> OutfitRead:
    outfit = await service.create(current_user, data)
    return outfit_to_read(outfit)


@router.post(
    "/from-images",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_outfit_from_images(
    media_service: MediaServiceDep,
    job_service: JobServiceDep,
    current_user: CurrentUserDep,
    files: list[UploadFile] = File(...),
) -> JobRead:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one image is required",
        )
    media_ids: list[int] = []
    for file in files:
        media = await media_service.upload(current_user, file)
        media_ids.append(media.id)
    job = await job_service.create(
        current_user,
        JobType.outfit_from_images,
        {"media_ids": media_ids},
    )
    celery_task_id = enqueue_job(job)
    job = await job_service.set_celery_task_id(job, celery_task_id)
    return job_to_read(job)


@router.get("", response_model=IPageResponse[list[OutfitRead]])
async def list_outfits(
    service: OutfitServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    event_id: Optional[int] = Query(default=None),
) -> IPageResponse[list[OutfitRead]]:
    result = await service.list_for_user(
        current_user,
        page=page,
        page_size=page_size,
        event_id=event_id,
    )
    return IPageResponse(
        page=result.page,
        total_items=result.total_items,
        total_pages=result.total_pages,
        results=[outfit_to_read(o) for o in result.results or []],
    )


@router.get("/{outfit_id}", response_model=OutfitRead)
async def get_outfit(
    outfit_id: int,
    service: OutfitServiceDep,
    current_user: CurrentUserDep,
) -> OutfitRead:
    outfit = await service.get_for_user(current_user, outfit_id)
    return outfit_to_read(outfit)


@router.patch("/{outfit_id}", response_model=OutfitRead)
async def update_outfit(
    outfit_id: int,
    data: OutfitUpdate,
    service: OutfitServiceDep,
    current_user: CurrentUserDep,
) -> OutfitRead:
    outfit = await service.update(current_user, outfit_id, data)
    return outfit_to_read(outfit)


@router.delete("/{outfit_id}", response_model=OutfitRead)
async def delete_outfit(
    outfit_id: int,
    service: OutfitServiceDep,
    current_user: CurrentUserDep,
) -> OutfitRead:
    outfit = await service.get_for_user(current_user, outfit_id)
    read = outfit_to_read(outfit)
    await service.delete(current_user, outfit_id)
    return read
