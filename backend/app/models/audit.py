from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class AuditLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)

    action: Mapped[str] = mapped_column(String(80), index=True, nullable=False)  # e.g. beneficiary.create
    entity_type: Mapped[Optional[str]] = mapped_column(String(60), index=True, nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)

    status: Mapped[str] = mapped_column(String(16), default="success", nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    changes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
