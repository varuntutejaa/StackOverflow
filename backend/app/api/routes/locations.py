from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff
from app.api.pagination import CommonQuery, paginate
from app.db.session import get_db
from app.models.location import Location
from app.models.user import User
from app.schemas.common import Page
from app.schemas.location import LocationCreate, LocationOut, LocationUpdate

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=Page[LocationOut])
def list_locations(
    common: CommonQuery = Depends(),
    state: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Location)
    if state:
        stmt = stmt.where(Location.state.ilike(f"%{state}%"))
    if district:
        stmt = stmt.where(Location.district.ilike(f"%{district}%"))
    if common.q:
        stmt = stmt.where(Location.district.ilike(f"%{common.q}%"))
    items, total = paginate(db, stmt, common, Location, sortable={"district": Location.district})
    return Page.build([LocationOut.model_validate(i) for i in items], total, common.page, common.page_size)


@router.get("/states", response_model=list[str])
def list_states(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [r[0] for r in db.execute(select(distinct(Location.state)).order_by(Location.state)).all()]


@router.get("/districts", response_model=list[str])
def list_districts(state: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(distinct(Location.district)).order_by(Location.district)
    if state:
        stmt = stmt.where(Location.state == state)
    return [r[0] for r in db.execute(stmt).all()]


@router.post("", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationCreate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    loc = Location(**payload.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return LocationOut.model_validate(loc)


@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
    return LocationOut.model_validate(loc)


@router.patch("/{location_id}", response_model=LocationOut)
def update_location(location_id: str, payload: LocationUpdate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(loc, f, v)
    db.commit()
    db.refresh(loc)
    return LocationOut.model_validate(loc)
