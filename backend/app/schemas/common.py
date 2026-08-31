from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Message(BaseModel):
    detail: str


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class Page(BaseModel, Generic[T]):
    items: List[T]
    meta: PageMeta

    @classmethod
    def build(cls, items: List[T], total: int, page: int, page_size: int) -> "Page[T]":
        pages = (total + page_size - 1) // page_size if page_size else 0
        return cls(items=items, meta=PageMeta(total=total, page=page, page_size=page_size, pages=pages))


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)
    sort: Optional[str] = None       # e.g. "-created_at"
    q: Optional[str] = None
