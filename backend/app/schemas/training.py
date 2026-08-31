from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import TrainingStatus
from app.schemas.location import LocationOut
from app.schemas.skill import SkillOut


class TrainingProviderBase(BaseModel):
    name: str
    type: str = "pia"
    accreditation: Optional[str] = None
    rating: float = 4.0
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    location_id: Optional[str] = None
    address: Optional[str] = None


class TrainingProviderCreate(TrainingProviderBase):
    is_simulated: bool = True


class TrainingProviderUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    accreditation: Optional[str] = None
    rating: Optional[float] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    location_id: Optional[str] = None
    address: Optional[str] = None


class TrainingProviderOut(TrainingProviderBase):
    id: str
    is_simulated: bool
    location: Optional[LocationOut] = None
    model_config = {"from_attributes": True}


class TrainingProgramBase(BaseModel):
    title: str
    provider_id: str
    skill_id: str
    nsqf_level: int = 3
    mode: str = "offline"
    duration_hours: int = 300
    duration_weeks: int = 12
    total_seats: int = 30
    fee: int = 0
    stipend_monthly: int = 0
    is_residential: bool = False
    location_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    application_deadline: Optional[date] = None
    eligibility_min_education: str = "none"
    eligibility_min_age: int = 15
    eligibility_max_age: Optional[int] = 45
    eligibility_notes: List[str] = Field(default_factory=list)
    certification_body: Optional[str] = None


class TrainingProgramCreate(TrainingProgramBase):
    is_simulated: bool = True


class TrainingProgramUpdate(BaseModel):
    title: Optional[str] = None
    nsqf_level: Optional[int] = None
    mode: Optional[str] = None
    duration_hours: Optional[int] = None
    duration_weeks: Optional[int] = None
    total_seats: Optional[int] = None
    fee: Optional[int] = None
    stipend_monthly: Optional[int] = None
    is_residential: Optional[bool] = None
    location_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    application_deadline: Optional[date] = None
    eligibility_min_education: Optional[str] = None
    eligibility_min_age: Optional[int] = None
    eligibility_max_age: Optional[int] = None
    eligibility_notes: Optional[List[str]] = None
    status: Optional[TrainingStatus] = None
    certification_body: Optional[str] = None


class TrainingProgramOut(TrainingProgramBase):
    id: str
    filled_seats: int
    seats_available: int
    status: TrainingStatus
    is_simulated: bool
    skill: Optional[SkillOut] = None
    provider: Optional[TrainingProviderOut] = None
    location: Optional[LocationOut] = None
    model_config = {"from_attributes": True}
