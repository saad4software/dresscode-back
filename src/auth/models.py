from datetime import datetime, UTC
from typing import Optional
from enum import Enum

from sqlmodel import SQLModel, Field

from src.auth.constants import (
    BEARER_TOKEN_TYPE,
    CHANGE_EMAIL_CODE_TYPE,
    FORGET_PASSWORD_CODE_TYPE,
    USER_ROLE_ADMIN,
    USER_ROLE_CLIENT,
    USER_ID_FOREIGN_KEY,
    USER_TABLE_NAME,
    VERIFICATION_CODE_TABLE_NAME,
    VERIFY_EMAIL_CODE_TYPE,
)


class UserRole(str, Enum):
    client = USER_ROLE_CLIENT
    admin = USER_ROLE_ADMIN


class VerificationCodeType(str, Enum):
    verify_email = VERIFY_EMAIL_CODE_TYPE
    forget_password = FORGET_PASSWORD_CODE_TYPE
    change_email = CHANGE_EMAIL_CODE_TYPE


class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=255, unique=True, index=True)
    disabled: bool = Field(default=False)
    role: UserRole = UserRole.client


class User(UserBase, table=True):
    __tablename__ = USER_TABLE_NAME

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(max_length=255)
    email_verified: bool = Field(default=False)
    email_verified_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class VerificationCode(SQLModel, table=True):
    __tablename__ = VERIFICATION_CODE_TABLE_NAME

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key=USER_ID_FOREIGN_KEY, index=True)
    code_type: VerificationCodeType = Field(index=True)
    code_hash: str = Field(max_length=255)
    sent_to: str = Field(max_length=255, index=True)
    expires_at: datetime
    used_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserRead(SQLModel):
    id: int
    username: str
    email_verified: bool
    disabled: bool
    created_at: datetime


class UserCreate(SQLModel):
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(SQLModel):
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(SQLModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(SQLModel):
    username: str = Field(min_length=3, max_length=255)
    code: str = Field(min_length=4, max_length=12)


class ResendVerificationCodeRequest(SQLModel):
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(SQLModel):
    refresh_token: str


class TokenPair(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = BEARER_TOKEN_TYPE


class TokenData(SQLModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
