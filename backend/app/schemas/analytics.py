from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class KpiCard(BaseModel):
    key: str
    label: str
    value: float
    unit: str = "count"
    delta_pct: Optional[float] = None
    trend: List[float] = []


class DistrictStat(BaseModel):
    district: str
    state: str
    beneficiaries: int
    interviews_done: int
    recommendations: int
    in_training: int
    certified: int
    placed: int
    self_employed: int
    placement_rate: float


class SkillDemandStat(BaseModel):
    skill: str
    sector: str
    demand_score: float
    supply_score: float
    gap_score: float
    open_positions: int


class FunnelStage(BaseModel):
    stage: str
    count: int
    conversion_from_previous: float


class TimeseriesPoint(BaseModel):
    period: str
    value: float


class OverviewResponse(BaseModel):
    generated_at: str
    kpis: List[KpiCard]
    funnel: List[FunnelStage]
    district_stats: List[DistrictStat]
    skill_demand: List[SkillDemandStat]
    enrollment_trend: List[TimeseriesPoint]
    language_split: Dict[str, int]
    recommendation_success_rate: float
    notes: str


class OutcomeDashboard(BaseModel):
    completion_rate: float
    placement_rate: float
    self_employment_rate: float
    wage_employment_rate: float
    avg_income_before: float
    avg_income_after: float
    avg_income_improvement_pct: float
    district_performance: List[DistrictStat]
    demand_vs_supply: List[SkillDemandStat]
