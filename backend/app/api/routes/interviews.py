from __future__ import annotations

import json
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff
from app.api.pagination import CommonQuery, paginate
from app.core.security import decode_token
from app.db.session import SessionLocal, get_db
from app.models.beneficiary import Beneficiary
from app.models.enums import InterviewStatus, Language, UserRole
from app.models.interview import Interview
from app.models.user import User
from app.schemas.common import Page
from app.schemas.interview import (
    InterviewCreate,
    InterviewMessageOut,
    InterviewOut,
    SynthesizeRequest,
    SynthesizeResponse,
    TranscribeRequest,
    TranscribeResponse,
    TurnRequest,
    TurnResponse,
)
from app.services import audit, interview_runner
from app.services.ai.registry import get_stt, get_tts

router = APIRouter(tags=["interviews"])
interviews_router = APIRouter(prefix="/interviews")
voice_router = APIRouter(prefix="/voice")


@interviews_router.get("", response_model=Page[InterviewOut])
def list_interviews(
    common: CommonQuery = Depends(),
    beneficiary_id: Optional[str] = None,
    status_: Optional[InterviewStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Interview)
    if beneficiary_id:
        stmt = stmt.where(Interview.beneficiary_id == beneficiary_id)
    if status_:
        stmt = stmt.where(Interview.status == status_)
    items, total = paginate(db, stmt, common, Interview)
    return Page.build([InterviewOut.model_validate(i) for i in items], total, common.page, common.page_size)


@interviews_router.post("", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
def create_interview(payload: InterviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    beneficiary = db.get(Beneficiary, payload.beneficiary_id)
    if not beneficiary:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary not found")
    if user.role == UserRole.BENEFICIARY and user.id not in (beneficiary.user_account_id, beneficiary.created_by_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only start an interview for your own record")
    interview = Interview(
        beneficiary_id=beneficiary.id,
        conducted_by_id=user.id,
        language=payload.language,
        channel=payload.channel,
        is_demo=payload.is_demo or beneficiary.is_demo,
    )
    db.add(interview)
    db.flush()
    interview_runner.start_interview(db, interview)
    db.commit()
    db.refresh(interview)
    audit.record(db, action="interview.create", actor=user, entity_type="interview", entity_id=interview.id)
    return InterviewOut.model_validate(interview)


@interviews_router.get("/{interview_id}", response_model=InterviewOut)
def get_interview(interview_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")
    return InterviewOut.model_validate(interview)


@interviews_router.post("/{interview_id}/turn", response_model=TurnResponse)
def submit_turn(interview_id: str, payload: TurnRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")
    if interview.status == InterviewStatus.COMPLETED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Interview already completed")
    try:
        _, assistant_msg, is_complete = interview_runner.handle_turn(
            db,
            interview,
            text=payload.text,
            audio_base64=payload.audio_base64,
            language=payload.language,
            text_english=payload.text_english,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    db.commit()
    db.refresh(interview)
    return TurnResponse(
        interview=InterviewOut.model_validate(interview),
        assistant_message=InterviewMessageOut.model_validate(assistant_msg),
        is_complete=is_complete,
        next_prompt_tts_url=assistant_msg.audio_url,
    )


@interviews_router.post("/{interview_id}/complete", response_model=InterviewOut)
def complete_interview(interview_id: str, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")
    interview_runner.finalize_interview(db, interview)
    db.commit()
    db.refresh(interview)
    audit.record(db, action="interview.complete", actor=user, entity_type="interview", entity_id=interview.id)
    return InterviewOut.model_validate(interview)


@interviews_router.get("/{interview_id}/transcript", response_model=dict)
def get_transcript(interview_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")
    return {
        "interview_id": interview.id,
        "language": interview.language.value,
        "transcript": interview.transcript,
        "extracted_entities": interview.extracted_entities,
        "structured_profile": interview.structured_profile,
        "status": interview.status.value,
    }


# ── Voice endpoints ────────────────────────────────────────
@voice_router.post("/transcribe", response_model=TranscribeResponse)
def transcribe(payload: TranscribeRequest, user: User = Depends(get_current_user)):
    result = get_stt().transcribe(payload.audio_base64, payload.language)
    return TranscribeResponse(
        text_original=result.text_original,
        text_english=result.text_english,
        language=result.language,
        confidence=result.confidence,
    )


@voice_router.post("/synthesize", response_model=SynthesizeResponse)
def synthesize(payload: SynthesizeRequest, user: User = Depends(get_current_user)):
    result = get_tts().synthesize(payload.text, payload.language)
    return SynthesizeResponse(audio_url=result.audio_url, audio_base64=result.audio_base64, provider=result.provider)


# ── Realtime websocket ─────────────────────────────────────
@interviews_router.websocket("/{interview_id}/ws")
async def interview_ws(websocket: WebSocket, interview_id: str, token: Optional[str] = Query(None)):
    await websocket.accept()
    # auth via ?token=
    try:
        if not token:
            raise ValueError("missing token")
        decode_token(token, expected_type="access")
    except ValueError:
        await websocket.send_json({"type": "error", "detail": "unauthorized"})
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        interview = db.get(Interview, interview_id)
        if not interview:
            await websocket.send_json({"type": "error", "detail": "interview not found"})
            await websocket.close(code=4404)
            return

        await websocket.send_json({"type": "state", "interview": json.loads(InterviewOut.model_validate(interview).model_dump_json())})

        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if data.get("type") != "turn":
                continue
            if interview.status == InterviewStatus.COMPLETED:
                await websocket.send_json({"type": "error", "detail": "interview completed"})
                continue

            lang = None
            if data.get("language"):
                try:
                    lang = Language(data["language"])
                except ValueError:
                    lang = None
            try:
                _, assistant_msg, is_complete = interview_runner.handle_turn(
                    db, interview, text=data.get("text"), audio_base64=data.get("audio_base64"),
                    language=lang, text_english=data.get("text_english"),
                )
                db.commit()
                db.refresh(interview)
            except ValueError as exc:
                await websocket.send_json({"type": "error", "detail": str(exc)})
                continue

            await websocket.send_json(
                {
                    "type": "assistant",
                    "message": json.loads(InterviewMessageOut.model_validate(assistant_msg).model_dump_json()),
                    "interview": json.loads(InterviewOut.model_validate(interview).model_dump_json()),
                    "is_complete": is_complete,
                }
            )
            if is_complete:
                await websocket.send_json({"type": "complete", "profile": interview.structured_profile})
    except WebSocketDisconnect:
        pass
    finally:
        db.close()


router.include_router(interviews_router)
router.include_router(voice_router)
