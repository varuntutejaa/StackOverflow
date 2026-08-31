from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    name: str
    code: Optional[str] = None
    sector: str
    description: Optional[str] = None
    nsqf_level: int = Field(3, ge=1, le=10)
    min_education: str = "none"
    min_age: int = 15
    max_age: Optional[int] = None
    typical_duration_hours: int = 200
    avg_wage_monthly: Optional[int] = None
    self_employable: bool = False
    tags: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    demand_index: float = 50.0


class SkillCreate(SkillBase):
    is_simulated: bool = True


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    nsqf_level: Optional[int] = None
    min_education: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    typical_duration_hours: Optional[int] = None
    avg_wage_monthly: Optional[int] = None
    self_employable: Optional[bool] = None
    tags: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    demand_index: Optional[float] = None


class SkillOut(SkillBase):
    id: str
    is_simulated: bool
    model_config = {"from_attributes": True}


class NsqfRoleBase(BaseModel):
    title: str
    nco_code: Optional[str] = None
    qp_code: Optional[str] = None
    sector: str
    nsqf_level: int = Field(3, ge=1, le=10)
    description: Optional[str] = None
    eligibility: Optional[str] = None
    entry_wage_monthly: Optional[int] = None
    growth_outlook: str = "stable"
    self_employment_path: Optional[str] = None


class NsqfRoleCreate(NsqfRoleBase):
    skill_ids: List[str] = Field(default_factory=list)
    is_simulated: bool = True


class NsqfRoleUpdate(BaseModel):
    description: Optional[str] = None
    eligibility: Optional[str] = None
    entry_wage_monthly: Optional[int] = None
    growth_outlook: Optional[str] = None
    self_employment_path: Optional[str] = None
    skill_ids: Optional[List[str]] = None


class NsqfRoleOut(NsqfRoleBase):
    id: str
    is_simulated: bool
    skills: List[SkillOut] = Field(default_factory=list)
    model_config = {"from_attributes": True}
