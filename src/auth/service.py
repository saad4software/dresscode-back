import asyncio
import logging
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.constants import (
    ACCESS_TOKEN_TYPE,
    BEARER_AUTH_HEADER,
    DETAIL_COULD_NOT_VALIDATE_CREDENTIALS,
    DETAIL_CURRENT_PASSWORD_INCORRECT,
    DETAIL_EMAIL_ALREADY_VERIFIED,
    DETAIL_EMAIL_NOT_VERIFIED,
    DETAIL_INVALID_ACCESS_TOKEN,
    DETAIL_INVALID_OR_EXPIRED_CODE,
    DETAIL_INVALID_REFRESH_TOKEN,
    DETAIL_INVALID_USERNAME_OR_PASSWORD,
    DETAIL_NEW_PASSWORD_MUST_DIFFER,
    DETAIL_TOKEN_INVALIDATED,
    DETAIL_USER_DISABLED,
    DETAIL_USER_MUST_BE_SAVED,
    DETAIL_USER_NO_LONGER_ACTIVE,
    DETAIL_USER_NOT_FOUND,
    DETAIL_USERNAME_MUST_BE_EMAIL,
    DETAIL_USERNAME_TAKEN,
    DETAIL_VERIFICATION_EMAIL_NOT_SENT,
    EMAIL_CODE_EXPIRY_LINE_TEMPLATE,
    EMAIL_CODE_LINE_TEMPLATE,
    EMAIL_CODE_TYPE_VALUES,
    EMAIL_HEADER_FROM,
    EMAIL_HEADER_SUBJECT,
    EMAIL_HEADER_TO,
    EMAIL_IGNORE_LINE,
    EMAIL_SUBJECT_TEMPLATE,
    JWT_EXPIRES_AT_CLAIM,
    JWT_ID_CLAIM,
    JWT_ISSUED_AT_CLAIM,
    JWT_SUBJECT_CLAIM,
    JWT_TYPE_CLAIM,
    JWT_USER_ID_CLAIM,
    LOG_VERIFICATION_CODE_TEMPLATE,
    REFRESH_TOKEN_TYPE,
)
from src.auth.models import (
    TokenPair,
    User,
    UserCreate,
    VerificationCode,
    VerificationCodeType,
)
from src.auth.utils import (
    generate_numeric_code,
    hash_secret,
    is_valid_email,
    normalize_email,
    to_utc,
    verify_secret,
)
from src.core.config import config


logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_username(self, username: str) -> Optional[User]:
        username = normalize_email(username)
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def register(self, data: UserCreate) -> User:
        username = normalize_email(data.username)
        existing = await self.get_user_by_username(username)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=DETAIL_USERNAME_TAKEN,
            )
        if config.email_verification_required and not is_valid_email(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_USERNAME_MUST_BE_EMAIL,
            )

        now = datetime.now(timezone.utc)
        user = User(
            username=username,
            hashed_password=hash_secret(data.password),
            email_verified=not config.email_verification_required,
            email_verified_at=now if not config.email_verification_required else None,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        if config.email_verification_required:
            await self.create_and_send_verification_code(
                user,
                VerificationCodeType.verify_email,
                sent_to=user.username,
            )
        return user

    async def login(self, username: str, password: str) -> TokenPair:
        user = await self.authenticate(username, password, require_verified=True)
        return self._issue_token_pair(user)

    async def authenticate(
        self, username: str, password: str, require_verified: bool = False
    ) -> User:
        user = await self.get_user_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=DETAIL_INVALID_USERNAME_OR_PASSWORD,
                headers=BEARER_AUTH_HEADER,
            )
        if not verify_secret(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=DETAIL_INVALID_USERNAME_OR_PASSWORD,
                headers=BEARER_AUTH_HEADER,
            )
        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=DETAIL_USER_DISABLED,
            )
        if (
            require_verified
            and config.email_verification_required
            and not user.email_verified
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=DETAIL_EMAIL_NOT_VERIFIED,
            )
        return user

    async def create_and_send_verification_code(
        self,
        user: User,
        code_type: VerificationCodeType,
        sent_to: str,
    ) -> VerificationCode:
        sent_to = normalize_email(sent_to)
        if code_type.value in EMAIL_CODE_TYPE_VALUES and not is_valid_email(sent_to):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_USERNAME_MUST_BE_EMAIL,
            )
        if user.id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_USER_MUST_BE_SAVED,
            )

        code = generate_numeric_code(config.email_verification_code_length)
        now = datetime.now(timezone.utc)
        await self._expire_existing_verification_codes(user, code_type, now)
        verification_code = VerificationCode(
            user_id=user.id,
            code_type=code_type,
            code_hash=hash_secret(code),
            sent_to=sent_to,
            expires_at=now
            + timedelta(minutes=config.email_verification_code_exp_minutes),
            created_at=now,
        )
        self.session.add(verification_code)
        await self.session.commit()
        await self.session.refresh(verification_code)

        if code_type.value in EMAIL_CODE_TYPE_VALUES:
            await self._send_verification_code(sent_to, code, code_type)
        return verification_code

    async def _expire_existing_verification_codes(
        self,
        user: User,
        code_type: VerificationCodeType,
        now: datetime,
    ) -> None:
        result = await self.session.execute(
            select(VerificationCode)
            .where(VerificationCode.user_id == user.id)
            .where(VerificationCode.code_type == code_type)
            .where(VerificationCode.used_at.is_(None))
        )
        for verification_code in result.scalars().all():
            verification_code.used_at = now
            self.session.add(verification_code)

    async def _get_active_verification_code(
        self,
        user: User,
        code_type: VerificationCodeType,
        code: str,
    ) -> VerificationCode:
        result = await self.session.execute(
            select(VerificationCode)
            .where(VerificationCode.user_id == user.id)
            .where(VerificationCode.code_type == code_type)
            .where(VerificationCode.used_at.is_(None))
            .order_by(VerificationCode.created_at.desc())
        )
        verification_codes = result.scalars().all()
        now = datetime.now(timezone.utc)
        for verification_code in verification_codes:
            if to_utc(verification_code.expires_at) < now:
                continue
            if verify_secret(code, verification_code.code_hash):
                return verification_code
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=DETAIL_INVALID_OR_EXPIRED_CODE,
        )

    async def _send_verification_code(
        self,
        to_email: str,
        code: str,
        code_type: VerificationCodeType,
    ) -> None:
        if not is_valid_email(to_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_USERNAME_MUST_BE_EMAIL,
            )
        try:
            if not config.smtp_host:
                logger.info(
                    LOG_VERIFICATION_CODE_TEMPLATE,
                    code_type.value,
                    to_email,
                    code,
                )
                return
            await asyncio.to_thread(self._send_email_verification_code, to_email, code)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=DETAIL_VERIFICATION_EMAIL_NOT_SENT,
            )

    def _send_email_verification_code(self, to_email: str, code: str) -> None:
        message = EmailMessage()
        message[EMAIL_HEADER_SUBJECT] = EMAIL_SUBJECT_TEMPLATE.format(
            app_name=config.app_name
        )
        message[EMAIL_HEADER_FROM] = config.smtp_from_email
        message[EMAIL_HEADER_TO] = to_email
        message.set_content(
            "\n".join(
                [
                    EMAIL_CODE_LINE_TEMPLATE.format(
                        app_name=config.app_name,
                        code=code,
                    ),
                    "",
                    EMAIL_CODE_EXPIRY_LINE_TEMPLATE.format(
                        minutes=config.email_verification_code_exp_minutes
                    ),
                    EMAIL_IGNORE_LINE,
                ]
            )
        )

        if config.smtp_use_tls:
            with smtplib.SMTP(
                config.smtp_host,
                config.smtp_port,
                timeout=config.smtp_timeout_seconds,
            ) as server:
                server.starttls()
                self._login_to_smtp_if_configured(server)
                server.send_message(message)
            return

        with smtplib.SMTP_SSL(
            config.smtp_host,
            config.smtp_port,
            timeout=config.smtp_timeout_seconds,
        ) as server:
            self._login_to_smtp_if_configured(server)
            server.send_message(message)

    def _login_to_smtp_if_configured(self, server: smtplib.SMTP) -> None:
        if config.smtp_username and config.smtp_password:
            server.login(config.smtp_username, config.smtp_password)

    async def verify_email(self, username: str, code: str) -> User:
        username = normalize_email(username)
        user = await self.get_user_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_INVALID_OR_EXPIRED_CODE,
            )
        if user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_EMAIL_ALREADY_VERIFIED,
            )

        now = datetime.now(timezone.utc)
        verification_code = await self._get_active_verification_code(
            user,
            VerificationCodeType.verify_email,
            code,
        )
        verification_code.used_at = now
        user.email_verified = True
        user.email_verified_at = now
        user.updated_at = now
        self.session.add(verification_code)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def resend_verification_code(self, username: str, password: str) -> None:
        username = normalize_email(username)
        if not is_valid_email(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_USERNAME_MUST_BE_EMAIL,
            )
        user = await self.authenticate(username, password, require_verified=False)
        if user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_EMAIL_ALREADY_VERIFIED,
            )
        await self.create_and_send_verification_code(
            user,
            VerificationCodeType.verify_email,
            sent_to=user.username,
        )

    def _issue_token_pair(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=self._encode_access_token(user),
            refresh_token=self._encode_refresh_token(user),
        )

    def _encode_access_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            JWT_SUBJECT_CLAIM: user.username,
            JWT_USER_ID_CLAIM: user.id,
            JWT_TYPE_CLAIM: ACCESS_TOKEN_TYPE,
            JWT_ISSUED_AT_CLAIM: now.timestamp(),
            JWT_EXPIRES_AT_CLAIM: int(
                (now + timedelta(minutes=config.jwt_access_exp_minutes)).timestamp()
            ),
        }
        return jwt.encode(
            payload, config.jwt_secret_key, algorithm=config.jwt_algorithm
        )

    def _encode_refresh_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            JWT_SUBJECT_CLAIM: user.username,
            JWT_USER_ID_CLAIM: user.id,
            JWT_TYPE_CLAIM: REFRESH_TOKEN_TYPE,
            JWT_ID_CLAIM: uuid.uuid4().hex,
            JWT_ISSUED_AT_CLAIM: now.timestamp(),
            JWT_EXPIRES_AT_CLAIM: int(
                (now + timedelta(days=config.jwt_refresh_exp_days)).timestamp()
            ),
        }
        return jwt.encode(
            payload, config.jwt_secret_key, algorithm=config.jwt_algorithm
        )

    def _decode_token(self, token: str, expected_type: str) -> dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=DETAIL_COULD_NOT_VALIDATE_CREDENTIALS,
            headers=BEARER_AUTH_HEADER,
        )
        try:
            payload = jwt.decode(
                token,
                config.jwt_secret_key,
                algorithms=[config.jwt_algorithm],
            )
        except InvalidTokenError:
            raise credentials_exception
        if payload.get(JWT_TYPE_CLAIM) != expected_type:
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
        token_iat = payload.get(JWT_ISSUED_AT_CLAIM)
        if token_iat is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=DETAIL_COULD_NOT_VALIDATE_CREDENTIALS,
                headers=BEARER_AUTH_HEADER,
            )
        invalid_before = to_utc(user.updated_at).timestamp()
        if float(token_iat) < invalid_before:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=DETAIL_TOKEN_INVALIDATED,
                headers=BEARER_AUTH_HEADER,
            )

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = self._decode_token(refresh_token, REFRESH_TOKEN_TYPE)
        user_id = payload.get(JWT_USER_ID_CLAIM)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=DETAIL_INVALID_REFRESH_TOKEN,
            )

        user = await self.get_user_by_id(user_id)
        if user is None or user.disabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=DETAIL_USER_NO_LONGER_ACTIVE,
            )

        self._ensure_token_not_invalidated(payload, user)

        return self._issue_token_pair(user)

    async def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        if not verify_secret(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_CURRENT_PASSWORD_INCORRECT,
            )
        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DETAIL_NEW_PASSWORD_MUST_DIFFER,
            )
        user.hashed_password = hash_secret(new_password)
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
        user_id = payload.get(JWT_USER_ID_CLAIM)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=DETAIL_INVALID_ACCESS_TOKEN,
                headers=BEARER_AUTH_HEADER,
            )
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=DETAIL_USER_NOT_FOUND,
                headers=BEARER_AUTH_HEADER,
            )
        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=DETAIL_USER_DISABLED,
            )
        self._ensure_token_not_invalidated(payload, user)
        return user
