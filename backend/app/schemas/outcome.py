from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.enums import OutcomeStage, OutcomeType


class OutcomeCreate(BaseModel):
    beneficiary_id: str
    application_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    stage: OutcomeStage
    outcome_type: Optional[OutcomeType] = None
    occurred_on: Optional[date] = None
    employer_or_venture: Optional[str] = None
    sector: Optional[str] = None
    district: Optional[str] = None
    income_before: Optional[int] = None
    income_after: Optional[int] = None
    is_verified: bool = False
    verification_source: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    is_demo: bool = False


class OutcomeUpdate(BaseModel):
    outcome_type: Optional[OutcomeType] = None
    occurred_on: Optional[date] = None
    employer_or_venture: Optional[str] = None
    sector: Optional[str] = None
    income_before: Optional[int] = None
    income_after: Optional[int] = None
    is_verified: Optional[bool] = None
    verification_source: Optional[str] = None
    notes: Optional[str] = None


class OutcomeOut(BaseModel):
    id: str
    beneficiary_id: str
    application_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    stage: OutcomeStage
    outcome_type: Optional[OutcomeType] = None
    occurred_on: Optional[date] = None
    employer_or_venture: Optional[str] = None
    sector: Optional[str] = None
    district: Optional[str] = None
    income_before: Optional[int] = None
    income_after: Optional[int] = None
    income_delta_pct: Optional[float] = None
    is_verified: bool
    verification_source: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    is_demo: bool
    created_at: datetime
    model_config = {"from_attributes": True}
