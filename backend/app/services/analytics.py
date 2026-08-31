from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.beneficiary import Beneficiary
from app.models.enums import ApplicationStatus, BeneficiaryStatus, InterviewStatus, OutcomeStage, OutcomeType
from app.models.interview import Interview
from app.models.location import Location
from app.models.opportunity import Opportunity, SkillDemand
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.skill import Skill
from app.models.training import TrainingProgram


def _count(db: Session, model, *where) -> int:
    stmt = select(func.count()).select_from(model)
    for w in where:
        stmt = stmt.where(w)
    return db.execute(stmt).scalar_one()


def overview(db: Session) -> Dict:
    total_ben = _count(db, Beneficiary, Beneficiary.is_archived.is_(False))
    interviews_done = _count(db, Interview, Interview.status == InterviewStatus.COMPLETED)
    recos = _count(db, Recommendation)
    enrolled = _count(
        db,
        Application,
        Application.status.in_(
            [ApplicationStatus.ENROLLED, ApplicationStatus.IN_PROGRESS, ApplicationStatus.COMPLETED, ApplicationStatus.CERTIFIED]
        ),
    )
    certified = _count(db, Application, Application.status == ApplicationStatus.CERTIFIED)
    placed = _count(db, Beneficiary, Beneficiary.status == BeneficiaryStatus.PLACED)
    self_emp = _count(db, Beneficiary, Beneficiary.status == BeneficiaryStatus.SELF_EMPLOYED)

    accepted = _count(db, Recommendation, Recommendation.is_accepted.is_(True))
    decided = _count(db, Recommendation, Recommendation.is_accepted.isnot(None))
    reco_success = round((accepted / decided * 100) if decided else 0.0, 1)

    kpis = [
        {"key": "beneficiaries", "label": "Total Beneficiaries", "value": total_ben, "unit": "count"},
        {"key": "interviews", "label": "Interviews Completed", "value": interviews_done, "unit": "count"},
        {"key": "recommendations", "label": "Recommendations Generated", "value": recos, "unit": "count"},
        {"key": "enrolled", "label": "Training Enrolment", "value": enrolled, "unit": "count"},
        {"key": "certified", "label": "Certifications", "value": certified, "unit": "count"},
        {"key": "placed", "label": "Employed", "value": placed, "unit": "count"},
        {"key": "self_employed", "label": "Self-Employed", "value": self_emp, "unit": "count"},
        {"key": "reco_success", "label": "Recommendation Success Rate", "value": reco_success, "unit": "percent"},
    ]

    # Funnel
    registered = total_ben
    funnel_counts = [
        ("Registered", registered),
        ("Interviewed", interviews_done),
        ("Recommended", _count(db, Beneficiary, Beneficiary.status.in_([
            BeneficiaryStatus.RECOMMENDED, BeneficiaryStatus.IN_TRAINING, BeneficiaryStatus.CERTIFIED,
            BeneficiaryStatus.PLACED, BeneficiaryStatus.SELF_EMPLOYED]))),
        ("Enrolled", enrolled),
        ("Certified", certified),
        ("Employed / Self-employed", placed + self_emp),
    ]
    funnel = []
    for i, (stage, count) in enumerate(funnel_counts):
        prev = funnel_counts[i - 1][1] if i else count
        conv = round((count / prev * 100) if prev else 0.0, 1)
        funnel.append({"stage": stage, "count": count, "conversion_from_previous": conv})

    # District stats
    district_stats = _district_stats(db)

    # Skill demand
    skill_demand = _skill_demand_stats(db)

    # Enrollment trend (by month of application submitted_at)
    trend_map: Dict[str, int] = defaultdict(int)
    for a in db.execute(select(Application)).scalars():
        d = a.submitted_at or a.created_at
        if d:
            trend_map[d.strftime("%Y-%m")] += 1
    enrollment_trend = [{"period": k, "value": v} for k, v in sorted(trend_map.items())]

    # Language split
    lang_split: Dict[str, int] = defaultdict(int)
    for b in db.execute(select(Beneficiary.preferred_language)).scalars():
        lang_split[b.value] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kpis": kpis,
        "funnel": funnel,
        "district_stats": district_stats,
        "skill_demand": skill_demand,
        "enrollment_trend": enrollment_trend,
        "language_split": dict(lang_split),
        "recommendation_success_rate": reco_success,
        "notes": "Figures include DEMO/SIMULATED seed records. Filter is_demo=false for production-only data.",
    }


def _district_stats(db: Session) -> List[Dict]:
    rows: Dict[str, Dict] = {}
    locs = {l.id: l for l in db.execute(select(Location)).scalars()}
    for b in db.execute(select(Beneficiary).where(Beneficiary.is_archived.is_(False))).scalars():
        loc = locs.get(b.location_id)
        district = loc.district if loc else "Unassigned"
        state = loc.state if loc else "—"
        r = rows.setdefault(district, {
            "district": district, "state": state, "beneficiaries": 0, "interviews_done": 0,
            "recommendations": 0, "in_training": 0, "certified": 0, "placed": 0, "self_employed": 0,
        })
        r["beneficiaries"] += 1
        if b.status in (BeneficiaryStatus.INTERVIEW_DONE, BeneficiaryStatus.RECOMMENDED, BeneficiaryStatus.IN_TRAINING, BeneficiaryStatus.CERTIFIED, BeneficiaryStatus.PLACED, BeneficiaryStatus.SELF_EMPLOYED):
            r["interviews_done"] += 1
        if b.status in (BeneficiaryStatus.RECOMMENDED, BeneficiaryStatus.IN_TRAINING, BeneficiaryStatus.CERTIFIED, BeneficiaryStatus.PLACED, BeneficiaryStatus.SELF_EMPLOYED):
            r["recommendations"] += 1
        if b.status == BeneficiaryStatus.IN_TRAINING:
            r["in_training"] += 1
        if b.status == BeneficiaryStatus.CERTIFIED:
            r["certified"] += 1
        if b.status == BeneficiaryStatus.PLACED:
            r["placed"] += 1
        if b.status == BeneficiaryStatus.SELF_EMPLOYED:
            r["self_employed"] += 1

    out = []
    for r in rows.values():
        base = r["certified"] + r["placed"] + r["self_employed"]
        r["placement_rate"] = round(((r["placed"] + r["self_employed"]) / base * 100) if base else 0.0, 1)
        out.append(r)
    return sorted(out, key=lambda x: x["beneficiaries"], reverse=True)


def _skill_demand_stats(db: Session) -> List[Dict]:
    skills = {s.id: s for s in db.execute(select(Skill)).scalars()}
    agg: Dict[str, Dict] = {}
    for sd in db.execute(select(SkillDemand)).scalars():
        s = skills.get(sd.skill_id)
        if not s:
            continue
        a = agg.setdefault(s.id, {"skill": s.name, "sector": s.sector, "d": [], "sup": [], "open": 0})
        a["d"].append(sd.demand_score)
        a["sup"].append(sd.supply_score)
        a["open"] += sd.open_positions
    out = []
    for a in agg.values():
        d = round(sum(a["d"]) / len(a["d"]), 1) if a["d"] else 0.0
        sup = round(sum(a["sup"]) / len(a["sup"]), 1) if a["sup"] else 0.0
        out.append({
            "skill": a["skill"], "sector": a["sector"], "demand_score": d,
            "supply_score": sup, "gap_score": round(d - sup, 1), "open_positions": a["open"],
        })
    return sorted(out, key=lambda x: x["gap_score"], reverse=True)


def outcome_dashboard(db: Session) -> Dict:
    apps = list(db.execute(select(Application)).scalars())
    total_apps = len(apps) or 1
    completed = sum(1 for a in apps if a.status in (ApplicationStatus.COMPLETED, ApplicationStatus.CERTIFIED))
    certified = sum(1 for a in apps if a.status == ApplicationStatus.CERTIFIED)

    outcomes = list(db.execute(select(Outcome)).scalars())
    emp = [o for o in outcomes if o.outcome_type == OutcomeType.WAGE_EMPLOYMENT or o.stage == OutcomeStage.EMPLOYMENT]
    selfemp = [o for o in outcomes if o.outcome_type == OutcomeType.SELF_EMPLOYMENT or o.stage == OutcomeStage.SELF_EMPLOYMENT]
    placement_base = certified or 1

    incomes_before = [o.income_before for o in outcomes if o.income_before]
    incomes_after = [o.income_after for o in outcomes if o.income_after]
    avg_before = round(sum(incomes_before) / len(incomes_before), 0) if incomes_before else 0.0
    avg_after = round(sum(incomes_after) / len(incomes_after), 0) if incomes_after else 0.0
    improvement = round(((avg_after - avg_before) / avg_before * 100) if avg_before else 0.0, 1)

    return {
        "completion_rate": round(completed / total_apps * 100, 1),
        "placement_rate": round(len(emp) / placement_base * 100, 1),
        "self_employment_rate": round(len(selfemp) / placement_base * 100, 1),
        "wage_employment_rate": round(len(emp) / placement_base * 100, 1),
        "avg_income_before": avg_before,
        "avg_income_after": avg_after,
        "avg_income_improvement_pct": improvement,
        "district_performance": _district_stats(db),
        "demand_vs_supply": _skill_demand_stats(db),
    }


def livelihood_map(db: Session) -> Dict:
    locs = list(db.execute(select(Location)).scalars())
    beneficiaries = list(db.execute(select(Beneficiary)).scalars())
    programs = list(db.execute(select(TrainingProgram)).scalars())
    opps = list(db.execute(select(Opportunity).where(Opportunity.is_active.is_(True))).scalars())
    demand = list(db.execute(select(SkillDemand)).scalars())
    skills = {s.id: s for s in db.execute(select(Skill)).scalars()}

    by_loc_ben: Dict[str, List[Beneficiary]] = defaultdict(list)
    for b in beneficiaries:
        if b.location_id:
            by_loc_ben[b.location_id].append(b)
    by_loc_prog: Dict[str, int] = Counter(p.location_id for p in programs if p.location_id)
    by_loc_opp: Dict[str, int] = defaultdict(int)
    for o in opps:
        if o.location_id:
            by_loc_opp[o.location_id] += o.openings
    by_loc_demand: Dict[str, List] = defaultdict(list)
    for d in demand:
        by_loc_demand[d.location_id].append(d)

    points = []
    totals = Counter()
    for loc in locs:
        bens = by_loc_ben.get(loc.id, [])
        d_rows = sorted(by_loc_demand.get(loc.id, []), key=lambda x: x.demand_score, reverse=True)
        gap_rows = sorted(by_loc_demand.get(loc.id, []), key=lambda x: x.gap_score, reverse=True)
        certified = sum(1 for b in bens if b.status == BeneficiaryStatus.CERTIFIED)
        placed = sum(1 for b in bens if b.status in (BeneficiaryStatus.PLACED, BeneficiaryStatus.SELF_EMPLOYED))
        in_training = sum(1 for b in bens if b.status == BeneficiaryStatus.IN_TRAINING)
        interviews_done = sum(1 for b in bens if b.status not in (BeneficiaryStatus.REGISTERED, BeneficiaryStatus.INTERVIEW_PENDING))
        d_scores = [d.demand_score for d in d_rows] or [0]
        s_scores = [d.supply_score for d in d_rows] or [0]
        g_scores = [d.gap_score for d in d_rows] or [0]

        points.append({
            "location_id": loc.id,
            "state": loc.state,
            "district": loc.district,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "beneficiaries": len(bens),
            "interviews_done": interviews_done,
            "in_training": in_training,
            "certified": certified,
            "placed": placed,
            "training_centers": by_loc_prog.get(loc.id, 0),
            "open_opportunities": by_loc_opp.get(loc.id, 0),
            "top_demand_skills": [skills[d.skill_id].name for d in d_rows[:3] if d.skill_id in skills],
            "top_gap_skills": [skills[d.skill_id].name for d in gap_rows[:3] if d.skill_id in skills and d.gap_score > 0],
            "avg_demand_score": round(sum(d_scores) / len(d_scores), 1),
            "avg_supply_score": round(sum(s_scores) / len(s_scores), 1),
            "avg_gap_score": round(sum(g_scores) / len(g_scores), 1),
        })
        totals["beneficiaries"] += len(bens)
        totals["training_centers"] += by_loc_prog.get(loc.id, 0)
        totals["open_opportunities"] += by_loc_opp.get(loc.id, 0)
        totals["certified"] += certified
        totals["placed"] += placed

    period = demand[0].period if demand else "2026-Q1"
    return {"period": period, "points": points, "totals": dict(totals)}
