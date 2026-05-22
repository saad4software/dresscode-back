import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.config import config
from src.auth.models import (
    TokenPair,
    User,
    UserCreate,
)


_password_hash = PasswordHash.recommended()

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _to_utc(dt: datetime) -> datetime:
    """Return `dt` as a timezone-aware UTC datetime.

    SQLite returns naive datetimes; we treat those as UTC since we always
    persist with `datetime.now(timezone.utc)`.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _hash_password(self, password: str) -> str:
        return _password_hash.hash(password)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def register(self, data: UserCreate) -> User:
        existing = await self.get_user_by_username(data.username)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        user = User(
            username=data.username,
            hashed_password=self._hash_password(data.password),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def login(self, username: str, password: str) -> TokenPair:
        user = await self.authenticate(username, password)
        return self._issue_token_pair(user)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return _password_hash.verify(plain_password, hashed_password)

    async def authenticate(self, username: str, password: str) -> User:
        user = await self.get_user_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not self._verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )
        return user

    def _issue_token_pair(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=self._encode_access_token(user),
            refresh_token=self._encode_refresh_token(user),
        )

    def _encode_access_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.username,
            "uid": user.id,
            "type": ACCESS_TOKEN_TYPE,
            "iat": now.timestamp(),
            "exp": int(
                (now + timedelta(minutes=config.jwt_access_exp_minutes)).timestamp()
            ),
        }
        return jwt.encode(
            payload, config.jwt_secret_key, algorithm=config.jwt_algorithm
        )

    def _encode_refresh_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.username,
            "uid": user.id,
            "type": REFRESH_TOKEN_TYPE,
            "jti": uuid.uuid4().hex,
            "iat": now.timestamp(),
            "exp": int(
                (now + timedelta(days=config.jwt_refresh_exp_days)).timestamp()
            ),
        }
        return jwt.encode(
            payload, config.jwt_secret_key, algorithm=config.jwt_algorithm
        )

    def _decode_token(self, token: str, expected_type: str) -> dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token,
                config.jwt_secret_key,
                algorithms=[config.jwt_algorithm],
            )
        except InvalidTokenError:
            raise credentials_exception
        if payload.get("type") != expected_type:
            raise credentials_exception
        return payload

    def _ensure_token_not_invalidated(self, payload: dict, user: User) -> None:
        """Reject tokens issued before the user's invalidation watermark.

        We use `User.updated_at` as a global "tokens-invalid-before" marker.
        Any state change that should revoke outstanding tokens (currently:
        password change) bumps this field, which transparently invalidates
        every token whose `iat` precedes it -- without persisting individual
        token state.
        """
        token_iat = payload.get("iat")
        if token_iat is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        invalid_before = _to_utc(user.updated_at).timestamp()
        if float(token_iat) < invalid_before:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated, please log in again",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = self._decode_token(refresh_token, REFRESH_TOKEN_TYPE)
        user_id = payload.get("uid")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = await self.get_user_by_id(user_id)
        if user is None or user.disabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer active",
            )

        self._ensure_token_not_invalidated(payload, user)

        return self._issue_token_pair(user)

    async def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        if not self._verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must differ from current password",
            )
        user.hashed_password = self._hash_password(new_password)
        # Bump the "tokens-invalid-before" watermark. Token `iat` is encoded
        # with sub-second precision, so any token issued strictly before this
        # moment -- including the access token used to authorize the current
        # request -- is invalidated by the `_ensure_token_not_invalidated`
        # check.
        user.updated_at = datetime.now(timezone.utc)
        self.session.add(user)
        await self.session.commit()

    async def get_user_from_access_token(self, token: str) -> User:
        payload = self._decode_token(token, ACCESS_TOKEN_TYPE)
        user_id = payload.get("uid")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )
        self._ensure_token_not_invalidated(payload, user)
        return user
