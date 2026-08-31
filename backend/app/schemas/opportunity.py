from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.location import LocationOut
from app.schemas.skill import SkillOut


class OpportunityBase(BaseModel):
    title: str
    kind: str = "wage_job"
    sector: str
    location_id: Optional[str] = None
    skill_id: Optional[str] = None
    nsqf_role_id: Optional[str] = None
    employer: Optional[str] = None
    openings: int = 1
    wage_monthly_min: Optional[int] = None
    wage_monthly_max: Optional[int] = None
    source: str = "simulated"
    valid_till: Optional[date] = None
    description: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    is_simulated: bool = True


class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    openings: Optional[int] = None
    wage_monthly_min: Optional[int] = None
    wage_monthly_max: Optional[int] = None
    valid_till: Optional[date] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class OpportunityOut(OpportunityBase):
    id: str
    is_active: bool
    is_simulated: bool
    location: Optional[LocationOut] = None
    skill: Optional[SkillOut] = None
    model_config = {"from_attributes": True}


class SkillDemandOut(BaseModel):
    id: str
    location_id: str
    skill_id: str
    demand_score: float
    supply_score: float
    gap_score: float
    open_positions: int
    trained_workforce: int
    active_beneficiaries: int
    period: str
    is_simulated: bool
    location: Optional[LocationOut] = None
    skill: Optional[SkillOut] = None
    model_config = {"from_attributes": True}


class DistrictMapPoint(BaseModel):
    location_id: str
    state: str
    district: str
    latitude: Optional[float]
    longitude: Optional[float]
    beneficiaries: int
    interviews_done: int
    in_training: int
    certified: int
    placed: int
    training_centers: int
    open_opportunities: int
    top_demand_skills: List[str]
    top_gap_skills: List[str]
    avg_demand_score: float
    avg_supply_score: float
    avg_gap_score: float


class MapResponse(BaseModel):
    period: str
    points: List[DistrictMapPoint]
    totals: dict
