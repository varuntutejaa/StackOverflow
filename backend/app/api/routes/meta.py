from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import engine, get_db
from app.models.beneficiary import Beneficiary
from app.models.enums import Language, UserRole
from app.services.ai.registry import provider_status
from app.services.cache import cache

router = APIRouter(tags=["meta"])


@router.get("/health")
def health():
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "service": settings.project_name,
        "env": settings.env,
        "database": "ok" if db_ok else "error",
        "database_engine": "sqlite" if settings.using_sqlite else "postgres",
        "cache_backend": cache.backend,
        "ai": provider_status(),
    }


@router.get("/meta/config")
def public_config():
    """Non-sensitive config the frontend needs at boot."""
    return {
        "project_name": settings.project_name,
        "env": settings.env,
        "api_prefix": settings.api_prefix,
        "languages": [
            {"code": Language.HINDI.value, "label": "हिन्दी (Hindi)"},
            {"code": Language.ENGLISH.value, "label": "English"},
            {"code": Language.SANTHALI.value, "label": "ᱥᱟᱱᱛᱟᱲᱤ (Santhali)"},
            {"code": Language.HO.value, "label": "𑄦𑄮 (Ho)"},
            {"code": Language.MUNDARI.value, "label": "मुंडारी (Mundari)"},
        ],
        "roles": [r.value for r in UserRole],
        "ai": provider_status(),
        "supabase_configured": bool(settings.supabase_url and settings.supabase_anon_key),
    }


@router.get("/meta/demo")
def demo_pointer(db: Session = Depends(get_db)):
    b = db.execute(
        select(Beneficiary).where(Beneficiary.pmajay_id == "PMAJAY-JH-RAN-000042")
    ).scalars().first()
    if not b:
        b = db.execute(
            select(Beneficiary).where(Beneficiary.full_name == "Ramesh Kumar", Beneficiary.is_demo.is_(True))
        ).scalars().first()
    return {
        "has_demo": b is not None,
        "beneficiary_id": b.id if b else None,
        "name": b.full_name if b else None,
        "note": "DEMO/SIMULATED — Ramesh Kumar walkthrough. Use POST /api/v1/meta/demo/reset (admin) to rebuild.",
    }
