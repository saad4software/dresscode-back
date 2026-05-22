from typing import Annotated

from fastapi import Depends

from src.core.dependencies import SessionDep
from src.dress.service import DressService


def get_dress_service(session: SessionDep) -> DressService:
    return DressService(session)


DressServiceDep = Annotated[DressService, Depends(get_dress_service)]
