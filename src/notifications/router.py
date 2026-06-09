from fastapi import APIRouter, Query, status

from src.auth.dependencies import CurrentUserDep
from src.core.models import IPageResponse
from src.notifications.dependencies import NotificationServiceDep
from src.notifications.models import (
    DeviceTokenCreate,
    DeviceTokenRead,
    NotificationRead,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "/devices",
    response_model=DeviceTokenRead,
    status_code=status.HTTP_201_CREATED,
)
async def register_device(
    data: DeviceTokenCreate,
    service: NotificationServiceDep,
    current_user: CurrentUserDep,
) -> DeviceTokenRead:
    device = await service.register_device(current_user, data)
    return DeviceTokenRead.model_validate(device, from_attributes=True)


@router.get("", response_model=IPageResponse[list[NotificationRead]])
async def list_notifications(
    service: NotificationServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
) -> IPageResponse[list[NotificationRead]]:
    result = await service.list_for_user(
        current_user,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    return IPageResponse(
        page=result.page,
        total_items=result.total_items,
        total_pages=result.total_pages,
        results=[
            NotificationRead.model_validate(n, from_attributes=True)
            for n in result.results or []
        ],
    )


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: int,
    service: NotificationServiceDep,
    current_user: CurrentUserDep,
) -> NotificationRead:
    notification = await service.mark_read(current_user, notification_id)
    return NotificationRead.model_validate(notification, from_attributes=True)
