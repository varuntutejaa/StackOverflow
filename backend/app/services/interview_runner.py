"""Orchestrates one interview: turn handling, entity aggregation, completion."""
from __future__ import annotations

import base64
import json
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.beneficiary import Beneficiary
from app.models.enums import (
    BeneficiaryStatus,
    EducationLevel,
    EmploymentPreference,
    InterviewStatus,
    Language,
    MessageRole,
    Mobility,
)
from app.models.interview import Interview, InterviewMessage
from app.models.location import Location
from app.services import interview_engine as eng
from app.services.ai.registry import get_stt, get_translator, get_tts

log = get_logger("interview")


def _encode_text_as_audio(text: str) -> str:
    return base64.b64encode(json.dumps({"text": text}).encode()).decode()


def start_interview(db: Session, interview: Interview) -> InterviewMessage:
    """Create the opening assistant message."""
    q = eng.next_question(0, interview.language)
    phrased = eng.phrase_question(q["text"], interview.language, had_previous_answer=False)
    tts = get_tts().synthesize(phrased, interview.language)
    msg = InterviewMessage(
        interview_id=interview.id,
        sequence=0,
        role=MessageRole.ASSISTANT,
        language=interview.language,
        text_original=phrased,
        text_english=phrased if interview.language == Language.ENGLISH else get_translator().translate(phrased, interview.language, Language.ENGLISH),
        audio_url=tts.audio_url,
        intent="ask_" + q["id"],
    )
    interview.status = InterviewStatus.IN_PROGRESS
    interview.current_step = 0
    interview.total_steps = eng.TOTAL_STEPS
    interview.stt_provider = get_stt().name
    interview.llm_provider = "mock" if get_stt().name == "mock" else get_stt().name
    db.add(msg)
    db.flush()
    return msg


def handle_turn(
    db: Session,
    interview: Interview,
    *,
    text: Optional[str],
    audio_base64: Optional[str],
    language: Optional[Language],
    text_english: Optional[str] = None,
) -> Tuple[InterviewMessage, InterviewMessage, bool]:
    """Process a beneficiary turn. Returns (user_msg, assistant_msg, is_complete)."""
    lang = language or interview.language
    stt = get_stt()

    # 1. Resolve the user's utterance -> original + English
    if audio_base64:
        result = stt.transcribe(audio_base64, lang)
        text_original = result.text_original
        text_english = text_english or result.text_english
        confidence = result.confidence
    elif text is not None:
        text_original = text
        if not text_english:
            text_english = text if lang == Language.ENGLISH else get_translator().translate(text, lang, Language.ENGLISH)
        confidence = 1.0
    else:
        raise ValueError("Either text or audio_base64 is required")

    current_step = interview.current_step
    step_meta = eng.QUESTION_SCRIPT[min(current_step, eng.TOTAL_STEPS - 1)]

    # 2. Extract entities for this step
    entities = eng.extract_entities(step_meta["id"], text_english)
    aggregated: Dict = dict(interview.extracted_entities or {})
    for k, v in entities.items():
        if isinstance(v, list):
            aggregated[k] = sorted(set(aggregated.get(k, []) + v))
        elif v not in (None, "", []):
            aggregated[k] = v
    interview.extracted_entities = aggregated

    seq = len(interview.messages)
    user_msg = InterviewMessage(
        interview_id=interview.id,
        sequence=seq,
        role=MessageRole.USER,
        language=lang,
        text_original=text_original,
        text_english=text_english,
        stt_confidence=confidence,
        intent="answer_" + step_meta["id"],
        entities=entities,
    )
    db.add(user_msg)

    # 3. Advance
    next_step = current_step + 1
    interview.current_step = next_step
    interview.completion_pct = round(min(next_step / (eng.LAST_ANSWERABLE_INDEX + 1), 1.0) * 100, 1)

    is_complete = next_step > eng.LAST_ANSWERABLE_INDEX
    nq = eng.next_question(next_step, lang)

    if nq is None or is_complete:
        assistant_text = eng.QUESTION_SCRIPT[-1]["prompts"].get(lang, eng.QUESTION_SCRIPT[-1]["prompts"][Language.ENGLISH])
        is_complete = True
    else:
        assistant_text = eng.phrase_question(nq["text"], lang, had_previous_answer=True)

    tts = get_tts().synthesize(assistant_text, lang)
    assistant_msg = InterviewMessage(
        interview_id=interview.id,
        sequence=seq + 1,
        role=MessageRole.ASSISTANT,
        language=lang,
        text_original=assistant_text,
        text_english=assistant_text if lang == Language.ENGLISH else get_translator().translate(assistant_text, lang, Language.ENGLISH),
        audio_url=tts.audio_url,
        intent="ask_" + (nq["id"] if nq else "closing"),
    )
    db.add(assistant_msg)
    db.flush()

    # 4. Rebuild transcript
    interview.transcript = _render_transcript(interview)

    if is_complete:
        finalize_interview(db, interview)

    return user_msg, assistant_msg, is_complete


def _render_transcript(interview: Interview) -> str:
    lines = []
    for m in sorted(interview.messages, key=lambda x: x.sequence):
        who = "Kaushal AI" if m.role == MessageRole.ASSISTANT else "Beneficiary"
        lines.append(f"[{who}] {m.text_english or m.text_original}")
    return "\n".join(lines)


def finalize_interview(db: Session, interview: Interview) -> Dict:
    profile = eng.build_structured_profile(interview.extracted_entities or {})
    interview.structured_profile = profile
    interview.status = InterviewStatus.COMPLETED
    interview.completion_pct = 100.0

    beneficiary: Beneficiary = interview.beneficiary
    _apply_profile_to_beneficiary(db, beneficiary, profile)
    beneficiary.ai_profile = profile
    if beneficiary.status in (
        BeneficiaryStatus.REGISTERED,
        BeneficiaryStatus.INTERVIEW_PENDING,
        BeneficiaryStatus.INTERVIEW_DONE,
    ):
        beneficiary.status = BeneficiaryStatus.INTERVIEW_DONE
    db.flush()
    log.info("interview_finalized", interview_id=interview.id, confidence=profile.get("confidence"))
    return profile


def _apply_profile_to_beneficiary(db: Session, b: Beneficiary, profile: Dict) -> None:
    def _maybe(attr, value, caster=lambda x: x):
        if value not in (None, "", []):
            try:
                setattr(b, attr, caster(value))
            except Exception:  # noqa: BLE001
                pass

    if not b.full_name or b.full_name.lower().startswith(("beneficiary", "new ")):
        _maybe("full_name", profile.get("full_name"))
    if not b.age:
        _maybe("age", profile.get("age"), int)
    if not b.village:
        _maybe("village", profile.get("village"))
    if not b.current_occupation:
        _maybe("current_occupation", profile.get("current_occupation"))
    if not b.family_occupation:
        _maybe("family_occupation", profile.get("family_occupation"))
    _maybe("education_notes", profile.get("education_notes"))

    if profile.get("education_level"):
        # never downgrade a known education level from a noisy transcript
        from app.services.recommendation_engine import _edu_rank

        try:
            new_level = EducationLevel(profile["education_level"])
            if _edu_rank(new_level.value) >= _edu_rank(b.education_level.value) or b.education_level == EducationLevel.NONE:
                b.education_level = new_level
        except ValueError:
            pass
    if profile.get("mobility"):
        try:
            b.mobility = Mobility(profile["mobility"])
        except ValueError:
            pass
    if profile.get("employment_preference"):
        try:
            b.employment_preference = EmploymentPreference(profile["employment_preference"])
        except ValueError:
            pass

    if profile.get("skills"):
        b.skills = sorted(set((b.skills or []) + profile["skills"]))
    if profile.get("interests"):
        b.interests = sorted(set((b.interests or []) + profile["interests"]))
    if profile.get("constraints"):
        b.constraints = sorted(set((b.constraints or []) + profile["constraints"]))

    # best-effort district link
    district = profile.get("district")
    if district and not b.location_id:
        loc = db.query(Location).filter(Location.district.ilike(district)).first()
        if loc:
            b.location_id = loc.id
