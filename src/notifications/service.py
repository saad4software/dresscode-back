from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.models import User
from src.core.models import IPageResponse
from src.core.pagination import paginate
from src.jobs.models import Job, JobStatus, JobType
from src.notifications.models import (
    DevicePlatform,
    DeviceToken,
    DeviceTokenCreate,
    Notification,
)
from src.notifications.push import send_push

_JOB_TITLES: dict[JobType, str] = {
    JobType.dress_from_image: "Wardrobe analysis",
    JobType.dress_analyze: "Dress analysis",
    JobType.outfit_from_images: "Outfit from images",
    JobType.event_suggest_outfits: "Outfit suggestions",
}


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register_device(
        self, user: User, data: DeviceTokenCreate
    ) -> DeviceToken:
        stmt = select(DeviceToken).where(DeviceToken.token == data.token)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if existing is not None:
            if existing.user_id != user.id:
                existing.user_id = user.id
            existing.platform = data.platform
            existing.last_used_at = now
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        device = DeviceToken(
            user_id=user.id,
            token=data.token,
            platform=data.platform,
            last_used_at=now,
        )
        self.session.add(device)
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def list_for_user(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> IPageResponse[list[Notification]]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)  # noqa: E712
        return await paginate(self.session, stmt, page, page_size)

    async def mark_read(self, user: User, notification_id: int) -> Notification:
        notification = await self.session.get(Notification, notification_id)
        if notification is None or notification.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        notification.is_read = True
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def notify_job(self, job: Job) -> Notification:
        label = _JOB_TITLES.get(job.job_type, "Background job")
        if job.status == JobStatus.succeeded:
            title = f"{label} complete"
            body = "Your request finished successfully."
        else:
            title = f"{label} failed"
            body = job.error or "Something went wrong. Please try again."

        data: dict[str, Any] = {
            "job_id": job.id,
            "job_type": job.job_type.value,
            "status": job.status.value,
        }
        notification = Notification(
            user_id=job.user_id,
            title=title,
            body=body,
            data=data,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)

        tokens = await self._tokens_for_user(job.user_id)
        if tokens:
            invalid = send_push(
                tokens=[t.token for t in tokens],
                title=title,
                body=body,
                data=data,
            )
            if invalid:
                await self._prune_tokens(invalid)

        return notification

    async def _tokens_for_user(self, user_id: int) -> list[DeviceToken]:
        stmt = select(DeviceToken).where(DeviceToken.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _prune_tokens(self, invalid_tokens: list[str]) -> None:
        stmt = select(DeviceToken).where(DeviceToken.token.in_(invalid_tokens))
        result = await self.session.execute(stmt)
        for device in result.scalars().all():
            await self.session.delete(device)
        await self.session.commit()
