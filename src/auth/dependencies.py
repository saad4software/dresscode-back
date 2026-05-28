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
