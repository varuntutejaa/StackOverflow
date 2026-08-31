from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.enums import ApplicationStatus
from app.schemas.training import TrainingProgramOut


class ApplicationCreate(BaseModel):
    beneficiary_id: str
    program_id: str
    recommendation_id: Optional[str] = None
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    progress_pct: Optional[float] = Field(default=None, ge=0, le=100)
    attendance_pct: Optional[float] = Field(default=None, ge=0, le=100)
    assessment_score: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None


class CertificateIssue(BaseModel):
    assessment_score: float = Field(ge=0, le=100)
    certificate_number: Optional[str] = None


class ApplicationOut(BaseModel):
    id: str
    beneficiary_id: str
    program_id: str
    recommendation_id: Optional[str] = None
    status: ApplicationStatus
    eligibility_passed: bool
    eligibility_report: Dict[str, Any] = Field(default_factory=dict)
    submitted_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    enrolled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_pct: float
    attendance_pct: float
    assessment_score: Optional[float] = None
    certificate_number: Optional[str] = None
    certificate_url: Optional[str] = None
    notes: Optional[str] = None
    is_demo: bool
    created_at: datetime
    program: Optional[TrainingProgramOut] = None
    model_config = {"from_attributes": True}
