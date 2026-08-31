from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff
from app.api.pagination import CommonQuery, paginate
from app.db.session import get_db
from app.models.beneficiary import Beneficiary
from app.models.enums import BeneficiaryStatus, OutcomeStage, OutcomeType
from app.models.outcome import Outcome
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.outcome import OutcomeCreate, OutcomeOut, OutcomeUpdate
from app.services import audit

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.get("", response_model=Page[OutcomeOut])
def list_outcomes(
    common: CommonQuery = Depends(),
    beneficiary_id: Optional[str] = None,
    stage: Optional[OutcomeStage] = None,
    outcome_type: Optional[OutcomeType] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Outcome)
    if beneficiary_id:
        stmt = stmt.where(Outcome.beneficiary_id == beneficiary_id)
    if stage:
        stmt = stmt.where(Outcome.stage == stage)
    if outcome_type:
        stmt = stmt.where(Outcome.outcome_type == outcome_type)
    if district:
        stmt = stmt.where(Outcome.district.ilike(f"%{district}%"))
    items, total = paginate(db, stmt, common, Outcome)
    return Page.build([OutcomeOut.model_validate(i) for i in items], total, common.page, common.page_size)


@router.post("", response_model=OutcomeOut, status_code=status.HTTP_201_CREATED)
def create_outcome(payload: OutcomeCreate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    beneficiary = db.get(Beneficiary, payload.beneficiary_id)
    if not beneficiary:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary not found")
    data = payload.model_dump()
    if not data.get("district") and beneficiary.location:
        data["district"] = beneficiary.location.district
    o = Outcome(**data)
    db.add(o)

    # keep the beneficiary lifecycle state consistent
    if o.stage == OutcomeStage.EMPLOYMENT or o.outcome_type == OutcomeType.WAGE_EMPLOYMENT:
        beneficiary.status = BeneficiaryStatus.PLACED
    elif o.stage == OutcomeStage.SELF_EMPLOYMENT or o.outcome_type == OutcomeType.SELF_EMPLOYMENT:
        beneficiary.status = BeneficiaryStatus.SELF_EMPLOYED

    db.commit()
    db.refresh(o)
    audit.record(db, action="outcome.create", actor=user, entity_type="outcome", entity_id=o.id)
    return OutcomeOut.model_validate(o)


@router.get("/{outcome_id}", response_model=OutcomeOut)
def get_outcome(outcome_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = db.get(Outcome, outcome_id)
    if not o:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Outcome not found")
    return OutcomeOut.model_validate(o)


@router.patch("/{outcome_id}", response_model=OutcomeOut)
def update_outcome(outcome_id: str, payload: OutcomeUpdate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    o = db.get(Outcome, outcome_id)
    if not o:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Outcome not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(o, f, v)
    db.commit()
    db.refresh(o)
    return OutcomeOut.model_validate(o)


@router.delete("/{outcome_id}", response_model=Message)
def delete_outcome(outcome_id: str, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    o = db.get(Outcome, outcome_id)
    if not o:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Outcome not found")
    db.delete(o)
    db.commit()
    return Message(detail="Outcome deleted")
