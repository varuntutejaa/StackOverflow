from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_provider_staff, require_staff
from app.api.pagination import CommonQuery, paginate
from app.db.session import get_db
from app.models.enums import TrainingStatus
from app.models.location import Location
from app.models.skill import Skill
from app.models.training import TrainingProgram, TrainingProvider
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.training import (
    TrainingProgramCreate,
    TrainingProgramOut,
    TrainingProgramUpdate,
    TrainingProviderCreate,
    TrainingProviderOut,
    TrainingProviderUpdate,
)

router = APIRouter(tags=["training"])
providers_router = APIRouter(prefix="/training-providers")
programs_router = APIRouter(prefix="/training-programs")


# ── Providers ──────────────────────────────────────────────
@providers_router.get("", response_model=Page[TrainingProviderOut])
def list_providers(
    common: CommonQuery = Depends(),
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(TrainingProvider)
    if type:
        stmt = stmt.where(TrainingProvider.type == type)
    if common.q:
        stmt = stmt.where(TrainingProvider.name.ilike(f"%{common.q}%"))
    items, total = paginate(db, stmt, common, TrainingProvider, sortable={"name": TrainingProvider.name, "rating": TrainingProvider.rating})
    return Page.build([TrainingProviderOut.model_validate(i) for i in items], total, common.page, common.page_size)


@providers_router.post("", response_model=TrainingProviderOut, status_code=status.HTTP_201_CREATED)
def create_provider(payload: TrainingProviderCreate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    p = TrainingProvider(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return TrainingProviderOut.model_validate(p)


@providers_router.get("/{provider_id}", response_model=TrainingProviderOut)
def get_provider(provider_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.get(TrainingProvider, provider_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider not found")
    return TrainingProviderOut.model_validate(p)


@providers_router.patch("/{provider_id}", response_model=TrainingProviderOut)
def update_provider(provider_id: str, payload: TrainingProviderUpdate, db: Session = Depends(get_db), user: User = Depends(require_provider_staff)):
    p = db.get(TrainingProvider, provider_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, f, v)
    db.commit()
    db.refresh(p)
    return TrainingProviderOut.model_validate(p)


# ── Programs ───────────────────────────────────────────────
@programs_router.get("", response_model=Page[TrainingProgramOut])
def list_programs(
    common: CommonQuery = Depends(),
    sector: Optional[str] = None,
    skill_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    district: Optional[str] = None,
    nsqf_level: Optional[int] = None,
    status_: Optional[TrainingStatus] = Query(None, alias="status"),
    has_seats: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(TrainingProgram).outerjoin(Location, TrainingProgram.location_id == Location.id).outerjoin(Skill, TrainingProgram.skill_id == Skill.id)
    if sector:
        stmt = stmt.where(Skill.sector.ilike(f"%{sector}%"))
    if skill_id:
        stmt = stmt.where(TrainingProgram.skill_id == skill_id)
    if provider_id:
        stmt = stmt.where(TrainingProgram.provider_id == provider_id)
    if district:
        stmt = stmt.where(Location.district.ilike(f"%{district}%"))
    if nsqf_level:
        stmt = stmt.where(TrainingProgram.nsqf_level == nsqf_level)
    if status_:
        stmt = stmt.where(TrainingProgram.status == status_)
    if has_seats:
        stmt = stmt.where(TrainingProgram.total_seats > TrainingProgram.filled_seats)
    if common.q:
        stmt = stmt.where(TrainingProgram.title.ilike(f"%{common.q}%"))
    items, total = paginate(db, stmt, common, TrainingProgram, sortable={"title": TrainingProgram.title, "start_date": TrainingProgram.start_date})
    return Page.build([TrainingProgramOut.model_validate(i) for i in items], total, common.page, common.page_size)


@programs_router.post("", response_model=TrainingProgramOut, status_code=status.HTTP_201_CREATED)
def create_program(payload: TrainingProgramCreate, db: Session = Depends(get_db), user: User = Depends(require_provider_staff)):
    if not db.get(TrainingProvider, payload.provider_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown provider_id")
    if not db.get(Skill, payload.skill_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown skill_id")
    p = TrainingProgram(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return TrainingProgramOut.model_validate(p)


@programs_router.get("/{program_id}", response_model=TrainingProgramOut)
def get_program(program_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.get(TrainingProgram, program_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Program not found")
    return TrainingProgramOut.model_validate(p)


@programs_router.patch("/{program_id}", response_model=TrainingProgramOut)
def update_program(program_id: str, payload: TrainingProgramUpdate, db: Session = Depends(get_db), user: User = Depends(require_provider_staff)):
    p = db.get(TrainingProgram, program_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Program not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, f, v)
    db.commit()
    db.refresh(p)
    return TrainingProgramOut.model_validate(p)


@programs_router.delete("/{program_id}", response_model=Message)
def delete_program(program_id: str, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    p = db.get(TrainingProgram, program_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Program not found")
    db.delete(p)
    db.commit()
    return Message(detail="Program deleted")


router.include_router(providers_router)
router.include_router(programs_router)
