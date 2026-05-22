from fastapi import APIRouter, Query, status

from src.ai.dependencies import OutfitServiceDep
from src.auth.dependencies import CurrentUserDep
from src.core.models import IPageResponse
from src.dress.dependencies import DressServiceDep
from src.event.cities import CITY_COORDINATES, GermanCity
from src.event.dependencies import EventServiceDep
from src.event.models import (
    CityOption,
    EventCreate,
    EventRead,
    EventUpdate,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/cities", response_model=list[CityOption])
async def list_cities() -> list[CityOption]:
    return [
        CityOption(slug=slug, display_name=meta[0])
        for slug, meta in CITY_COORDINATES.items()
    ]


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    service: EventServiceDep,
    current_user: CurrentUserDep,
) -> EventRead:
    event = await service.create(current_user, data)
    return EventRead.model_validate(event, from_attributes=True)


@router.get("", response_model=IPageResponse[list[EventRead]])
async def list_events(
    service: EventServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> IPageResponse[list[EventRead]]:
    result = await service.list_for_user(
        current_user, page=page, page_size=page_size
    )
    return IPageResponse(
        page=result.page,
        total_items=result.total_items,
        total_pages=result.total_pages,
        results=[
            EventRead.model_validate(e, from_attributes=True)
            for e in result.results or []
        ],
    )


@router.get("/{event_id}", response_model=EventRead)
async def get_event(
    event_id: int,
    service: EventServiceDep,
    current_user: CurrentUserDep,
) -> EventRead:
    event = await service.get_for_user(current_user, event_id)
    return EventRead.model_validate(event, from_attributes=True)


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int,
    data: EventUpdate,
    service: EventServiceDep,
    current_user: CurrentUserDep,
) -> EventRead:
    event = await service.update(current_user, event_id, data)
    return EventRead.model_validate(event, from_attributes=True)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    service: EventServiceDep,
    current_user: CurrentUserDep,
) -> None:
    await service.delete(current_user, event_id)


@router.post("/{event_id}/suggest-outfits")
async def suggest_outfits(
    event_id: int,
    event_service: EventServiceDep,
    dress_service: DressServiceDep,
    outfit_service: OutfitServiceDep,
    current_user: CurrentUserDep,
):
    event = await event_service.get_for_user(current_user, event_id)
    return await outfit_service.suggest_for_event(
        current_user, event, event_service, dress_service
    )
