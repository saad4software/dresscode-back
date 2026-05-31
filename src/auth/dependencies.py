from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.auth.constants import OAUTH_TOKEN_URL
from src.auth.models import User
from src.auth.service import AuthService
from src.core.dependencies import SessionDep


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=OAUTH_TOKEN_URL)


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    service: AuthServiceDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    return await service.get_user_from_access_token(token)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_admin_user(
    current_user: CurrentUserDep,
) -> User:
    from fastapi import HTTPException, status
    from src.auth.models import UserRole
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users are allowed to access this resource",
        )
    return current_user


CurrentAdminUserDep = Annotated[User, Depends(get_current_admin_user)]

