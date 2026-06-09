from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.dependencies import AuthServiceDep, CurrentUserDep
from src.auth.models import (
    ChangePasswordRequest,
    RefreshRequest,
    ResendVerificationCodeRequest,
    TokenPair,
    UserCreate,
    UserRead,
    LoginRequest,
    VerifyEmailRequest,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, service: AuthServiceDep) -> UserRead:
    user = await service.register(data)
    return UserRead.model_validate(user, from_attributes=True)


@router.post("/login_swagger", response_model=TokenPair)
async def login_swagger(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
) -> TokenPair:
    return await service.login(form_data.username, form_data.password)


@router.post("/login", response_model=TokenPair)
async def login(
    data: LoginRequest,
    service: AuthServiceDep,
) -> TokenPair:
    return await service.login(data.username, data.password)


@router.post("/verify-email", response_model=UserRead)
async def verify_email(
    data: VerifyEmailRequest,
    service: AuthServiceDep,
) -> UserRead:
    user = await service.verify_email(data.username, data.code)
    return UserRead.model_validate(user, from_attributes=True)


@router.post(
    "/resend-verification-code",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def resend_verification_code(
    data: ResendVerificationCodeRequest,
    service: AuthServiceDep,
) -> None:
    await service.resend_verification_code(data.username, data.password)


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshRequest, service: AuthServiceDep) -> TokenPair:
    return await service.refresh(data.refresh_token)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    service: AuthServiceDep,
    current_user: CurrentUserDep,
) -> None:
    await service.change_password(
        current_user, data.current_password, data.new_password
    )


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUserDep) -> UserRead:
    return UserRead.model_validate(current_user, from_attributes=True)
