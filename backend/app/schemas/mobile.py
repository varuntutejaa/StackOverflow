"""camelCase request/response models for the KaushAI **Android app** surface.

The Android client (`DishaAI`, package `com.example.kaushai`) codes against a fixed
contract — see `BACKEND_API_CONTRACT.md` in that repo — which differs from the
snake_case admin API the Next.js dashboard uses:

* every key is camelCase (`nsqfLevel`, `matchScore`, …)
* enums are the app's UPPER_SNAKE names, not the DB's lowercase values
* responses are flat objects, never the admin API's `Page[...]` envelope

So these models are deliberately *not* shared with `app/schemas/*` — they are a
presentation layer for one client, and letting them drift from the ORM shape is
the point. `app/services/mobile_mapper.py` does the ORM -> DTO translation.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class MobileModel(BaseModel):
    """Serialises to camelCase, accepts either casing on the way in."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        ser_json_by_alias=True,
    )


# ── Auth ───────────────────────────────────────────────────
class DeviceAuthRequest(MobileModel):
    device_id: str
    language: str = "hi"
    app_version: str = "1.0"


class MobileAuthResponse(MobileModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int = 3600
    beneficiary_id: Optional[str] = None
    # Lets the app skip straight past the interview for a returning user, and
    # greet them by name without a second round trip.
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_new_account: bool = False
    has_completed_interview: bool = False


class SignUpStartRequest(MobileModel):
    """Step 1 of registration: the details, held only until the OTP is confirmed."""

    full_name: str
    phone: str
    password: str
    language: str = "en"


class OtpChallengeOut(MobileModel):
    phone: str
    expires_in_seconds: int
    # Present only outside production, where no SMS is actually sent.
    debug_code: Optional[str] = None


class SignUpVerifyRequest(MobileModel):
    """Step 2: the code from the SMS. Creates the account."""

    phone: str
    code: str


class SignUpResendRequest(MobileModel):
    phone: str


class SignInRequest(MobileModel):
    phone: str
    password: str


# ── Interview ──────────────────────────────────────────────
class InterviewFieldOut(MobileModel):
    key: str
    question: str


class InterviewQuestionsOut(MobileModel):
    fields: List[InterviewFieldOut]


# ── Beneficiary registration (interview submission) ────────
class InterviewSubmission(MobileModel):
    language: str = "hi"
    answers: Dict[str, str]
    is_demo: bool = False


class MobileProfileOut(MobileModel):
    name: str
    age: int
    gender: str
    district: str
    state: str
    education: str
    family_background: str
    existing_skills: List[str]
    interest_areas: List[str]
    work_preference: str  # SELF_EMPLOYMENT | LOCAL_EMPLOYMENT | EITHER
    category: str = "SC"
    summary: str


class BeneficiaryRegistrationOut(MobileModel):
    beneficiary_id: str
    profile: MobileProfileOut
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None


# ── Recommendations / NSQF catalogue ───────────────────────
class SkillRecommendationOut(MobileModel):
    id: str
    title: str
    category: str
    match_score: int
    reasons: List[str]
    nsqf_level: int
    demand_level: str
    average_monthly_income: str
    icon: str


class RecommendationsOut(MobileModel):
    recommendations: List[SkillRecommendationOut]


class NsqfSkillOut(MobileModel):
    id: str
    title: str
    category: str
    nsqf_level: int
    demand_level: str
    average_monthly_income: str
    icon: str
    keywords: List[str] = []


class NsqfSkillsOut(MobileModel):
    skills: List[NsqfSkillOut]


# ── Training ───────────────────────────────────────────────
class TrainingProgramOut(MobileModel):
    id: str
    skill_id: str
    name: str
    provider: str
    nsqf_level: int
    duration_weeks: int
    mode: str  # OFFLINE | ONLINE | HYBRID
    location: str
    distance_km: float
    eligibility: List[str]
    fee: str
    scheme: str
    certification_body: str
    start_date: str
    seats_available: int
    rating: float


# ── Opportunities ──────────────────────────────────────────
class OpportunityOut(MobileModel):
    id: str
    title: str
    type: str  # EMPLOYMENT | SELF_EMPLOYMENT | APPRENTICESHIP
    organization: str
    location: str
    lat: float
    lng: float
    distance_km: float
    description: str
    match_score: int
    monthly_income_range: str


class OpportunitiesOut(MobileModel):
    opportunities: List[OpportunityOut]


# ── Applications ───────────────────────────────────────────
class MobileApplicationRequest(MobileModel):
    beneficiary_id: str
    skill_id: str
    training_id: str


class MobileApplicationOut(MobileModel):
    application_id: str
    status: str


# ── Progress ───────────────────────────────────────────────
class ProgressMilestoneOut(MobileModel):
    id: str
    title: str
    date: str
    status: str  # DONE | ON_TRACK | PENDING
    detail: str


class ProgressSummaryOut(MobileModel):
    overall_percent: int
    current_stage: str
    monthly_income_after: Optional[str] = None
    milestones: List[ProgressMilestoneOut]


# ── Assistant / translation ────────────────────────────────
class AssistantAskRequest(MobileModel):
    beneficiary_id: Optional[str] = None
    question: str
    language: str = "hi"


class AssistantAskOut(MobileModel):
    answer: str


class TranslationRequest(MobileModel):
    text: str
    target_language: str


class TranslationOut(MobileModel):
    translated_text: str
