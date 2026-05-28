import re
import secrets
from datetime import datetime, timezone

from pwdlib import PasswordHash

from src.auth.constants import (
    EMAIL_REGEX,
    MAX_VERIFICATION_CODE_LENGTH,
    MIN_VERIFICATION_CODE_LENGTH,
)


_password_hash = PasswordHash.recommended()
_EMAIL_RE = re.compile(EMAIL_REGEX)


def hash_secret(secret: str) -> str:
    return _password_hash.hash(secret)


def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
    return _password_hash.verify(plain_secret, hashed_secret)


def generate_numeric_code(length: int) -> str:
    length = min(
        max(length, MIN_VERIFICATION_CODE_LENGTH),
        MAX_VERIFICATION_CODE_LENGTH,
    )
    return str(secrets.randbelow(10**length)).zfill(length)


def is_valid_email(value: str) -> bool:
    return bool(_EMAIL_RE.fullmatch(value))


def normalize_email(value: str) -> str:
    return value.strip().lower()


def to_utc(dt: datetime) -> datetime:
    """Return `dt` as a timezone-aware UTC datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
