"""The Android app's API surface (`DishaAI` / `com.example.kaushai`).

These routes live at the same `/api/v1` prefix as the dashboard's, because the
app's Retrofit interfaces hardcode bare paths (`nsqf/skills`, `training/{id}`,
…) against a configurable base URL. Four of the contract's paths collide with
existing dashboard routes — `POST /beneficiaries`, `POST /applications`,
`GET /opportunities` and `POST /auth/refresh` — and a path may only have one
handler per method, so those four handlers stay in their existing modules and
dispatch to the `mobile_*` functions exported from here based on the shape of
the request. Everything else is served directly below.

Contract: `BACKEND_API_CONTRACT.md` in the Android repo.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import SessionLocal, get_db
from app.models.beneficiary import Beneficiary
from app.models.enums import Language, TrainingStatus, UserRole
from app.models.opportunity import Opportunity
from app.models.skill import Skill
from app.models.training import TrainingProgram
from app.models.user import User
from app.schemas.mobile import (
    AssistantAskOut,
    AssistantAskRequest,
    BeneficiaryRegistrationOut,
    DeviceAuthRequest,
    InterviewFieldOut,
    InterviewQuestionsOut,
    InterviewSubmission,
    MobileApplicationOut,
    MobileApplicationRequest,
    MobileAuthResponse,
    NsqfSkillsOut,
    OpportunitiesOut,
    OtpChallengeOut,
    ProgressSummaryOut,
    RecommendationsOut,
    SignInRequest,
    SignUpResendRequest,
    SignUpStartRequest,
    SignUpVerifyRequest,
    TrainingProgramOut,
    TranslationOut,
    TranslationRequest,
)
from app.services import (
    assistant,
    interview_engine,
    mobile_intake,
    mobile_mapper,
    otp,
)
from app.services.ai.registry import get_translator

router = APIRouter(tags=["mobile-app"])


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def _session(db: Session, user: User, *, is_new: bool = False) -> MobileAuthResponse:
    """Everything the app needs to decide which screen to open next."""
    beneficiary = mobile_intake.beneficiary_for_user(db, user)
    return MobileAuthResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
        beneficiary_id=beneficiary.id if beneficiary else None,
        display_name=user.full_name,
        email=user.email if not user.email.endswith(mobile_intake.DEVICE_EMAIL_DOMAIN) else None,
        is_new_account=is_new,
        has_completed_interview=bool(beneficiary and beneficiary.interviews),
    )


def _owned_beneficiary(db: Session, user: User, beneficiary_id: str) -> Beneficiary:
    """Fetch a beneficiary, enforcing the same ownership rule as the admin API."""
    beneficiary = db.get(Beneficiary, beneficiary_id)
    if not beneficiary:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary not found")
    if user.role == UserRole.BENEFICIARY and user.id not in (
        beneficiary.user_account_id,
        beneficiary.created_by_id,
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")
    return beneficiary


# ─────────────────────────────────────────────────────────────
# Auth — `POST /auth/refresh` lives in routes/auth.py (shared path)
# ─────────────────────────────────────────────────────────────
@router.post("/auth/device", response_model=MobileAuthResponse)
def device_session(payload: DeviceAuthRequest, db: Session = Depends(get_db)):
    """Anonymous session bootstrap — used when someone continues without an account."""
    user = mobile_intake.get_or_create_device_user(db, payload.device_id, payload.language)
    return _session(db, user)


@router.post("/auth/signup/start", response_model=OtpChallengeOut)
def sign_up_start(payload: SignUpStartRequest):
    """Step 1 of registration: name, phone and password, then send an SMS code.

    Nothing is written to the database here — the details ride along with the OTP
    in the cache and only become an account once the number is proven, so an
    abandoned sign-up leaves nothing behind to collide with a later one.
    """
    if len(payload.full_name.strip()) < 2:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Please enter your name")
    if len(payload.password) < 6:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Password must be at least 6 characters")
    try:
        phone = otp.normalise_phone(payload.phone)
    except otp.OtpError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    challenge = otp.start_challenge(
        phone,
        payload={
            "full_name": payload.full_name.strip()[:160],
            "password_hash": hash_password(payload.password),
            "language": payload.language,
        },
    )
    return OtpChallengeOut(
        phone=challenge.phone,
        expires_in_seconds=challenge.expires_in_seconds,
        debug_code=challenge.debug_code,
    )


@router.post("/auth/signup/verify", response_model=MobileAuthResponse, status_code=status.HTTP_201_CREATED)
def sign_up_verify(payload: SignUpVerifyRequest, db: Session = Depends(get_db)):
    """Step 2: confirm the code, create the account, hand back a session."""
    try:
        phone, parked = otp.verify_challenge(payload.phone, payload.code)
    except otp.OtpError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    if not parked.get("password_hash"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Start the sign-up again from the beginning")

    existing = db.execute(select(User).where(User.phone == phone)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with this number already exists. Please sign in."
        )

    try:
        user, is_new = mobile_intake.find_or_create_account(
            db, phone=phone, full_name=parked.get("full_name"),
            password_hash=parked["password_hash"],
        )
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    return _session(db, user, is_new=is_new)


@router.post("/auth/signup/resend", response_model=OtpChallengeOut)
def sign_up_resend(payload: SignUpResendRequest):
    """Re-send the code, keeping the details parked against the original request."""
    try:
        phone = otp.normalise_phone(payload.phone)
    except otp.OtpError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    parked = otp.peek_payload(phone)
    if not parked:
        raise HTTPException(status.HTTP_410_GONE, "Start the sign-up again from the beginning")
    challenge = otp.start_challenge(phone, payload=parked)
    return OtpChallengeOut(
        phone=challenge.phone,
        expires_in_seconds=challenge.expires_in_seconds,
        debug_code=challenge.debug_code,
    )


@router.post("/auth/signin", response_model=MobileAuthResponse)
def sign_in(payload: SignInRequest, db: Session = Depends(get_db)):
    """Sign in with phone number + password."""
    try:
        phone = otp.normalise_phone(payload.phone)
    except otp.OtpError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    user = db.execute(select(User).where(User.phone == phone)).scalar_one_or_none()
    # Identical message either way, so this can't be used to discover which
    # numbers are registered.
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect phone number or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been disabled")
    return _session(db, user)


# ─────────────────────────────────────────────────────────────
# Interview
# ─────────────────────────────────────────────────────────────
@router.get("/interview/questions", response_model=InterviewQuestionsOut)
def interview_questions(language: str = Query("hi"), user: User = Depends(get_current_user)):
    """The localised question script, in ask order."""
    lang = mobile_mapper.language_of(language)
    fields: List[InterviewFieldOut] = []
    for app_key, script_id in mobile_mapper.MOBILE_INTERVIEW_FIELDS:
        step = next(s for s in interview_engine.QUESTION_SCRIPT if s["id"] == script_id)
        fields.append(
            InterviewFieldOut(
                key=app_key,
                question=step["prompts"].get(lang, step["prompts"][Language.ENGLISH]),
            )
        )
    return InterviewQuestionsOut(fields=fields)


# ── Shared with routes/beneficiaries.py (POST /beneficiaries) ──
def mobile_register_beneficiary(
    payload: InterviewSubmission, db: Session, user: User
) -> BeneficiaryRegistrationOut:
    """Interview submission doubles as registration; see the contract's Auth note."""
    beneficiary = mobile_intake.register_from_interview(
        db,
        user,
        answers=payload.answers,
        language=mobile_mapper.language_of(payload.language),
        is_demo=payload.is_demo,
    )
    mobile_intake.ensure_recommendations(db, beneficiary)
    return BeneficiaryRegistrationOut(
        beneficiary_id=beneficiary.id,
        profile=mobile_mapper.profile_to_dto(beneficiary, mobile_mapper.summarise(beneficiary)),
        # The caller is already authenticated, so the app keeps its current
        # session and only records the beneficiary id.
    )


# ─────────────────────────────────────────────────────────────
# Recommendations & catalogue
# ─────────────────────────────────────────────────────────────
@router.get("/beneficiaries/{beneficiary_id}/recommendations", response_model=RecommendationsOut)
def recommendations(
    beneficiary_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    beneficiary = _owned_beneficiary(db, user, beneficiary_id)
    rows = mobile_intake.ensure_recommendations(db, beneficiary)
    return RecommendationsOut(
        recommendations=[
            mobile_mapper.recommendation_to_dto(r.skill, r.match_score, list(r.reasons or []))
            for r in rows
            if r.skill
        ]
    )


@router.get("/nsqf/skills", response_model=NsqfSkillsOut)
def nsqf_catalogue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    skills = db.execute(select(Skill).order_by(Skill.demand_index.desc())).scalars().all()
    return NsqfSkillsOut(skills=[mobile_mapper.skill_to_dto(s) for s in skills])


@router.get("/training/{skill_id}", response_model=TrainingProgramOut)
def training_for_skill(
    skill_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """The single best programme for a skill: open batches first, then most seats."""
    programs = db.execute(
        select(TrainingProgram).where(TrainingProgram.skill_id == skill_id)
    ).scalars().unique().all()
    if not programs:
        # The app falls back to a generic placeholder rather than a blank screen.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No training programme for this skill")

    beneficiary = mobile_intake.beneficiary_for_user(db, user)
    origin = beneficiary.location if beneficiary else None
    best = min(
        programs,
        key=lambda p: (
            p.status not in (TrainingStatus.OPEN, TrainingStatus.UPCOMING),
            -p.seats_available,
            mobile_mapper.distance_km(origin, p.location) or 9_999,
        ),
    )
    return mobile_mapper.program_to_dto(best, origin)


# ── Shared with routes/opportunities.py (GET /opportunities) ──
def mobile_list_opportunities(skill_id: str, db: Session, user: User) -> OpportunitiesOut:
    rows = db.execute(
        select(Opportunity).where(
            Opportunity.skill_id == skill_id, Opportunity.is_active.is_(True)
        )
    ).scalars().unique().all()

    beneficiary = mobile_intake.beneficiary_for_user(db, user)
    origin = beneficiary.location if beneficiary else None
    # Reuse the engine's score for this skill when we have one, so the map and the
    # recommendation card never disagree about how good a fit this trade is.
    scored = next(
        (r.match_score for r in (beneficiary.recommendations if beneficiary else []) if r.skill_id == skill_id),
        None,
    )
    skill = db.get(Skill, skill_id)
    base = int(round(scored if scored is not None else (skill.demand_index if skill else 60)))

    return OpportunitiesOut(
        opportunities=[
            mobile_mapper.opportunity_to_dto(
                o, origin, min(99, base + (2 if o.kind == "self_employment" else 0))
            )
            for o in rows
        ]
    )


# ── Shared with routes/applications.py (POST /applications) ──
def mobile_submit_application(
    payload: MobileApplicationRequest, db: Session, user: User
) -> MobileApplicationOut:
    beneficiary = _owned_beneficiary(db, user, payload.beneficiary_id)
    program = db.get(TrainingProgram, payload.training_id)
    if not program:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Training programme not found")
    application = mobile_intake.submit_application(db, beneficiary, program)
    return MobileApplicationOut(
        application_id=application.id,
        status=mobile_mapper.application_status_label(application),
    )


# ─────────────────────────────────────────────────────────────
# Progress
# ─────────────────────────────────────────────────────────────
@router.get("/beneficiaries/{beneficiary_id}/progress", response_model=ProgressSummaryOut)
def progress(beneficiary_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return mobile_mapper.build_progress(_owned_beneficiary(db, user, beneficiary_id))


# ─────────────────────────────────────────────────────────────
# Assistant
# ─────────────────────────────────────────────────────────────
@router.post("/assistant/ask", response_model=AssistantAskOut)
def assistant_ask(
    payload: AssistantAskRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    beneficiary = (
        _owned_beneficiary(db, user, payload.beneficiary_id)
        if payload.beneficiary_id
        else mobile_intake.beneficiary_for_user(db, user)
    )
    return AssistantAskOut(
        answer=assistant.answer(db, beneficiary, payload.question, mobile_mapper.language_of(payload.language))
    )


@router.websocket("/ws/assistant")
async def assistant_ws(websocket: WebSocket):
    """Token-streamed assistant. Auth is the `Authorization` header on the upgrade.

    The app falls back to `POST /assistant/ask` if this socket errors or closes
    without a `done`, so every failure path here is a clean close.
    """
    await websocket.accept()
    header = websocket.headers.get("authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""

    db = SessionLocal()
    try:
        try:
            payload = decode_token(token, expected_type="access")
        except ValueError:
            await websocket.send_json({"type": "error", "message": "unauthorized"})
            await websocket.close(code=4401)
            return

        user = db.get(User, payload.get("sub"))
        if not user or not user.is_active:
            await websocket.send_json({"type": "error", "message": "unauthorized"})
            await websocket.close(code=4401)
            return

        while True:
            message = await websocket.receive_json()
            if message.get("type") != "question":
                continue
            question = (message.get("text") or "").strip()
            if not question:
                await websocket.send_json({"type": "error", "message": "empty question"})
                continue

            beneficiary = mobile_intake.beneficiary_for_user(db, user)
            language = mobile_mapper.language_of(message.get("language") or "hi")
            try:
                for chunk in assistant.stream(db, beneficiary, question, language):
                    await websocket.send_json({"type": "token", "text": chunk})
                await websocket.send_json({"type": "done"})
            except Exception as exc:  # noqa: BLE001
                await websocket.send_json({"type": "error", "message": str(exc)})
    except WebSocketDisconnect:
        pass
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# Translation
# ─────────────────────────────────────────────────────────────
@router.post("/translate", response_model=TranslationOut)
def translate(payload: TranslationRequest, user: User = Depends(get_current_user)):
    target = mobile_mapper.language_of(payload.target_language)
    source = Language.ENGLISH if target is not Language.ENGLISH else Language.HINDI
    return TranslationOut(translated_text=get_translator().translate(payload.text, source, target))
