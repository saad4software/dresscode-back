from typing import Annotated

from fastapi import Depends

from src.core.dependencies import SessionDep
from src.profile.service import ProfileService


def get_profile_service(session: SessionDep) -> ProfileService:
    return ProfileService(session)


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
