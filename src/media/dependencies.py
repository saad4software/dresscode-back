from typing import Annotated

from fastapi import Depends

from src.core.dependencies import SessionDep
from src.media.service import MediaService


def get_media_service(session: SessionDep) -> MediaService:
    return MediaService(session)


MediaServiceDep = Annotated[MediaService, Depends(get_media_service)]
