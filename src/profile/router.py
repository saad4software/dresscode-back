from fastapi import APIRouter

from src.auth.dependencies import CurrentUserDep
from src.profile.dependencies import ProfileServiceDep
from src.profile.models import PersonalStyleRead, ProfileRead, ProfileUpdate
from src.profile.service import _profile_to_read

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/personal-styles", response_model=list[PersonalStyleRead])
async def list_personal_styles(service: ProfileServiceDep) -> list[PersonalStyleRead]:
    styles = await service.list_personal_styles()
    return [
        PersonalStyleRead.model_validate(style, from_attributes=True)
        for style in styles
    ]


@router.get("/me", response_model=ProfileRead)
async def get_my_profile(
    service: ProfileServiceDep,
    current_user: CurrentUserDep,
) -> ProfileRead:
    profile = await service.get_or_create_profile(current_user)
    return _profile_to_read(profile)


@router.patch("/me", response_model=ProfileRead)
async def update_my_profile(
    data: ProfileUpdate,
    service: ProfileServiceDep,
    current_user: CurrentUserDep,
) -> ProfileRead:
    profile = await service.update_profile(current_user, data)
    return _profile_to_read(profile)
