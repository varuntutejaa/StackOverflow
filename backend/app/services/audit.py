from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.audit import AuditLog

log = get_logger("audit")


def record(
    db: Session,
    *,
    action: str,
    actor=None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status: str = "success",
    changes: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    commit: bool = True,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=getattr(actor, "id", None),
        actor_email=getattr(actor, "email", None),
        actor_role=getattr(getattr(actor, "role", None), "value", None),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        changes=changes or {},
        ip_address=ip_address,
        user_agent=(user_agent or "")[:300] or None,
    )
    db.add(entry)
    if commit:
        db.commit()
    log.info("audit", action=action, entity=entity_type, entity_id=entity_id, actor=entry.actor_email)
    return entry
