import asyncio
import logging
from typing import Any

from fastapi import HTTPException

from src.ai.outfit_service import OutfitSuggestionService
from src.ai.service import AIService
from src.auth.models import User
from src.core.celery_app import celery_app
from src.core.dependencies import SessionLocal
from src.dress.models import DressAnalyzeResponse, DressCreateFromImageResponse, DressRead
from src.dress.service import DressService
from src.event.service import EventService
from src.jobs.service import JobService
from src.media.service import MediaService
from src.notifications.service import NotificationService
from src.outfit.models import OutfitFromImagesResponse
from src.outfit.service import OutfitService, outfit_to_read

logger = logging.getLogger(__name__)


def _error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        return str(detail)
    return str(exc) or exc.__class__.__name__


async def _finalize_job(
    job_service: JobService,
    notification_service: NotificationService,
    job_id: int,
    *,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    if error is not None:
        job = await job_service.mark_failed(job_id, error)
    else:
        job = await job_service.mark_succeeded(job_id, result or {})
    try:
        await notification_service.notify_job(job)
    except Exception:
        logger.exception("Failed to send notification for job %s", job_id)


async def _run_dress_from_image(job_id: int, user_id: int, media_id: int) -> None:
    async with SessionLocal() as session:
        job_service = JobService(session)
        dress_service = DressService(session)
        media_service = MediaService(session)
        notification_service = NotificationService(session)
        await job_service.mark_processing(job_id)
        try:
            dresses, returned_media_id = await dress_service.analyze_from_image(
                user_id, media_id, media_service
            )
            payload = DressCreateFromImageResponse(
                dresses=[
                    DressRead.model_validate(d, from_attributes=True) for d in dresses
                ],
                media_id=returned_media_id,
            )
            await _finalize_job(
                job_service,
                notification_service,
                job_id,
                result=payload.model_dump(mode="json"),
            )
        except Exception as exc:
            logger.exception("Job %s dress_from_image failed", job_id)
            await _finalize_job(
                job_service,
                notification_service,
                job_id,
                error=_error_message(exc),
            )


async def _run_dress_analyze(job_id: int, user_id: int, dress_id: int) -> None:
    async with SessionLocal() as session:
        job_service = JobService(session)
        dress_service = DressService(session)
        notification_service = NotificationService(session)
        ai_service = AIService(session)
        await job_service.mark_processing(job_id)
        try:
            user = await session.get(User, user_id)
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            dress = await dress_service.get_for_user(user, dress_id)
            result = await ai_service.analyze_dress(dress)
            refreshed = await dress_service.get_for_user(user, dress_id)
            payload = DressAnalyzeResponse(
                dress=DressRead.model_validate(refreshed, from_attributes=True),
                analyzed_media_ids=result.analyzed_media_ids,
                failed_media_ids=result.failed_media_ids,
            )
            await _finalize_job(
                job_service,
                notification_service,
                job_id,
                result=payload.model_dump(mode="json"),
            )
        except Exception as exc:
            logger.exception("Job %s dress_analyze failed", job_id)
            await _finalize_job(
                job_service,
                notification_service,
                job_id,
                error=_error_message(exc),
            )


async def _run_outfit_from_images(
    job_id: int, user_id: int, media_ids: list[int]
) -> None:
    async with SessionLocal() as session:
        job_service = JobService(session)
        dress_service = DressService(session)
        media_service = MediaService(session)
        outfit_service = OutfitService(session)
        notification_service = NotificationService(session)
        await job_service.mark_processing(job_id)
        try:
            outfit, returned_media_ids = await outfit_service.create_from_uploaded_media(
                user_id, media_ids, dress_service, media_service
            )
            payload = OutfitFromImagesResponse(
                outfit=outfit_to_read(outfit),
                media_ids=returned_media_ids,
            )
            await _finalize_job(
                job_service,
                notification_service,
                job_id,
                result=payload.model_dump(mode="json"),
            )
        except Exception as exc:
            logger.exception("Job %s outfit_from_images failed", job_id)
            await _finalize_job(
                job_service,
                notification_service,
                job_id,
                error=_error_message(exc),
            )


async def _run_event_suggest_outfits(
    job_id: int, user_id: int, event_id: int
) -> None:
    async with SessionLocal() as session:
        job_service = JobService(session)
        event_service = EventService(session)
        dress_service = DressService(session)
        outfit_service = OutfitService(session)
        outfit_suggestion_service = OutfitSuggestionService(session)
        notification_service = NotificationService(session)
        await job_service.mark_processing(job_id)
        try:
            user = await session.get(User, user_id)
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            event = await event_service.get_for_user(user, event_id)
            outfits = await outfit_suggestion_service.suggest_for_event(
                user,
                event,
                event_service,
                dress_service,
                outfit_service,
            )
            await _finalize_job(
                job_service,
                notification_service,
                job_id,
                result={
                    "outfits": [
                        o.model_dump(mode="json") for o in outfits
                    ]
                },
            )
        except Exception as exc:
            logger.exception("Job %s event_suggest_outfits failed", job_id)
            await _finalize_job(
                job_service,
                notification_service,
                job_id,
                error=_error_message(exc),
            )


@celery_app.task(bind=True, name="jobs.run_dress_from_image")
def run_dress_from_image(self, job_id: int, user_id: int, media_id: int) -> None:
    asyncio.run(_run_dress_from_image(job_id, user_id, media_id))


@celery_app.task(bind=True, name="jobs.run_dress_analyze")
def run_dress_analyze(self, job_id: int, user_id: int, dress_id: int) -> None:
    asyncio.run(_run_dress_analyze(job_id, user_id, dress_id))


@celery_app.task(bind=True, name="jobs.run_outfit_from_images")
def run_outfit_from_images(
    self, job_id: int, user_id: int, media_ids: list[int]
) -> None:
    asyncio.run(_run_outfit_from_images(job_id, user_id, media_ids))


@celery_app.task(bind=True, name="jobs.run_event_suggest_outfits")
def run_event_suggest_outfits(
    self, job_id: int, user_id: int, event_id: int
) -> None:
    asyncio.run(_run_event_suggest_outfits(job_id, user_id, event_id))
