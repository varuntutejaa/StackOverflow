from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.enums import NotificationType, UserRole


class NotificationCreate(BaseModel):
    user_id: Optional[str] = None
    audience_role: Optional[UserRole] = None
    type: NotificationType = NotificationType.INFO
    title: str
    body: Optional[str] = None
    link: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class NotificationOut(BaseModel):
    id: str
    type: NotificationType
    title: str
    body: Optional[str] = None
    link: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class UnreadCount(BaseModel):
    unread: int
