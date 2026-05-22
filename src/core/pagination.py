from math import ceil
from typing import TypeVar

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlmodel.sql.expression import SelectOfScalar

from src.core.models import IPageResponse

T = TypeVar("T")


async def paginate(
    session: AsyncSession,
    stmt: SelectOfScalar[T],
    page: int,
    page_size: int,
) -> IPageResponse[list[T]]:
    page = max(page, 1)
    page_size = max(page_size, 1)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_items = (await session.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    result = await session.execute(stmt.offset(offset).limit(page_size))
    items = list(result.scalars().all())

    total_pages = ceil(total_items / page_size) if total_items > 0 else 0

    return IPageResponse(
        page=page,
        total_items=total_items,
        total_pages=total_pages,
        results=items,
    )
