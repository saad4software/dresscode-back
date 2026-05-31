from fastapi import APIRouter, status
from src.auth.dependencies import CurrentAdminUserDep
from src.admin.dependencies import AdminServiceDep
from src.admin.models import (
    CityCreate, CityRead,
    EventTypeCreate, EventTypeRead,
    DressCategoryCreate, DressCategoryRead
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/cities", response_model=CityRead, status_code=status.HTTP_201_CREATED)
async def create_city(
    data: CityCreate,
    service: AdminServiceDep,
    admin_user: CurrentAdminUserDep,
) -> CityRead:
    city = await service.create_city(data)
    return CityRead.model_validate(city)


@router.get("/cities", response_model=list[CityRead])
async def list_cities(
    service: AdminServiceDep,
    admin_user: CurrentAdminUserDep,
) -> list[CityRead]:
    cities = await service.list_cities()
    return [CityRead.model_validate(c) for c in cities]


@router.post("/event-types", response_model=EventTypeRead, status_code=status.HTTP_201_CREATED)
async def create_event_type(
    data: EventTypeCreate,
    service: AdminServiceDep,
    admin_user: CurrentAdminUserDep,
) -> EventTypeRead:
    et = await service.create_event_type(data)
    return EventTypeRead.model_validate(et)


@router.get("/event-types", response_model=list[EventTypeRead])
async def list_event_types(
    service: AdminServiceDep,
    admin_user: CurrentAdminUserDep,
) -> list[EventTypeRead]:
    ets = await service.list_event_types()
    return [EventTypeRead.model_validate(et) for et in ets]


@router.post("/dress-categories", response_model=DressCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_dress_category(
    data: DressCategoryCreate,
    service: AdminServiceDep,
    admin_user: CurrentAdminUserDep,
) -> DressCategoryRead:
    dc = await service.create_dress_category(data)
    return DressCategoryRead.model_validate(dc)


@router.get("/dress-categories", response_model=list[DressCategoryRead])
async def list_dress_categories(
    service: AdminServiceDep,
    admin_user: CurrentAdminUserDep,
) -> list[DressCategoryRead]:
    dcs = await service.list_dress_categories()
    return [DressCategoryRead.model_validate(dc) for dc in dcs]
