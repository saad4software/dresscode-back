from typing import Annotated

from fastapi import Depends

from src.core.dependencies import SessionDep
from src.outfit.service import OutfitService


def get_outfit_service(session: SessionDep) -> OutfitService:
    return OutfitService(session)


OutfitServiceDep = Annotated[OutfitService, Depends(get_outfit_service)]
