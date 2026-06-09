from fastapi import APIRouter, Query, status
from sqlmodel import select

from src.auth.dependencies import CurrentUserDep
from src.core.dependencies import SessionDep
from src.core.models import IPageResponse
from src.admin.models import City
from src.event.dependencies import EventServiceDep
from src.event.models import (
    CityOption,
    EventCreate,
    EventDetailRead,
    EventRead,
    EventUpdate,
)
from src.outfit.dependencies import OutfitServiceDep
from src.outfit.service import outfit_to_read
from src.jobs.dependencies import JobServiceDep
from src.jobs.enqueue import enqueue_job
from src.jobs.models import JobRead, JobType
from src.jobs.service import job_to_read
from src.admin.models import (
    EventTypeRead,
    EventType,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/cities", response_model=list[CityOption])
async def list_cities(session: SessionDep) -> list[CityOption]:
    stmt = select(City).order_by(City.display_name)
    res = await session.execute(stmt)
    cities = res.scalars().all()
    return [
        CityOption(slug=c.slug, display_name=c.display_name)
        for c in cities
    ]



@router.get("/event-types", response_model=list[EventTypeRead])
async def list_event_types(
    session: SessionDep,
) -> list[EventTypeRead]:
    stmt = select(EventType).order_by(EventType.display_name)
    res = await session.execute(stmt)
    ets = res.scalars().all()
    return [EventTypeRead.model_validate(et) for et in ets]


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    service: EventServiceDep,
    current_user: CurrentUserDep,
) -> EventRead:
    event = await service.create(current_user, data)
    return EventRead.from_event(event)


@router.get("", response_model=IPageResponse[list[EventRead]])
async def list_events(
    service: EventServiceDep,
    outfit_service: OutfitServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> IPageResponse[list[EventRead]]:
    result = await service.list_for_user(
        current_user, page=page, page_size=page_size
    )
    events = result.results or []
    event_ids = [event.id for event in events]
    with_suggestions = await outfit_service.event_ids_with_suggestions(
        current_user, event_ids
    )
    return IPageResponse(
        page=result.page,
        total_items=result.total_items,
        total_pages=result.total_pages,
        results=[
            EventRead.from_event(
                event,
                has_outfit_suggestions=event.id in with_suggestions,
            )
            for event in events
        ],
    )


@router.get("/{event_id}", response_model=EventDetailRead)
async def get_event(
    event_id: int,
    service: EventServiceDep,
    outfit_service: OutfitServiceDep,
    current_user: CurrentUserDep,
) -> EventDetailRead:
    event = await service.get_for_user(current_user, event_id)
    outfits = await outfit_service.list_for_event(current_user, event_id)
    return EventDetailRead.from_event(
        event,
        outfit_suggestions=[outfit_to_read(outfit) for outfit in outfits],
    )


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int,
    data: EventUpdate,
    service: EventServiceDep,
    outfit_service: OutfitServiceDep,
    current_user: CurrentUserDep,
) -> EventRead:
    event = await service.update(current_user, event_id, data)
    has_suggestions = await outfit_service.has_for_event(current_user, event_id)
    return EventRead.from_event(event, has_outfit_suggestions=has_suggestions)


@router.delete("/{event_id}", response_model=EventRead)
async def delete_event(
    event_id: int,
    service: EventServiceDep,
    outfit_service: OutfitServiceDep,
    current_user: CurrentUserDep,
) -> EventRead:
    has_suggestions = await outfit_service.has_for_event(current_user, event_id)
    event = await service.delete(current_user, event_id)
    return EventRead.from_event(event, has_outfit_suggestions=has_suggestions)


@router.post(
    "/{event_id}/suggest-outfits",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def suggest_outfits(
    event_id: int,
    event_service: EventServiceDep,
    job_service: JobServiceDep,
    current_user: CurrentUserDep,
) -> JobRead:
    await event_service.get_for_user(current_user, event_id)
    job = await job_service.create(
        current_user,
        JobType.event_suggest_outfits,
        {"event_id": event_id},
    )
    celery_task_id = enqueue_job(job)
    job = await job_service.set_celery_task_id(job, celery_task_id)
    return job_to_read(job)
