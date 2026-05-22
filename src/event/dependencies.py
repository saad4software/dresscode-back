from typing import Annotated

from fastapi import Depends

from src.core.dependencies import SessionDep
from src.event.service import EventService


def get_event_service(session: SessionDep) -> EventService:
    return EventService(session)


EventServiceDep = Annotated[EventService, Depends(get_event_service)]
