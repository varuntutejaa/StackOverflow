from typing import Optional

from fastapi import Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session


class CommonQuery:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=200),
        sort: Optional[str] = Query(None, description="Field name, prefix with '-' for descending"),
        q: Optional[str] = Query(None, description="Free-text search"),
    ):
        self.page = page
        self.page_size = page_size
        self.sort = sort
        self.q = q

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginate(db: Session, stmt, common: CommonQuery, model, sortable: Optional[dict] = None):
    """Return (items, total) applying sort + limit/offset to a select() stmt."""
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    if common.sort:
        field = common.sort.lstrip("-")
        direction = desc if common.sort.startswith("-") else asc
        col = (sortable or {}).get(field)
        if col is None and hasattr(model, field):
            col = getattr(model, field)
        if col is not None:
            stmt = stmt.order_by(direction(col))
    elif hasattr(model, "created_at"):
        stmt = stmt.order_by(desc(model.created_at))

    stmt = stmt.offset(common.offset).limit(common.page_size)
    items = list(db.execute(stmt).scalars().unique())
    return items, total
