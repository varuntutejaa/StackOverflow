from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.api.pagination import CommonQuery, paginate
from app.core.security import hash_password
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.user import UserCreateAdmin, UserOut, UserUpdateAdmin
from app.services import audit

router = APIRouter(tags=["users-roles"])
users_router = APIRouter(prefix="/users")


@users_router.get("", response_model=Page[UserOut])
def list_users(
    common: CommonQuery = Depends(),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    if common.q:
        stmt = stmt.where(User.email.ilike(f"%{common.q}%") | User.full_name.ilike(f"%{common.q}%"))
    items, total = paginate(db, stmt, common, User, sortable={"email": User.email, "role": User.role})
    return Page.build([UserOut.model_validate(i) for i in items], total, common.page, common.page_size)


@users_router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateAdmin, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already in use")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        role=payload.role,
        phone=payload.phone,
        organisation=payload.organisation,
        district=payload.district,
        is_active=payload.is_active,
        is_email_verified=True,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    audit.record(db, action="user.create", actor=admin, entity_type="user", entity_id=user.id, changes={"role": user.role.value})
    return UserOut.model_validate(user)


@users_router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserOut.model_validate(u)


@users_router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdateAdmin, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if u.id == admin.id and payload.is_active is False:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate your own account")
    changes = payload.model_dump(exclude_unset=True)
    for f, v in changes.items():
        setattr(u, f, v)
    db.commit()
    db.refresh(u)
    audit.record(db, action="user.update", actor=admin, entity_type="user", entity_id=u.id, changes=changes)
    return UserOut.model_validate(u)


@users_router.delete("/{user_id}", response_model=Message)
def deactivate_user(user_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if u.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate your own account")
    u.is_active = False
    db.commit()
    audit.record(db, action="user.deactivate", actor=admin, entity_type="user", entity_id=u.id)
    return Message(detail="User deactivated")


@router.get("/roles", response_model=list[dict], tags=["users-roles"])
def list_roles(admin: User = Depends(require_admin)):
    return [
        {"key": UserRole.ADMIN.value, "label": "Administrator", "scope": "Full platform access, user & config management"},
        {"key": UserRole.GOV_OFFICER.value, "label": "Government Officer", "scope": "Beneficiaries, interviews, recommendations, analytics, outcomes"},
        {"key": UserRole.TRAINING_PROVIDER.value, "label": "Training Provider", "scope": "Own programs, applications, enrolment, certification"},
        {"key": UserRole.BENEFICIARY.value, "label": "Beneficiary", "scope": "Own profile, interview, recommendations, applications"},
    ]


@router.get("/audit-logs", response_model=Page[dict], tags=["users-roles"])
def list_audit_logs(
    common: CommonQuery = Depends(),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    items, total = paginate(db, stmt, common, AuditLog)
    rows = [
        {
            "id": a.id,
            "created_at": a.created_at.isoformat(),
            "actor_email": a.actor_email,
            "actor_role": a.actor_role,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "status": a.status,
            "ip_address": a.ip_address,
            "changes": a.changes,
        }
        for a in items
    ]
    return Page.build(rows, total, common.page, common.page_size)


router.include_router(users_router)
