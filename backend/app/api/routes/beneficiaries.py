from __future__ import annotations

import csv
import io
from typing import Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_current_user, require_staff
from app.api.pagination import CommonQuery, paginate
from app.db.session import get_db
from app.models.beneficiary import Beneficiary
from app.models.enums import BeneficiaryStatus, EducationLevel, Language, UserRole
from app.models.location import Location
from app.models.user import User
from app.schemas.beneficiary import (
    BeneficiaryCreate,
    BeneficiaryListItem,
    BeneficiaryOut,
    BeneficiaryUpdate,
)
from app.schemas.common import Message, Page
from app.schemas.mobile import BeneficiaryRegistrationOut, InterviewSubmission
from app.services import audit

router = APIRouter(prefix="/beneficiaries", tags=["beneficiaries"])


def _visible(db: Session, user: User, stmt):
    """Beneficiaries can only see their own record."""
    if user.role == UserRole.BENEFICIARY:
        stmt = stmt.where(
            or_(Beneficiary.user_account_id == user.id, Beneficiary.created_by_id == user.id)
        )
    return stmt


def _district_of(b: Beneficiary) -> Optional[str]:
    return b.location.district if b.location else None


@router.get("", response_model=Page[BeneficiaryListItem])
def list_beneficiaries(
    common: CommonQuery = Depends(),
    district: Optional[str] = None,
    education_level: Optional[EducationLevel] = None,
    occupation: Optional[str] = None,
    skill: Optional[str] = None,
    status_: Optional[BeneficiaryStatus] = Query(None, alias="status"),
    language: Optional[Language] = None,
    is_demo: Optional[bool] = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Beneficiary).outerjoin(Location, Beneficiary.location_id == Location.id)
    stmt = _visible(db, user, stmt)

    if not include_archived:
        stmt = stmt.where(Beneficiary.is_archived.is_(False))
    if district:
        stmt = stmt.where(Location.district.ilike(f"%{district}%"))
    if education_level:
        stmt = stmt.where(Beneficiary.education_level == education_level)
    if occupation:
        stmt = stmt.where(Beneficiary.current_occupation.ilike(f"%{occupation}%"))
    if status_:
        stmt = stmt.where(Beneficiary.status == status_)
    if language:
        stmt = stmt.where(Beneficiary.preferred_language == language)
    if is_demo is not None:
        stmt = stmt.where(Beneficiary.is_demo.is_(is_demo))
    if skill:
        like = f'%"{skill.lower()}"%'
        stmt = stmt.where(func.lower(func.cast(Beneficiary.skills, str)).like(like))
    if common.q:
        term = f"%{common.q}%"
        stmt = stmt.where(
            or_(
                Beneficiary.full_name.ilike(term),
                Beneficiary.phone.ilike(term),
                Beneficiary.village.ilike(term),
                Beneficiary.pmajay_id.ilike(term),
            )
        )

    items, total = paginate(db, stmt, common, Beneficiary)
    rows = []
    for b in items:
        item = BeneficiaryListItem.model_validate(b)
        item.district = _district_of(b)
        rows.append(item)
    return Page.build(rows, total, common.page, common.page_size)


@router.get("/me", response_model=BeneficiaryOut)
def my_beneficiary_record(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = db.execute(
        select(Beneficiary).where(
            or_(Beneficiary.user_account_id == user.id, Beneficiary.created_by_id == user.id)
        ).order_by(Beneficiary.created_at)
    ).scalars().first()
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No beneficiary record linked to this account")
    return BeneficiaryOut.model_validate(b)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    # Two request shapes share this path, so the handler picks the model itself;
    # these are for the OpenAPI schema only.
    response_model=None,
    responses={201: {"model": Union[BeneficiaryOut, BeneficiaryRegistrationOut]}},
)
def create_beneficiary(
    request: Request,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Register a beneficiary — one path, two clients.

    The Android app posts a finished voice interview (`{language, answers,
    isDemo}`) and any authenticated device may do so for itself; the dashboard
    posts a filled-in `BeneficiaryCreate` form and that stays staff-only. The
    request body tells them apart: only the app's carries `answers`.
    """
    if "answers" in body:
        from app.api.routes.mobile import mobile_register_beneficiary

        return mobile_register_beneficiary(InterviewSubmission.model_validate(body), db, user)

    if user.role not in (UserRole.ADMIN, UserRole.GOV_OFFICER):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requires one of roles: admin, gov_officer")
    payload = BeneficiaryCreate.model_validate(body)
    if payload.location_id and not db.get(Location, payload.location_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown location_id")
    b = Beneficiary(**payload.model_dump(), created_by_id=user.id)
    if b.status in (None, BeneficiaryStatus.REGISTERED):
        b.status = BeneficiaryStatus.INTERVIEW_PENDING
    db.add(b)
    db.commit()
    db.refresh(b)
    audit.record(db, action="beneficiary.create", actor=user, entity_type="beneficiary", entity_id=b.id, ip_address=client_ip(request))
    return BeneficiaryOut.model_validate(b)


@router.get("/{beneficiary_id}", response_model=BeneficiaryOut)
def get_beneficiary(beneficiary_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = db.get(Beneficiary, beneficiary_id)
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary not found")
    if user.role == UserRole.BENEFICIARY and user.id not in (b.user_account_id, b.created_by_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")
    return BeneficiaryOut.model_validate(b)


@router.patch("/{beneficiary_id}", response_model=BeneficiaryOut)
def update_beneficiary(
    beneficiary_id: str,
    payload: BeneficiaryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
):
    b = db.get(Beneficiary, beneficiary_id)
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary not found")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(b, field, value)
    db.commit()
    db.refresh(b)
    audit.record(db, action="beneficiary.update", actor=user, entity_type="beneficiary", entity_id=b.id, changes=changes, ip_address=client_ip(request))
    return BeneficiaryOut.model_validate(b)


@router.post("/{beneficiary_id}/archive", response_model=Message)
def archive_beneficiary(beneficiary_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    b = db.get(Beneficiary, beneficiary_id)
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary not found")
    b.is_archived = True
    b.status = BeneficiaryStatus.ARCHIVED
    db.commit()
    audit.record(db, action="beneficiary.archive", actor=user, entity_type="beneficiary", entity_id=b.id, ip_address=client_ip(request))
    return Message(detail="Beneficiary archived")


@router.post("/{beneficiary_id}/restore", response_model=Message)
def restore_beneficiary(beneficiary_id: str, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    b = db.get(Beneficiary, beneficiary_id)
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary not found")
    b.is_archived = False
    b.status = BeneficiaryStatus.REGISTERED
    db.commit()
    return Message(detail="Beneficiary restored")


@router.delete("/{beneficiary_id}", response_model=Message)
def delete_beneficiary(beneficiary_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    b = db.get(Beneficiary, beneficiary_id)
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary not found")
    if b.is_demo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Demo records cannot be hard-deleted; archive instead")
    db.delete(b)
    db.commit()
    audit.record(db, action="beneficiary.delete", actor=user, entity_type="beneficiary", entity_id=beneficiary_id, ip_address=client_ip(request))
    return Message(detail="Beneficiary permanently deleted")


@router.get("/export/csv")
def export_csv(
    district: Optional[str] = None,
    status_: Optional[BeneficiaryStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
):
    stmt = select(Beneficiary).outerjoin(Location, Beneficiary.location_id == Location.id)
    if district:
        stmt = stmt.where(Location.district.ilike(f"%{district}%"))
    if status_:
        stmt = stmt.where(Beneficiary.status == status_)
    rows = db.execute(stmt).scalars().unique().all()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "name", "age", "gender", "district", "village", "education", "occupation", "status", "language", "skills", "interests", "is_demo"])
    for b in rows:
        w.writerow([
            b.id, b.full_name, b.age or "", b.gender.value, _district_of(b) or "", b.village or "",
            b.education_level.value, b.current_occupation or "", b.status.value,
            b.preferred_language.value, "|".join(b.skills or []), "|".join(b.interests or []), b.is_demo,
        ])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=beneficiaries.csv"},
    )
