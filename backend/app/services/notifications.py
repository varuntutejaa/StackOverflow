from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.user import User


def notify_user(
    db: Session,
    user_id: str,
    title: str,
    body: Optional[str] = None,
    *,
    type: NotificationType = NotificationType.INFO,
    link: Optional[str] = None,
    meta: Optional[dict] = None,
    commit: bool = True,
) -> Notification:
    n = Notification(
        user_id=user_id, title=title, body=body, type=type, link=link, meta=meta or {}
    )
    db.add(n)
    if commit:
        db.commit()
        db.refresh(n)
    return n


def notify_role(
    db: Session,
    role: str,
    title: str,
    body: Optional[str] = None,
    *,
    type: NotificationType = NotificationType.INFO,
    link: Optional[str] = None,
    commit: bool = True,
) -> int:
    users = db.execute(select(User).where(User.role == role, User.is_active.is_(True))).scalars().all()
    for u in users:
        db.add(Notification(user_id=u.id, title=title, body=body, type=type, link=link, audience_role=role))
    if commit:
        db.commit()
    return len(users)
