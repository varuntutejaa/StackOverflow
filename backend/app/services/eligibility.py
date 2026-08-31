from __future__ import annotations

from typing import Dict

from app.models.beneficiary import Beneficiary
from app.models.training import TrainingProgram
from app.services.recommendation_engine import _edu_rank


def check_eligibility(b: Beneficiary, program: TrainingProgram) -> Dict:
    checks = []

    edu_ok = _edu_rank(b.education_level) >= _edu_rank(program.eligibility_min_education)
    checks.append({
        "criterion": "education",
        "required": program.eligibility_min_education,
        "actual": b.education_level.value,
        "passed": edu_ok,
    })

    age_ok = True
    if b.age is not None:
        age_ok = program.eligibility_min_age <= b.age <= (program.eligibility_max_age or 200)
    checks.append({
        "criterion": "age",
        "required": f"{program.eligibility_min_age}-{program.eligibility_max_age or '∞'}",
        "actual": b.age,
        "passed": age_ok,
    })

    seats_ok = program.seats_available > 0
    checks.append({
        "criterion": "seats",
        "required": ">0",
        "actual": program.seats_available,
        "passed": seats_ok,
    })

    passed = all(c["passed"] for c in checks)
    return {"passed": passed, "checks": checks}
