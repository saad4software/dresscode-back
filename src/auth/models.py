from datetime import datetime, UTC
from typing import Optional
from enum import Enum

from sqlmodel import SQLModel, Field


class UserRole(str, Enum):
    client = "c"
    admin = "a"

class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=255, unique=True, index=True)
    disabled: bool = Field(default=False)
    role: UserRole = UserRole.client



class User(UserBase, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserRead(SQLModel):
    id: int
    username: str
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


class RefreshRequest(SQLModel):
    refresh_token: str


class TokenPair(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
