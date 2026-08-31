from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff
from app.api.pagination import CommonQuery, paginate
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.notification import NotificationCreate, NotificationOut, UnreadCount
from app.services.notifications import notify_role, notify_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=Page[NotificationOut])
def list_notifications(
    common: CommonQuery = Depends(),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Notification).where(
        or_(Notification.user_id == user.id, Notification.audience_role == user.role.value)
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    items, total = paginate(db, stmt, common, Notification)
    return Page.build([NotificationOut.model_validate(i) for i in items], total, common.page, common.page_size)


@router.get("/unread-count", response_model=UnreadCount)
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(Notification).where(
            or_(Notification.user_id == user.id, Notification.audience_role == user.role.value),
            Notification.is_read.is_(False),
        )
    ).scalars().all()
    return UnreadCount(unread=len(rows))


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.get(Notification, notification_id)
    if not n or (n.user_id and n.user_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    n.is_read = True
    n.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(n)
    return NotificationOut.model_validate(n)


@router.post("/read-all", response_model=Message)
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(Notification).where(
            or_(Notification.user_id == user.id, Notification.audience_role == user.role.value),
            Notification.is_read.is_(False),
        )
    ).scalars().all()
    for n in rows:
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
    db.commit()
    return Message(detail=f"{len(rows)} notification(s) marked read")


@router.post("", response_model=Message, status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    if payload.user_id:
        notify_user(db, payload.user_id, payload.title, payload.body, type=payload.type, link=payload.link, meta=payload.meta)
        return Message(detail="Notification sent to user")
    if payload.audience_role:
        n = notify_role(db, payload.audience_role.value, payload.title, payload.body, type=payload.type, link=payload.link)
        return Message(detail=f"Broadcast to {n} user(s)")
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Provide user_id or audience_role")
