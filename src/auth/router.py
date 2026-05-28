from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.constants import (
    AUTH_ROUTER_PREFIX,
    AUTH_ROUTER_TAG,
    CHANGE_PASSWORD_PATH,
    LOGIN_PATH,
    LOGIN_SWAGGER_PATH,
    ME_PATH,
    REFRESH_PATH,
    REGISTER_PATH,
    RESEND_VERIFICATION_CODE_PATH,
    VERIFY_EMAIL_PATH,
)
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


router = APIRouter(prefix=AUTH_ROUTER_PREFIX, tags=[AUTH_ROUTER_TAG])


@router.post(REGISTER_PATH, response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, service: AuthServiceDep) -> UserRead:
    user = await service.register(data)
    return UserRead.model_validate(user, from_attributes=True)


@router.post(LOGIN_SWAGGER_PATH, response_model=TokenPair)
async def login_swagger(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
) -> TokenPair:
    return await service.login(form_data.username, form_data.password)


@router.post(LOGIN_PATH, response_model=TokenPair)
async def login(
    data: LoginRequest,
    service: AuthServiceDep,
) -> TokenPair:
    return await service.login(data.username, data.password)


@router.post(VERIFY_EMAIL_PATH, response_model=UserRead)
async def verify_email(
    data: VerifyEmailRequest,
    service: AuthServiceDep,
) -> UserRead:
    user = await service.verify_email(data.username, data.code)
    return UserRead.model_validate(user, from_attributes=True)


@router.post(
    RESEND_VERIFICATION_CODE_PATH,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def resend_verification_code(
    data: ResendVerificationCodeRequest,
    service: AuthServiceDep,
) -> None:
    await service.resend_verification_code(data.username, data.password)


@router.post(REFRESH_PATH, response_model=TokenPair)
async def refresh(data: RefreshRequest, service: AuthServiceDep) -> TokenPair:
    return await service.refresh(data.refresh_token)


@router.post(CHANGE_PASSWORD_PATH, status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    service: AuthServiceDep,
    current_user: CurrentUserDep,
) -> None:
    await service.change_password(
        current_user, data.current_password, data.new_password
    )


@router.get(ME_PATH, response_model=UserRead)
async def me(current_user: CurrentUserDep) -> UserRead:
    return UserRead.model_validate(current_user, from_attributes=True)
