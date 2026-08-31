"""Explainable, configurable livelihood recommendation engine.

This is a transparent weighted-scoring model — NOT "ask an LLM what job is
best". Every point in the final score is attributable to a named factor, which
is what a government programme needs for audit and appeals.

score(beneficiary, skill) = 100 * Σ  w_f * f(beneficiary, skill)   /  Σ w_f
                                  f

Each factor f returns a value in [0, 1]. Hard eligibility failures zero the
score and are reported as blockers.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.beneficiary import Beneficiary
from app.models.enums import EducationLevel, EmploymentPreference, Mobility
from app.models.opportunity import Opportunity, SkillDemand
from app.models.skill import NsqfRole, Skill
from app.models.training import TrainingProgram

log = get_logger("reco")

ENGINE_VERSION = "1.0"

DEFAULT_WEIGHTS: Dict[str, float] = {
    "education_compatibility": 0.16,
    "existing_skills": 0.14,
    "interests": 0.18,
    "local_demand": 0.16,
    "mobility_fit": 0.08,
    "employment_preference": 0.10,
    "training_availability": 0.10,
    "local_opportunity": 0.06,
    "family_synergy": 0.02,
}

WEIGHT_DESCRIPTIONS: Dict[str, str] = {
    "education_compatibility": "How well the beneficiary's schooling meets the skill's NSQF entry level.",
    "existing_skills": "Overlap between skills the beneficiary already has and the skill's competencies/tags.",
    "interests": "Alignment of the skill with the sector/field the beneficiary said they want.",
    "local_demand": "District-level demand for this skill (from the livelihood map).",
    "mobility_fit": "Whether training/jobs for this skill are reachable given stated mobility.",
    "employment_preference": "Match between wage vs self-employment preference and the skill's nature.",
    "training_availability": "Availability of an eligible training seat near the beneficiary.",
    "local_opportunity": "Open jobs / self-employment openings for this skill nearby.",
    "family_synergy": "Whether the skill builds on the family's traditional occupation.",
}

_EDU_RANK = {
    EducationLevel.NONE: 0,
    EducationLevel.PRIMARY: 1,
    EducationLevel.MIDDLE: 2,
    EducationLevel.SECONDARY: 3,
    EducationLevel.SENIOR_SECONDARY: 4,
    EducationLevel.ITI: 4,
    EducationLevel.DIPLOMA: 5,
    EducationLevel.GRADUATE: 6,
    EducationLevel.POSTGRADUATE: 7,
}


def _edu_rank(value) -> int:
    try:
        return _EDU_RANK[EducationLevel(value)]
    except Exception:  # noqa: BLE001
        return 0


def load_weights(override: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)
    if settings.recommendation_weights_file:
        p = Path(settings.recommendation_weights_file)
        if p.exists():
            try:
                weights.update(json.loads(p.read_text()))
            except Exception as exc:  # noqa: BLE001
                log.warning("weights_file_invalid", error=str(exc))
    if override:
        weights.update({k: float(v) for k, v in override.items() if k in DEFAULT_WEIGHTS})
    return weights


class RecommendationEngine:
    def __init__(self, db: Session, weights: Optional[Dict[str, float]] = None):
        self.db = db
        self.weights = weights or load_weights()

    # ── factor implementations ─────────────────────────────
    def _f_education(self, b: Beneficiary, s: Skill) -> float:
        have = _edu_rank(b.education_level)
        need = _edu_rank(s.min_education)
        if have >= need:
            return 1.0
        gap = need - have
        return max(0.0, 1.0 - 0.34 * gap)

    def _f_existing_skills(self, b: Beneficiary, s: Skill) -> float:
        owned = {x.lower() for x in (b.skills or [])}
        if not owned:
            return 0.25  # neutral-low: nothing to build on but not disqualifying
        target = {s.name.lower(), s.sector.lower(), *[t.lower() for t in (s.tags or [])]}
        target |= {p.lower() for p in (s.prerequisites or [])}
        overlap = sum(1 for o in owned if any(o in t or t in o for t in target))
        return min(1.0, 0.3 + 0.35 * overlap)

    def _f_interests(self, b: Beneficiary, s: Skill) -> float:
        interests = {x.lower() for x in (b.interests or [])}
        if not interests:
            return 0.4
        hay = {s.name.lower(), s.sector.lower(), *[t.lower() for t in (s.tags or [])]}
        score = 0.0
        for it in interests:
            if any(it in h or h in it for h in hay):
                score = max(score, 1.0)
            elif any(w in " ".join(hay) for w in it.split()):
                score = max(score, 0.6)
        return score if score else 0.2

    def _f_local_demand(self, b: Beneficiary, s: Skill, demand_map: Dict[str, SkillDemand]) -> float:
        sd = demand_map.get(s.id)
        if sd:
            return max(0.0, min(1.0, sd.demand_score / 100.0))
        return max(0.0, min(1.0, s.demand_index / 100.0))

    def _f_mobility(self, b: Beneficiary, s: Skill, nearby_programs: int, any_programs: int) -> float:
        mob = b.mobility
        if nearby_programs > 0:
            return 1.0
        if any_programs == 0:
            return 0.3
        if mob in (Mobility.STATE, Mobility.ANYWHERE):
            return 0.9
        if mob == Mobility.DISTRICT:
            return 0.6
        return 0.35  # local-only + no local program

    def _f_employment_pref(self, b: Beneficiary, s: Skill) -> float:
        pref = b.employment_preference
        if pref == EmploymentPreference.SELF_EMPLOYMENT:
            return 1.0 if s.self_employable else 0.45
        if pref == EmploymentPreference.WAGE_EMPLOYMENT:
            return 0.7 if s.self_employable else 1.0
        return 0.85

    def _f_training_availability(self, programs: List[TrainingProgram], b: Beneficiary) -> float:
        if not programs:
            return 0.0
        eligible_open = [
            p
            for p in programs
            if p.seats_available > 0
            and _edu_rank(b.education_level) >= _edu_rank(p.eligibility_min_education)
            and (b.age is None or p.eligibility_min_age <= (b.age or 0) <= (p.eligibility_max_age or 99))
        ]
        if eligible_open:
            return 1.0
        return 0.4 if programs else 0.0

    def _f_local_opportunity(self, s: Skill, opps: List[Opportunity]) -> float:
        total = sum(o.openings for o in opps if o.skill_id == s.id and o.is_active)
        if total <= 0:
            return 0.2
        return min(1.0, 0.4 + 0.1 * total)

    def _f_family_synergy(self, b: Beneficiary, s: Skill) -> float:
        fam = (b.family_occupation or "").lower()
        if not fam:
            return 0.5
        hay = " ".join([s.name.lower(), s.sector.lower(), *[t.lower() for t in (s.tags or [])]])
        return 1.0 if any(w in hay for w in fam.split() if len(w) > 3) else 0.4

    # ── eligibility hard gate ──────────────────────────────
    def _eligibility_blockers(self, b: Beneficiary, s: Skill) -> List[str]:
        blockers = []
        if b.age is not None:
            if b.age < s.min_age:
                blockers.append(f"Below minimum age {s.min_age} for this skill")
            if s.max_age and b.age > s.max_age:
                blockers.append(f"Above maximum age {s.max_age} for this skill")
        if _edu_rank(b.education_level) + 2 < _edu_rank(s.min_education):
            blockers.append(
                f"Education gap too large (needs ~{s.min_education}, has {b.education_level.value})"
            )
        return blockers

    # ── public API ─────────────────────────────────────────
    def recommend(self, beneficiary: Beneficiary, top_n: int = 5) -> List[Dict]:
        skills = list(self.db.execute(select(Skill)).scalars())
        programs = list(self.db.execute(select(TrainingProgram)).scalars())
        opps = list(self.db.execute(select(Opportunity)).scalars())
        roles = list(self.db.execute(select(NsqfRole)).scalars())

        demand_rows = []
        if beneficiary.location_id:
            demand_rows = list(
                self.db.execute(
                    select(SkillDemand).where(SkillDemand.location_id == beneficiary.location_id)
                ).scalars()
            )
        demand_map = {d.skill_id: d for d in demand_rows}

        programs_by_skill: Dict[str, List[TrainingProgram]] = {}
        for p in programs:
            programs_by_skill.setdefault(p.skill_id, []).append(p)

        roles_by_sector: Dict[str, List[NsqfRole]] = {}
        for r in roles:
            roles_by_sector.setdefault(r.sector, []).append(r)

        results: List[Dict] = []
        for s in skills:
            s_programs = programs_by_skill.get(s.id, [])
            nearby = [p for p in s_programs if p.location_id == beneficiary.location_id]
            blockers = self._eligibility_blockers(beneficiary, s)

            factors = {
                "education_compatibility": self._f_education(beneficiary, s),
                "existing_skills": self._f_existing_skills(beneficiary, s),
                "interests": self._f_interests(beneficiary, s),
                "local_demand": self._f_local_demand(beneficiary, s, demand_map),
                "mobility_fit": self._f_mobility(beneficiary, s, len(nearby), len(s_programs)),
                "employment_preference": self._f_employment_pref(beneficiary, s),
                "training_availability": self._f_training_availability(s_programs, beneficiary),
                "local_opportunity": self._f_local_opportunity(s, opps),
                "family_synergy": self._f_family_synergy(beneficiary, s),
            }

            wsum = sum(self.weights.values()) or 1.0
            raw = sum(self.weights[k] * v for k, v in factors.items()) / wsum
            score = 0.0 if blockers else round(raw * 100, 1)

            role = self._pick_role(s, roles_by_sector)
            program = self._pick_program(s_programs, beneficiary)

            results.append(
                {
                    "skill": s,
                    "nsqf_role": role,
                    "suggested_program": program,
                    "match_score": score,
                    "factor_scores": {k: round(v * 100, 1) for k, v in factors.items()},
                    "reasons": self._reasons(beneficiary, s, factors, demand_map, nearby, blockers),
                    "skill_gaps": self._skill_gaps(beneficiary, s),
                    "career_pathway": self._pathway(s, role, program),
                    "blockers": blockers,
                }
            )

        results.sort(key=lambda r: r["match_score"], reverse=True)
        for i, r in enumerate(results, start=1):
            r["rank"] = i
        return results[:top_n]

    # ── helpers ────────────────────────────────────────────
    @staticmethod
    def _pick_role(skill: Skill, roles_by_sector: Dict[str, List[NsqfRole]]) -> Optional[NsqfRole]:
        if skill.roles:
            return sorted(skill.roles, key=lambda r: abs(r.nsqf_level - skill.nsqf_level))[0]
        candidates = roles_by_sector.get(skill.sector, [])
        if candidates:
            return sorted(candidates, key=lambda r: abs(r.nsqf_level - skill.nsqf_level))[0]
        return None

    @staticmethod
    def _pick_program(programs: List[TrainingProgram], b: Beneficiary) -> Optional[TrainingProgram]:
        if not programs:
            return None

        def key(p: TrainingProgram):
            local = 0 if p.location_id == b.location_id else 1
            has_seat = 0 if p.seats_available > 0 else 1
            return (has_seat, local, -p.stipend_monthly, p.fee)

        return sorted(programs, key=key)[0]

    def _reasons(self, b, s, factors, demand_map, nearby, blockers) -> List[str]:
        if blockers:
            return [f"Not eligible: {'; '.join(blockers)}"]
        r: List[str] = []
        if factors["interests"] >= 0.8:
            r.append(f"Directly matches the beneficiary's stated interest in {s.sector.lower()}")
        if factors["education_compatibility"] >= 0.99:
            r.append(f"Education ({b.education_level.value}) meets the NSQF Level {s.nsqf_level} entry requirement")
        elif factors["education_compatibility"] >= 0.6:
            r.append("Education is slightly below the ideal entry level but bridgeable with foundation modules")
        if factors["existing_skills"] >= 0.65:
            r.append(f"Builds on existing skills: {', '.join(b.skills or [])}")
        sd = demand_map.get(s.id)
        if sd and sd.demand_score >= 60:
            r.append(f"High local demand in the district (demand index {sd.demand_score:.0f}/100)")
        elif s.demand_index >= 60:
            r.append(f"Strong national demand for this skill (index {s.demand_index:.0f}/100)")
        if b.employment_preference == EmploymentPreference.SELF_EMPLOYMENT and s.self_employable:
            r.append("Supports the beneficiary's self-employment goal (micro-enterprise pathway available)")
        if nearby:
            r.append(f"{len(nearby)} training batch(es) available within the district")
        if s.avg_wage_monthly:
            r.append(f"Typical earning after certification ≈ ₹{s.avg_wage_monthly:,}/month")
        return r or ["Balanced overall fit across education, demand and training availability"]

    @staticmethod
    def _skill_gaps(b: Beneficiary, s: Skill) -> List[str]:
        owned = {x.lower() for x in (b.skills or [])}
        gaps = [p for p in (s.prerequisites or []) if p.lower() not in owned]
        if _edu_rank(b.education_level) < _edu_rank(s.min_education):
            gaps.append(f"Foundational literacy/numeracy bridge to reach {s.min_education} equivalence")
        if "computer" not in owned and "digital" in " ".join(s.tags or []).lower():
            gaps.append("Basic digital literacy")
        return gaps or ["No major skill gaps — ready for core training"]

    @staticmethod
    def _pathway(s: Skill, role: Optional[NsqfRole], program: Optional[TrainingProgram]) -> List[Dict]:
        steps = [
            {"step": 1, "title": "Enrol in training", "detail": program.title if program else f"{s.name} — NSQF L{s.nsqf_level}"},
            {"step": 2, "title": "Complete & certify", "detail": f"~{s.typical_duration_hours} hrs, assessment by {(program.certification_body if program else 'Sector Skill Council')}"},
            {
                "step": 3,
                "title": "Entry role",
                "detail": (role.title if role else f"{s.name} Technician") + (f" (₹{role.entry_wage_monthly:,}/mo)" if role and role.entry_wage_monthly else ""),
            },
        ]
        if s.self_employable:
            steps.append({"step": 4, "title": "Micro-enterprise", "detail": (role.self_employment_path if role and role.self_employment_path else f"Start an independent {s.name} service unit with PM-AJAY / PMEGP credit linkage")})
        else:
            steps.append({"step": 4, "title": "Growth", "detail": "Supervisor / senior technician after 2–3 years and NSQF up-skilling"})
        return steps


def build_recommendation_payloads(engine_results: List[Dict], beneficiary_id: str, interview_id: Optional[str], is_demo: bool, weights: Dict[str, float]) -> List[Dict]:
    """Shape engine output into ORM-ready dicts for Recommendation rows."""
    payloads = []
    for r in engine_results:
        payloads.append(
            {
                "beneficiary_id": beneficiary_id,
                "skill_id": r["skill"].id,
                "nsqf_role_id": r["nsqf_role"].id if r["nsqf_role"] else None,
                "suggested_program_id": r["suggested_program"].id if r["suggested_program"] else None,
                "interview_id": interview_id,
                "rank": r["rank"],
                "match_score": r["match_score"],
                "factor_scores": r["factor_scores"],
                "reasons": r["reasons"],
                "skill_gaps": r["skill_gaps"],
                "career_pathway": r["career_pathway"],
                "engine_version": ENGINE_VERSION,
                "is_demo": is_demo,
            }
        )
    return payloads


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
