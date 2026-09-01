"""Beneficiary intake driven by the Android app.

The dashboard registers beneficiaries field-by-field through the admin API; the
app registers them in one shot from a finished voice interview. Both end up as
the *same* rows — a `Beneficiary`, a completed `Interview` carrying the
transcript, and persisted `Recommendation`s — so a walk-in captured on a phone
shows up in the government portal with its full provenance intact.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.beneficiary import Beneficiary
from app.models.enums import (
    ApplicationStatus,
    BeneficiaryStatus,
    EducationLevel,
    EmploymentPreference,
    Gender,
    InterviewStatus,
    Language,
    MessageRole,
    Mobility,
    OutcomeStage,
    UserRole,
)
from app.models.interview import Interview, InterviewMessage
from app.models.location import Location
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.training import TrainingProgram
from app.models.user import User
from app.services import interview_engine
from app.services.eligibility import check_eligibility
from app.services.mobile_mapper import MOBILE_INTERVIEW_FIELDS
from app.services.recommendation_engine import (
    RecommendationEngine,
    build_recommendation_payloads,
    load_weights,
)

DEVICE_EMAIL_DOMAIN = "device.kaushai.local"


# ─────────────────────────────────────────────────────────────
# Device sessions
# ─────────────────────────────────────────────────────────────
def get_or_create_device_user(db: Session, device_id: str, language: str) -> User:
    """One `beneficiary`-role user per install, so the normal auth deps just work.

    The app has no login screen: the device id *is* the identity. Giving it a real
    `User` row (with no password, so it can never be signed into from the web)
    means every existing `get_current_user` / RBAC guard applies to app traffic
    unchanged.
    """
    email = f"device+{device_id.lower()}@{DEVICE_EMAIL_DOMAIN}"
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user:
        return user
    user = User(
        email=email,
        full_name="App user",
        role=UserRole.BENEFICIARY,
        hashed_password=None,
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def find_or_create_account(
    db: Session,
    *,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    full_name: Optional[str] = None,
    password_hash: Optional[str] = None,
    email_verified: bool = False,
) -> tuple[User, bool]:
    """Resolve a sign-in to one `beneficiary` user, creating it if new.

    Returns `(user, is_new)`. Matched on phone first — that is the identity the
    app registers with — then email, so a number that already has an account is
    never forked into a second one.
    """
    user: Optional[User] = None
    if phone:
        user = db.execute(select(User).where(User.phone == phone)).scalar_one_or_none()
    if not user and email:
        user = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()

    if user:
        if not user.is_active:
            raise PermissionError("Account is disabled")
        # Backfill whatever this sign-in just proved about them.
        if phone and not user.phone:
            user.phone = phone
        if email_verified:
            user.is_email_verified = True
        if full_name and user.full_name in ("App user", "", None):
            user.full_name = full_name
        db.commit()
        db.refresh(user)
        return user, False

    user = User(
        email=(email or f"phone+{(phone or '').lstrip('+')}@{DEVICE_EMAIL_DOMAIN}").lower(),
        phone=phone,
        full_name=full_name or "Beneficiary",
        role=UserRole.BENEFICIARY,
        hashed_password=password_hash,
        is_active=True,
        is_email_verified=email_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True


def has_completed_interview(db: Session, user: User) -> bool:
    """True once this account has a beneficiary profile built from an interview."""
    beneficiary = beneficiary_for_user(db, user)
    return bool(beneficiary and beneficiary.interviews)


def beneficiary_for_user(db: Session, user: User) -> Optional[Beneficiary]:
    return db.execute(
        select(Beneficiary)
        .where(or_(Beneficiary.user_account_id == user.id, Beneficiary.created_by_id == user.id))
        .order_by(Beneficiary.created_at)
    ).scalars().first()


# ─────────────────────────────────────────────────────────────
# Interview -> beneficiary
# ─────────────────────────────────────────────────────────────
def _resolve_location(db: Session, entities: Dict) -> Optional[Location]:
    """Best-effort match of the spoken place name onto a seeded district."""
    for key in ("district", "village"):
        name = (entities.get(key) or "").strip()
        if not name:
            continue
        hit = db.execute(
            select(Location).where(func.lower(Location.district) == name.lower())
        ).scalars().first()
        if hit:
            return hit
    return None


def _enum_or(value: Optional[str], enum_cls, default):
    try:
        return enum_cls(value)
    except (ValueError, TypeError):
        return default


def extract_profile(answers: Dict[str, str]) -> Dict:
    """Run each answer through the interview engine's extractor for its step."""
    entities: Dict = {}
    for app_key, script_id in MOBILE_INTERVIEW_FIELDS:
        answer = (answers.get(app_key) or "").strip()
        if answer:
            entities.update(interview_engine.extract_entities(script_id, answer))
    return entities


def register_from_interview(
    db: Session,
    user: User,
    *,
    answers: Dict[str, str],
    language: Language,
    is_demo: bool,
) -> Beneficiary:
    """Create (or refresh) this device's beneficiary record from its answers."""
    entities = extract_profile(answers)
    profile = interview_engine.build_structured_profile(entities)
    location = _resolve_location(db, entities)

    beneficiary = beneficiary_for_user(db, user)
    if beneficiary is None:
        beneficiary = Beneficiary(created_by_id=user.id, user_account_id=user.id)
        db.add(beneficiary)

    beneficiary.full_name = profile["full_name"] or (answers.get("name") or "Unnamed beneficiary").strip()[:160]
    beneficiary.age = profile["age"]
    beneficiary.gender = _enum_or(profile["gender"], Gender, Gender.UNDISCLOSED)
    beneficiary.preferred_language = language
    beneficiary.location_id = location.id if location else None
    beneficiary.village = profile["village"]
    beneficiary.education_level = _enum_or(profile["education_level"], EducationLevel, EducationLevel.NONE)
    beneficiary.education_notes = profile["education_notes"]
    beneficiary.current_occupation = profile["current_occupation"]
    beneficiary.family_occupation = profile["family_occupation"]
    beneficiary.skills = profile["skills"]
    beneficiary.interests = profile["interests"]
    beneficiary.constraints = profile["constraints"]
    beneficiary.mobility = _enum_or(profile["mobility"], Mobility, Mobility.LOCAL)
    beneficiary.employment_preference = _enum_or(
        profile["employment_preference"], EmploymentPreference, EmploymentPreference.ANY
    )
    beneficiary.has_smartphone = True  # they are literally using the app
    beneficiary.ai_profile = profile
    beneficiary.is_demo = is_demo
    beneficiary.status = BeneficiaryStatus.INTERVIEW_DONE
    db.flush()

    # keep the display name on the device account in step with the record
    if user.full_name in ("App user", "", None):
        user.full_name = beneficiary.full_name

    _record_interview(db, beneficiary, user, answers=answers, language=language, profile=profile)
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


def _record_interview(
    db: Session,
    beneficiary: Beneficiary,
    user: User,
    *,
    answers: Dict[str, str],
    language: Language,
    profile: Dict,
) -> Interview:
    """Persist the app's Q&A as a completed interview with a full transcript."""
    asked = [(key, script_id) for key, script_id in MOBILE_INTERVIEW_FIELDS if answers.get(key)]
    interview = Interview(
        beneficiary_id=beneficiary.id,
        conducted_by_id=user.id,
        language=language,
        channel="voice",
        status=InterviewStatus.COMPLETED,
        current_step=len(asked),
        total_steps=len(MOBILE_INTERVIEW_FIELDS),
        completion_pct=100.0,
        extracted_entities=profile,
        structured_profile=profile,
        is_demo=beneficiary.is_demo,
    )
    db.add(interview)
    db.flush()

    lines: List[str] = []
    for sequence, (key, script_id) in enumerate(asked):
        step = next(s for s in interview_engine.QUESTION_SCRIPT if s["id"] == script_id)
        question = step["prompts"].get(language, step["prompts"][Language.ENGLISH])
        answer = answers[key].strip()
        db.add(InterviewMessage(
            interview_id=interview.id, sequence=sequence * 2, role=MessageRole.ASSISTANT,
            language=language, text_original=question, text_english=step["prompts"][Language.ENGLISH],
        ))
        db.add(InterviewMessage(
            interview_id=interview.id, sequence=sequence * 2 + 1, role=MessageRole.USER,
            language=language, text_original=answer, text_english=answer,
        ))
        lines.append(f"Q: {step['prompts'][Language.ENGLISH]}\nA: {answer}")

    interview.transcript = "\n\n".join(lines)
    db.add(Outcome(
        beneficiary_id=beneficiary.id, stage=OutcomeStage.INTERVIEW,
        occurred_on=interview.created_at.date() if interview.created_at else None,
        is_demo=beneficiary.is_demo, details={"event": "interview_completed", "channel": "android_app"},
    ))
    return interview


# ─────────────────────────────────────────────────────────────
# Recommendations
# ─────────────────────────────────────────────────────────────
def ensure_recommendations(db: Session, beneficiary: Beneficiary, top_n: int = 5) -> List[Recommendation]:
    """Return this beneficiary's stored recommendations, generating them once.

    Persisting rather than computing on the fly is deliberate: the app and the
    dashboard then show the same ranked list with the same explanations, and an
    officer's accept/reject decision on a row survives the beneficiary reopening
    the screen.
    """
    stored = sorted(beneficiary.recommendations, key=lambda r: r.rank or 99)
    if stored:
        return stored[:top_n]

    weights = load_weights()
    results = RecommendationEngine(db, weights=weights).recommend(beneficiary, top_n=top_n)
    interview_id = beneficiary.interviews[-1].id if beneficiary.interviews else None
    rows = [
        Recommendation(**data)
        for data in build_recommendation_payloads(
            results, beneficiary.id, interview_id, beneficiary.is_demo, weights
        )
    ]
    for row in rows:
        db.add(row)
    if beneficiary.status in (
        BeneficiaryStatus.REGISTERED,
        BeneficiaryStatus.INTERVIEW_PENDING,
        BeneficiaryStatus.INTERVIEW_DONE,
    ):
        beneficiary.status = BeneficiaryStatus.RECOMMENDED
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


# ─────────────────────────────────────────────────────────────
# Enrollment
# ─────────────────────────────────────────────────────────────
def submit_application(db: Session, beneficiary: Beneficiary, program: TrainingProgram) -> Application:
    """Idempotent apply: re-submitting returns the existing application.

    The app deliberately does not retry this call, but a user can still tap
    Enroll twice. Returning the live application instead of a 409 keeps the app
    on its success path — a non-2xx would drop it into offline mock data.
    """
    existing = db.execute(
        select(Application).where(
            Application.beneficiary_id == beneficiary.id,
            Application.program_id == program.id,
            Application.status.notin_([ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN]),
        )
    ).scalars().first()
    if existing:
        return existing

    now = datetime.now(timezone.utc)
    report = check_eligibility(beneficiary, program)
    application = Application(
        beneficiary_id=beneficiary.id,
        program_id=program.id,
        recommendation_id=_recommendation_for_skill(beneficiary, program.skill_id),
        status=ApplicationStatus.SUBMITTED,
        eligibility_passed=report["passed"],
        eligibility_report=report,
        submitted_at=now,
        is_demo=beneficiary.is_demo,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    db.add(Outcome(
        beneficiary_id=beneficiary.id, application_id=application.id,
        stage=OutcomeStage.RECOMMENDATION, occurred_on=now.date(),
        is_demo=beneficiary.is_demo, details={"event": "applied", "program": program.title, "channel": "android_app"},
    ))
    db.commit()
    return application


def _recommendation_for_skill(beneficiary: Beneficiary, skill_id: str) -> Optional[str]:
    return next((r.id for r in beneficiary.recommendations if r.skill_id == skill_id), None)
