from typing import Annotated

from fastapi import Depends

from src.core.dependencies import SessionDep
from src.notifications.service import NotificationService


def get_notification_service(session: SessionDep) -> NotificationService:
    return NotificationService(session)


NotificationServiceDep = Annotated[
    NotificationService, Depends(get_notification_service)
]
