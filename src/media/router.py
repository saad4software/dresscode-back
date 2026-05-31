from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from src.ai.tasks import analyze_dress_task
from src.auth.dependencies import CurrentUserDep
from src.core.config import config
from src.core.models import IPageResponse
from src.media.dependencies import MediaServiceDep
from src.media.models import MediaRead, MediaUpdate

router = APIRouter(prefix="/media", tags=["media"])


@router.post(
    "/upload",
    response_model=MediaRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media(
    background_tasks: BackgroundTasks,
    service: MediaServiceDep,
    current_user: CurrentUserDep,
    file: UploadFile = File(...),
    dress_id: Optional[int] = Form(default=None),
) -> MediaRead:
    media = await service.upload(current_user, file, dress_id=dress_id)
    if dress_id is not None and config.ai_auto_analyze_on_upload:
        background_tasks.add_task(analyze_dress_task, dress_id, current_user.id)
    return MediaRead.model_validate(media, from_attributes=True)


@router.get("", response_model=IPageResponse[list[MediaRead]])
async def list_media(
    service: MediaServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    dress_id: Optional[int] = Query(default=None),
    unassigned: bool = Query(default=False),
) -> IPageResponse[list[MediaRead]]:
    result = await service.list_for_user(
        current_user,
        page=page,
        page_size=page_size,
        dress_id=dress_id,
        unassigned=unassigned,
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


@router.get("/{media_id}", response_model=MediaRead)
async def get_media(
    media_id: int,
    service: MediaServiceDep,
    current_user: CurrentUserDep,
) -> MediaRead:
    media = await service.get_for_user(current_user, media_id)
    return MediaRead.model_validate(media, from_attributes=True)


@router.patch("/{media_id}", response_model=MediaRead)
async def update_media(
    media_id: int,
    data: MediaUpdate,
    service: MediaServiceDep,
    current_user: CurrentUserDep,
) -> MediaRead:
    media = await service.update(current_user, media_id, data)
    return MediaRead.model_validate(media, from_attributes=True)


@router.delete("/{media_id}", response_model=MediaRead)
async def delete_media(
    media_id: int,
    service: MediaServiceDep,
    current_user: CurrentUserDep,
) -> MediaRead:
    media = await service.delete(current_user, media_id)
    return MediaRead.model_validate(media, from_attributes=True)


@router.get("/{media_id}/file")
async def get_media_file(
    media_id: int,
    service: MediaServiceDep,
    current_user: CurrentUserDep,
) -> FileResponse:
    media = await service.get_for_user(current_user, media_id)
    path = Path(media.storage_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File missing on disk",
        )
    return FileResponse(path, media_type=media.mime_type)
