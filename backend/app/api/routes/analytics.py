from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import OutcomeDashboard, OverviewResponse
from app.schemas.opportunity import MapResponse
from app.services import analytics
from app.services.cache import cache

router = APIRouter(tags=["analytics"])


@router.get("/analytics/overview", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db), user: User = Depends(require_staff)):
    cached = cache.get_json("analytics:overview")
    if cached:
        return cached
    data = analytics.overview(db)
    cache.set_json("analytics:overview", data, ttl=60)
    return data


@router.get("/analytics/outcomes", response_model=OutcomeDashboard)
def get_outcomes(db: Session = Depends(get_db), user: User = Depends(require_staff)):
    return analytics.outcome_dashboard(db)


@router.get("/map/livelihood", response_model=MapResponse)
def get_map(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cached = cache.get_json("map:livelihood")
    if cached:
        return cached
    data = analytics.livelihood_map(db)
    cache.set_json("map:livelihood", data, ttl=120)
    return data
