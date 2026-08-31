from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff
from app.api.pagination import CommonQuery, paginate
from app.db.session import get_db
from app.models.skill import NsqfRole, Skill
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.skill import (
    NsqfRoleCreate,
    NsqfRoleOut,
    NsqfRoleUpdate,
    SkillCreate,
    SkillOut,
    SkillUpdate,
)

router = APIRouter(tags=["nsqf-catalogue"])

skills_router = APIRouter(prefix="/skills")
roles_router = APIRouter(prefix="/nsqf-roles")


# ── Skills ─────────────────────────────────────────────────
@skills_router.get("", response_model=Page[SkillOut])
def list_skills(
    common: CommonQuery = Depends(),
    sector: Optional[str] = None,
    nsqf_level: Optional[int] = None,
    self_employable: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Skill)
    if sector:
        stmt = stmt.where(Skill.sector.ilike(f"%{sector}%"))
    if nsqf_level:
        stmt = stmt.where(Skill.nsqf_level == nsqf_level)
    if self_employable is not None:
        stmt = stmt.where(Skill.self_employable.is_(self_employable))
    if common.q:
        stmt = stmt.where(Skill.name.ilike(f"%{common.q}%"))
    items, total = paginate(db, stmt, common, Skill, sortable={"name": Skill.name, "demand_index": Skill.demand_index, "nsqf_level": Skill.nsqf_level})
    return Page.build([SkillOut.model_validate(i) for i in items], total, common.page, common.page_size)


@skills_router.get("/sectors", response_model=list[str])
def list_sectors(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [r[0] for r in db.execute(select(distinct(Skill.sector)).order_by(Skill.sector)).all()]


@skills_router.post("", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def create_skill(payload: SkillCreate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    if db.execute(select(Skill).where(Skill.name == payload.name)).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Skill name already exists")
    s = Skill(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return SkillOut.model_validate(s)


@skills_router.get("/{skill_id}", response_model=SkillOut)
def get_skill(skill_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.get(Skill, skill_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Skill not found")
    return SkillOut.model_validate(s)


@skills_router.patch("/{skill_id}", response_model=SkillOut)
def update_skill(skill_id: str, payload: SkillUpdate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    s = db.get(Skill, skill_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Skill not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, f, v)
    db.commit()
    db.refresh(s)
    return SkillOut.model_validate(s)


@skills_router.delete("/{skill_id}", response_model=Message)
def delete_skill(skill_id: str, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    s = db.get(Skill, skill_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Skill not found")
    db.delete(s)
    db.commit()
    return Message(detail="Skill deleted")


# ── NSQF job roles ─────────────────────────────────────────
@roles_router.get("", response_model=Page[NsqfRoleOut])
def list_roles(
    common: CommonQuery = Depends(),
    sector: Optional[str] = None,
    nsqf_level: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(NsqfRole)
    if sector:
        stmt = stmt.where(NsqfRole.sector.ilike(f"%{sector}%"))
    if nsqf_level:
        stmt = stmt.where(NsqfRole.nsqf_level == nsqf_level)
    if common.q:
        stmt = stmt.where(NsqfRole.title.ilike(f"%{common.q}%"))
    items, total = paginate(db, stmt, common, NsqfRole, sortable={"title": NsqfRole.title})
    return Page.build([NsqfRoleOut.model_validate(i) for i in items], total, common.page, common.page_size)


@roles_router.post("", response_model=NsqfRoleOut, status_code=status.HTTP_201_CREATED)
def create_role(payload: NsqfRoleCreate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    data = payload.model_dump(exclude={"skill_ids"})
    role = NsqfRole(**data)
    if payload.skill_ids:
        role.skills = list(db.execute(select(Skill).where(Skill.id.in_(payload.skill_ids))).scalars())
    db.add(role)
    db.commit()
    db.refresh(role)
    return NsqfRoleOut.model_validate(role)


@roles_router.get("/{role_id}", response_model=NsqfRoleOut)
def get_role(role_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    role = db.get(NsqfRole, role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    return NsqfRoleOut.model_validate(role)


@roles_router.patch("/{role_id}", response_model=NsqfRoleOut)
def update_role(role_id: str, payload: NsqfRoleUpdate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    role = db.get(NsqfRole, role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    data = payload.model_dump(exclude_unset=True, exclude={"skill_ids"})
    for f, v in data.items():
        setattr(role, f, v)
    if payload.skill_ids is not None:
        role.skills = list(db.execute(select(Skill).where(Skill.id.in_(payload.skill_ids))).scalars())
    db.commit()
    db.refresh(role)
    return NsqfRoleOut.model_validate(role)


router.include_router(skills_router)
router.include_router(roles_router)
