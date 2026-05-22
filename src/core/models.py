from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")


class IPageResponse(BaseModel, Generic[T]):
    page: int
    total_items: int
    total_pages: int
    results: T | None = None


class IResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: T | None = None