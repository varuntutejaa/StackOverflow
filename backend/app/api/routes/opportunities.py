from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff
from app.api.pagination import CommonQuery, paginate
from app.db.session import get_db
from app.models.location import Location
from app.models.opportunity import Opportunity
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.opportunity import OpportunityCreate, OpportunityOut, OpportunityUpdate

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("", response_model=Page[OpportunityOut])
def list_opportunities(
    common: CommonQuery = Depends(),
    sector: Optional[str] = None,
    kind: Optional[str] = None,
    district: Optional[str] = None,
    skill_id: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Opportunity).outerjoin(Location, Opportunity.location_id == Location.id)
    if sector:
        stmt = stmt.where(Opportunity.sector.ilike(f"%{sector}%"))
    if kind:
        stmt = stmt.where(Opportunity.kind == kind)
    if district:
        stmt = stmt.where(Location.district.ilike(f"%{district}%"))
    if skill_id:
        stmt = stmt.where(Opportunity.skill_id == skill_id)
    if active_only:
        stmt = stmt.where(Opportunity.is_active.is_(True))
    if common.q:
        stmt = stmt.where(Opportunity.title.ilike(f"%{common.q}%"))
    items, total = paginate(db, stmt, common, Opportunity)
    return Page.build([OpportunityOut.model_validate(i) for i in items], total, common.page, common.page_size)


@router.post("", response_model=OpportunityOut, status_code=status.HTTP_201_CREATED)
def create_opportunity(payload: OpportunityCreate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    o = Opportunity(**payload.model_dump())
    db.add(o)
    db.commit()
    db.refresh(o)
    return OpportunityOut.model_validate(o)


@router.get("/{opportunity_id}", response_model=OpportunityOut)
def get_opportunity(opportunity_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = db.get(Opportunity, opportunity_id)
    if not o:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found")
    return OpportunityOut.model_validate(o)


@router.patch("/{opportunity_id}", response_model=OpportunityOut)
def update_opportunity(opportunity_id: str, payload: OpportunityUpdate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    o = db.get(Opportunity, opportunity_id)
    if not o:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(o, f, v)
    db.commit()
    db.refresh(o)
    return OpportunityOut.model_validate(o)


@router.delete("/{opportunity_id}", response_model=Message)
def delete_opportunity(opportunity_id: str, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    o = db.get(Opportunity, opportunity_id)
    if not o:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found")
    db.delete(o)
    db.commit()
    return Message(detail="Opportunity deleted")
