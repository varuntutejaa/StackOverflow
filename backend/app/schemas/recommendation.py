from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.skill import NsqfRoleOut, SkillOut
from app.schemas.training import TrainingProgramOut


class RecommendationOut(BaseModel):
    id: str
    beneficiary_id: str
    rank: int
    match_score: float
    factor_scores: Dict[str, float] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    career_pathway: List[Dict[str, Any]] = Field(default_factory=list)
    engine_version: str
    is_accepted: Optional[bool] = None
    is_demo: bool
    created_at: datetime
    skill: Optional[SkillOut] = None
    nsqf_role: Optional[NsqfRoleOut] = None
    suggested_program: Optional[TrainingProgramOut] = None
    model_config = {"from_attributes": True}


class GenerateRecommendationsRequest(BaseModel):
    beneficiary_id: str
    top_n: int = Field(5, ge=1, le=20)
    persist: bool = True
    weights_override: Optional[Dict[str, float]] = None


class RecommendationResult(BaseModel):
    beneficiary_id: str
    engine_version: str
    weights: Dict[str, float]
    generated_at: datetime
    recommendations: List[RecommendationOut]


class AcceptRecommendationRequest(BaseModel):
    accepted: bool


class WeightsOut(BaseModel):
    weights: Dict[str, float]
    description: Dict[str, str]
