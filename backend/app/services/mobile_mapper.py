"""ORM -> Android-app DTO translation.

Everything the mobile contract needs that the database does not store verbatim is
derived here, in one place, so `app/api/routes/mobile.py` stays a thin routing
layer and the dashboard's snake_case schemas stay untouched.

Two things worth knowing:

* **Ids are the database UUIDs.** The contract's examples use slugs
  (`solar_pv_installer`), but the app only ever round-trips whatever ids we hand
  it — catalogue -> training -> opportunities -> application — so real ids keep
  the app and the admin dashboard pointing at the same rows.
* **Display strings are formatted server-side** (`₹12,000 – ₹22,000`,
  `15 Oct 2026`) because the app renders them as-is.
"""
from __future__ import annotations

import math
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional, Tuple

from app.models.application import Application
from app.models.beneficiary import Beneficiary
from app.models.enums import (
    ApplicationStatus,
    EducationLevel,
    EmploymentPreference,
    Gender,
    Language,
)
from app.models.location import Location
from app.models.opportunity import Opportunity
from app.models.skill import Skill
from app.models.training import TrainingProgram
from app.schemas.mobile import (
    MobileProfileOut,
    NsqfSkillOut,
    OpportunityOut,
    ProgressMilestoneOut,
    ProgressSummaryOut,
    SkillRecommendationOut,
    TrainingProgramOut,
)

# ─────────────────────────────────────────────────────────────
# Interview script — the app's answer keys, in ask order.
#
# `script_id` names the step in `services/interview_engine.QUESTION_SCRIPT` whose
# localised prompt we serve AND whose extractor parses the answer. Keeping both
# sides of the round trip in this one table is what stops the questions we ask
# from drifting away from the entities we can actually parse back out.
# ─────────────────────────────────────────────────────────────
MOBILE_INTERVIEW_FIELDS: List[Tuple[str, str]] = [
    ("name", "name"),
    ("age", "age_gender"),
    ("location", "location"),
    ("education", "education"),
    ("family_background", "family_work"),
    ("existing_skills", "skills"),
    ("interests", "interests"),
    ("work_preference", "employment_pref"),
]


# ─────────────────────────────────────────────────────────────
# Display formatting
# ─────────────────────────────────────────────────────────────
_ICON_RULES: List[Tuple[str, Iterable[str]]] = [
    # first match wins, so the specific tags come before the broad ones
    ("solar", ("solar",)),
    ("mobile", ("mobile repair", "mobile")),
    ("rac", ("refrigeration", "air conditioning", "rac", "hvac")),
    ("electrical", ("electrical", "electronics", "wiring", "cctv", "computer", "digital")),
    ("tailoring", ("tailoring", "apparel", "stitching", "garment", "handloom", "weaving", "textile")),
    ("agritech", ("agriculture", "dairy", "poultry", "irrigation", "livestock", "honey", "allied")),
    ("construction", ("masonry", "construction", "welding", "fabrication", "civil", "plumbing", "steel")),
    ("food", ("food processing", "food service", "hospitality", "pickle", "papad", "restaurant")),
]

_EDUCATION_LABELS: Dict[EducationLevel, str] = {
    EducationLevel.NONE: "No formal schooling",
    EducationLevel.PRIMARY: "5th Pass",
    EducationLevel.MIDDLE: "8th Pass",
    EducationLevel.SECONDARY: "10th Pass",
    EducationLevel.SENIOR_SECONDARY: "12th Pass",
    EducationLevel.ITI: "ITI",
    EducationLevel.DIPLOMA: "Diploma",
    EducationLevel.GRADUATE: "Graduate",
    EducationLevel.POSTGRADUATE: "Post Graduate",
}

_GENDER_LABELS: Dict[Gender, str] = {
    Gender.MALE: "Male",
    Gender.FEMALE: "Female",
    Gender.OTHER: "Other",
    Gender.UNDISCLOSED: "Not disclosed",
}

# The app's WorkPreference enum has three members; the DB's has four.
_WORK_PREFERENCE: Dict[EmploymentPreference, str] = {
    EmploymentPreference.SELF_EMPLOYMENT: "SELF_EMPLOYMENT",
    EmploymentPreference.WAGE_EMPLOYMENT: "LOCAL_EMPLOYMENT",
    EmploymentPreference.APPRENTICESHIP: "EITHER",
    EmploymentPreference.ANY: "EITHER",
}

_OPPORTUNITY_TYPES = {
    "wage_job": "EMPLOYMENT",
    "self_employment": "SELF_EMPLOYMENT",
    "apprenticeship": "APPRENTICESHIP",
    "scheme": "SELF_EMPLOYMENT",
}

_TRAINING_MODES = {"offline": "OFFLINE", "online": "ONLINE", "blended": "HYBRID", "hybrid": "HYBRID"}


def icon_for(skill: Skill) -> str:
    """One of the eight icons the app's IconMapper knows; `star` is its fallback."""
    haystack = " ".join([skill.name, skill.sector, *(skill.tags or [])]).lower()
    for icon, needles in _ICON_RULES:
        if any(n in haystack for n in needles):
            return icon
    return "star"


def demand_level(demand_index: float) -> str:
    if demand_index >= 70:
        return "High"
    if demand_index >= 55:
        return "Medium"
    return "Moderate"


def income_range(wage_monthly: Optional[int]) -> str:
    """A single average wage rendered as the band the app displays."""
    if not wage_monthly:
        return "Varies by employer"
    low = int(round(wage_monthly * 0.85 / 500.0)) * 500
    high = int(round(wage_monthly * 1.55 / 500.0)) * 500
    return f"₹{low:,} – ₹{high:,}"


def format_day(value: Optional[date]) -> str:
    if not value:
        return "To be announced"
    return f"{value.day:02d} {value.strftime('%b %Y')}"


def language_of(code: str) -> Language:
    try:
        return Language(code)
    except ValueError:
        return Language.HINDI


def distance_km(origin: Optional[Location], target: Optional[Location]) -> float:
    """Great-circle distance, 0.0 when either end has no coordinates."""
    if not origin or not target:
        return 0.0
    if None in (origin.latitude, origin.longitude, target.latitude, target.longitude):
        return 0.0
    radius = 6371.0
    lat1, lon1, lat2, lon2 = map(
        math.radians, (origin.latitude, origin.longitude, target.latitude, target.longitude)
    )
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return round(2 * radius * math.asin(math.sqrt(a)), 1)


def place_label(location: Optional[Location], fallback: str = "Location not recorded") -> str:
    if not location:
        return fallback
    return ", ".join(p for p in (location.block, location.district, location.state) if p) or fallback


# ─────────────────────────────────────────────────────────────
# Catalogue DTOs
# ─────────────────────────────────────────────────────────────
def skill_to_dto(skill: Skill) -> NsqfSkillOut:
    return NsqfSkillOut(
        id=skill.id,
        title=skill.name,
        category=skill.sector,
        nsqf_level=skill.nsqf_level,
        demand_level=demand_level(skill.demand_index),
        average_monthly_income=income_range(skill.avg_wage_monthly),
        icon=icon_for(skill),
        keywords=list(skill.tags or []),
    )


def recommendation_to_dto(skill: Skill, match_score: float, reasons: List[str]) -> SkillRecommendationOut:
    return SkillRecommendationOut(
        id=skill.id,
        title=skill.name,
        category=skill.sector,
        match_score=int(round(match_score)),
        reasons=reasons,
        nsqf_level=skill.nsqf_level,
        demand_level=demand_level(skill.demand_index),
        average_monthly_income=income_range(skill.avg_wage_monthly),
        icon=icon_for(skill),
    )


def program_to_dto(program: TrainingProgram, origin: Optional[Location]) -> TrainingProgramOut:
    eligibility = list(program.eligibility_notes or [])
    age_cap = program.eligibility_max_age or 45
    eligibility.insert(0, f"Age {program.eligibility_min_age}–{age_cap} years")
    min_edu = EducationLevel(program.eligibility_min_education)
    if min_edu is not EducationLevel.NONE:
        eligibility.insert(1, f"Minimum {_EDUCATION_LABELS[min_edu]}")

    if program.fee == 0:
        fee = "Fully subsidized (PM-AJAY / PM-DAKSH)"
        scheme = "PM-AJAY Adarsh Gram & Grants-in-Aid / PM-DAKSH"
    else:
        fee = f"₹{program.fee:,}"
        scheme = "Partially subsidized — self-funded component"
    if program.stipend_monthly:
        fee += f" · ₹{program.stipend_monthly:,}/month stipend"

    return TrainingProgramOut(
        id=program.id,
        skill_id=program.skill_id,
        name=program.title,
        provider=program.provider.name if program.provider else "Empanelled training provider",
        nsqf_level=program.nsqf_level,
        duration_weeks=program.duration_weeks,
        mode=_TRAINING_MODES.get(program.mode.lower(), "OFFLINE"),
        location=place_label(program.location, "Venue to be announced"),
        distance_km=distance_km(origin, program.location),
        eligibility=eligibility,
        fee=fee,
        scheme=scheme,
        certification_body=program.certification_body or "NCVET-recognised Sector Skill Council",
        start_date=format_day(program.start_date),
        seats_available=program.seats_available,
        rating=round(program.provider.rating, 1) if program.provider else 4.0,
    )


def opportunity_to_dto(
    opportunity: Opportunity, origin: Optional[Location], match_score: int
) -> OpportunityOut:
    loc = opportunity.location
    wage_min, wage_max = opportunity.wage_monthly_min, opportunity.wage_monthly_max
    if wage_min and wage_max:
        income = f"₹{wage_min:,} – ₹{wage_max:,}"
    elif wage_min or wage_max:
        income = f"₹{(wage_min or wage_max):,}"
    else:
        income = income_range(opportunity.skill.avg_wage_monthly if opportunity.skill else None)

    return OpportunityOut(
        id=opportunity.id,
        title=opportunity.title,
        type=_OPPORTUNITY_TYPES.get(opportunity.kind, "EMPLOYMENT"),
        organization=opportunity.employer or opportunity.source.title(),
        location=place_label(loc),
        lat=loc.latitude if loc and loc.latitude is not None else 0.0,
        lng=loc.longitude if loc and loc.longitude is not None else 0.0,
        distance_km=distance_km(origin, loc),
        description=opportunity.description or f"{opportunity.openings} opening(s) in {opportunity.sector}.",
        match_score=match_score,
        monthly_income_range=income,
    )


# ─────────────────────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────────────────────
def profile_to_dto(beneficiary: Beneficiary, summary: str) -> MobileProfileOut:
    loc = beneficiary.location
    return MobileProfileOut(
        name=beneficiary.full_name,
        age=beneficiary.age or 0,
        gender=_GENDER_LABELS.get(beneficiary.gender, "Not disclosed"),
        district=(loc.district if loc else None) or beneficiary.village or "Not recorded",
        state=(loc.state if loc else None) or "Jharkhand",
        education=_EDUCATION_LABELS.get(beneficiary.education_level, "Not recorded"),
        family_background=beneficiary.family_occupation or beneficiary.current_occupation or "Not recorded",
        existing_skills=[s.title() for s in (beneficiary.skills or [])],
        interest_areas=[i.title() for i in (beneficiary.interests or [])],
        work_preference=_WORK_PREFERENCE.get(beneficiary.employment_preference, "EITHER"),
        category=beneficiary.social_category or "SC",
        summary=summary,
    )


def summarise(beneficiary: Beneficiary) -> str:
    """Deterministic one-paragraph profile summary.

    Written from the extracted entities rather than asked of the LLM: this text is
    shown back to the beneficiary as "what we understood about you", so it has to
    be a faithful readback of the stored record, not a generated paraphrase.
    """
    loc = beneficiary.location
    where = ", ".join(p for p in (beneficiary.village, loc.district if loc else None) if p) or "your area"
    bits = [
        f"{beneficiary.full_name}, "
        f"{f'{beneficiary.age} years old, ' if beneficiary.age else ''}"
        f"from {where}."
    ]
    bits.append(f"Education: {_EDUCATION_LABELS.get(beneficiary.education_level, 'not recorded')}.")
    if beneficiary.skills:
        bits.append("Already skilled in " + ", ".join(beneficiary.skills) + ".")
    if beneficiary.interests:
        bits.append("Wants to build a livelihood in " + ", ".join(beneficiary.interests) + ".")
    preference = {
        "SELF_EMPLOYMENT": "Prefers starting their own work or enterprise.",
        "LOCAL_EMPLOYMENT": "Prefers a wage job close to home.",
        "EITHER": "Open to either a wage job or self-employment.",
    }[_WORK_PREFERENCE.get(beneficiary.employment_preference, "EITHER")]
    bits.append(preference)
    return " ".join(bits)


# ─────────────────────────────────────────────────────────────
# Progress timeline
# ─────────────────────────────────────────────────────────────
_STAGE_WEIGHTS = [
    ("Profile Created", 15),
    ("Skill Recommendation", 15),
    ("Training Application", 15),
    ("Training Enrollment", 15),
    ("Training Completion", 25),
    ("Certification & Placement", 15),
]

_ACTIVE_APPLICATION_STATES = {
    ApplicationStatus.ENROLLED,
    ApplicationStatus.IN_PROGRESS,
    ApplicationStatus.COMPLETED,
    ApplicationStatus.CERTIFIED,
}


def _milestone(
    index: int, title: str, when: Optional[datetime | date], status: str, detail: str
) -> ProgressMilestoneOut:
    stamp = when.date() if isinstance(when, datetime) else when
    return ProgressMilestoneOut(
        id=f"m{index}",
        title=title,
        date=format_day(stamp) if stamp else "—",
        status=status,
        detail=detail,
    )


def build_progress(beneficiary: Beneficiary) -> ProgressSummaryOut:
    """Derive the app's milestone timeline from the beneficiary's real record.

    Each of the six stages is either DONE (the underlying row exists), ON_TRACK
    (it's the next thing that will happen) or PENDING, and `overallPercent` is the
    weighted sum of the DONE stages — so the number and the timeline can never
    disagree.
    """
    recommendations = sorted(beneficiary.recommendations, key=lambda r: r.rank or 99)
    applications = sorted(beneficiary.applications, key=lambda a: a.created_at)
    active = next((a for a in applications if a.status in _ACTIVE_APPLICATION_STATES), None)
    certified = next((a for a in applications if a.status == ApplicationStatus.CERTIFIED), None)
    completed = next(
        (a for a in applications if a.status in (ApplicationStatus.COMPLETED, ApplicationStatus.CERTIFIED)),
        None,
    )
    top = recommendations[0] if recommendations else None

    done = [
        True,  # the record exists, so the profile stage is always complete
        bool(recommendations),
        bool(applications),
        bool(active),
        bool(completed),
        bool(certified),
    ]
    # the first not-yet-done stage is what the beneficiary is working towards
    next_index = next((i for i, ok in enumerate(done) if not ok), None)

    def state(index: int) -> str:
        if done[index]:
            return "DONE"
        return "ON_TRACK" if index == next_index else "PENDING"

    top_skill = top.skill.name if top and top.skill else "your recommended trade"
    program = active.program if active else (applications[0].program if applications else None)
    program_title = program.title if program else "a matching training programme"

    milestones = [
        _milestone(1, "Profile Created", beneficiary.created_at, state(0),
                   "Beneficiary profile generated from voice interview"),
        _milestone(2, "Skill Recommendation", top.created_at if top else None, state(1),
                   f"Best match: {top_skill}" if top else "Awaiting recommendation run"),
        _milestone(3, "Training Application", applications[0].submitted_at if applications else None, state(2),
                   f"Applied to {program_title}" if applications else "No application submitted yet"),
        _milestone(4, "Training Enrollment", active.enrolled_at if active else None, state(3),
                   f"Enrolled in {program_title}" if active else "Awaiting provider confirmation"),
        _milestone(5, "Training Completion", completed.completed_at if completed else None, state(4),
                   f"{active.progress_pct:.0f}% complete" if active else "Training not started"),
        _milestone(6, "Certification & Placement", certified.updated_at if certified else None, state(5),
                   f"Certificate {certified.certificate_number}" if certified
                   else "Certification after successful assessment"),
    ]

    percent = sum(weight for (_, weight), ok in zip(_STAGE_WEIGHTS, done) if ok)
    current_stage = _STAGE_WEIGHTS[next_index][0] if next_index is not None else "Certified & Placed"

    income = None
    if top and top.skill:
        suffix = "" if certified else " (projected)"
        income = f"{income_range(top.skill.avg_wage_monthly)}{suffix}"

    return ProgressSummaryOut(
        overall_percent=percent,
        current_stage=current_stage,
        monthly_income_after=income,
        milestones=milestones,
    )


def application_status_label(application: Application) -> str:
    """The app shows this verbatim; SUBMITTED reads as APPLIED to a beneficiary."""
    if application.status == ApplicationStatus.SUBMITTED:
        return "APPLIED"
    return application.status.value.upper()
