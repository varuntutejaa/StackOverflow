"""Q&A assistant behind `POST /assistant/ask` and `WS /ws/assistant`.

When a real LLM is configured it answers with the beneficiary's own record in
context. The bundled mock provider only knows the interview-prompt protocol, so
this module also carries a deterministic, record-grounded answerer — the app
must work end-to-end with zero external credentials, and an assistant that
invents scheme details for a government service would be worse than one that
sticks to what the database actually says.
"""
from __future__ import annotations

import re
from typing import Iterator, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.beneficiary import Beneficiary
from app.models.enums import Language
from app.services.ai.base import ChatMessage
from app.services.ai.registry import get_llm
from app.services.mobile_mapper import build_progress, income_range

log = get_logger("assistant")

_FALLBACK = (
    "I can help with your recommended skills, the training programme you were matched to, "
    "eligibility, fees and stipends, and your progress. Ask me about any of those — for example, "
    "\"what training was I matched to?\" or \"what subsidy can I get?\""
)


def _context(beneficiary: Optional[Beneficiary]) -> str:
    if not beneficiary:
        return "No beneficiary profile is linked to this session yet."
    top = sorted(beneficiary.recommendations, key=lambda r: r.rank or 99)
    lines = [
        f"Name: {beneficiary.full_name}",
        f"Age: {beneficiary.age or 'unknown'}",
        f"Education: {beneficiary.education_level.value}",
        f"District: {beneficiary.location.district if beneficiary.location else 'unknown'}",
        f"Existing skills: {', '.join(beneficiary.skills or []) or 'none recorded'}",
        f"Interests: {', '.join(beneficiary.interests or []) or 'none recorded'}",
        f"Social category: {beneficiary.social_category}",
        f"Pipeline status: {beneficiary.status.value}",
    ]
    if top:
        best = top[0]
        lines.append(f"Top recommendation: {best.skill.name} at {best.match_score:.0f}% match")
        lines.append("Why: " + " ".join(best.reasons or []))
        if best.suggested_program:
            p = best.suggested_program
            lines.append(
                f"Suggested training: {p.title} by {p.provider.name if p.provider else 'a provider'}, "
                f"{p.duration_weeks} weeks, fee {'free under PM-AJAY/PM-DAKSH' if p.fee == 0 else f'₹{p.fee}'}"
            )
    return "\n".join(lines)


# ── Deterministic answerer ─────────────────────────────────
def _topic(question: str) -> str:
    q = question.lower()
    tests: List[Tuple[str, str]] = [
        ("subsidy", r"subsid|scheme|yojana|free|paisa|money|loan|grant|stipend|fee|cost|kitna"),
        ("training", r"training|course|class|batch|centre|center|institute|iti|where.*learn"),
        ("eligibility", r"eligib|qualify|can i apply|requirement|documents|papers|age limit"),
        ("income", r"income|salary|earn|kamai|wage|paisa milega|how much.*earn"),
        ("duration", r"how long|duration|weeks|months|time.*take"),
        ("progress", r"progress|status|stage|where am i|kahan"),
        ("recommendation", r"recommend|suggest|which skill|what should i|best.*for me|match"),
        ("enroll", r"enrol|enroll|apply|admission|join|register"),
    ]
    for topic, pattern in tests:
        if re.search(pattern, q):
            return topic
    return "general"


def _deterministic_answer(beneficiary: Optional[Beneficiary], question: str) -> str:
    topic = _topic(question)
    if not beneficiary:
        return (
            "Finish the voice interview first and I will be able to answer using your own profile. "
            + _FALLBACK
        )

    ranked = sorted(beneficiary.recommendations, key=lambda r: r.rank or 99)
    best = ranked[0] if ranked else None
    program = best.suggested_program if best else None
    name = beneficiary.full_name.split()[0]

    if topic == "subsidy":
        if program and program.fee == 0:
            answer = (
                f"{name}, the {program.title} programme is fully funded — there is no course fee for you. "
                f"As an SC-category candidate under PM-AJAY, training, assessment and certification are covered."
            )
            if program.stipend_monthly:
                answer += f" You also receive a stipend of ₹{program.stipend_monthly:,} per month during training."
            return answer
        return (
            f"{name}, SC-category candidates under PM-AJAY and PM-DAKSH get government-funded skilling — "
            "course fee, assessment and certification are covered, and most batches pay a monthly stipend. "
            "Complete your recommendation step and I can tell you the exact figures for your batch."
        )

    if topic == "training" and program:
        where = program.location.district if program.location else "your district"
        return (
            f"You were matched to {program.title}, run by "
            f"{program.provider.name if program.provider else 'an empanelled provider'} in {where}. "
            f"It runs for {program.duration_weeks} weeks ({program.duration_hours} hours) at NSQF level "
            f"{program.nsqf_level}, with {program.seats_available} seats currently open."
        )

    if topic == "eligibility" and program:
        return (
            f"For {program.title} you need to be between {program.eligibility_min_age} and "
            f"{program.eligibility_max_age or 45} years old with at least "
            f"{program.eligibility_min_education.replace('_', ' ')} education. "
            f"You are {beneficiary.age or 'of unrecorded age'} with "
            f"{beneficiary.education_level.value.replace('_', ' ')} education. "
            "Carry your Aadhaar, caste certificate and last education certificate to enrolment."
        )

    if topic == "income" and best:
        return (
            f"A certified {best.skill.name} in your area typically earns "
            f"{income_range(best.skill.avg_wage_monthly)} per month. "
            "Self-employment can go higher once you build a customer base."
            if best.skill.self_employable
            else f"A certified {best.skill.name} typically earns "
                 f"{income_range(best.skill.avg_wage_monthly)} per month."
        )

    if topic == "duration" and program:
        return (
            f"{program.title} takes {program.duration_weeks} weeks — about "
            f"{program.duration_hours} hours of training in "
            f"{'classroom and practical' if program.mode == 'offline' else program.mode} mode."
        )

    if topic == "progress":
        progress = build_progress(beneficiary)
        return (
            f"{name}, you are {progress.overall_percent}% through your livelihood journey. "
            f"Your current stage is {progress.current_stage}."
        )

    if topic in ("recommendation", "general") and best:
        return (
            f"{name}, your strongest match is {best.skill.name} at {best.match_score:.0f}%. "
            + " ".join((best.reasons or [])[:2])
        ).strip()

    if topic == "enroll" and program:
        return (
            f"To join {program.title}, tap Enroll on the training screen. Your application goes to "
            f"{program.provider.name if program.provider else 'the provider'} for eligibility "
            "verification, and you will see it appear on your progress timeline."
        )

    return _FALLBACK


# ── Public API ─────────────────────────────────────────────
_LANGUAGE_INSTRUCTION = {
    Language.HINDI: "Reply in Hindi, in Devanagari script. Use simple, everyday words.",
    Language.ENGLISH: "Reply in simple English, at about an 8th-standard reading level.",
    Language.SANTHALI: "Reply in Santhali. If unsure of a word, use the Hindi one.",
    Language.HO: "Reply in Ho. If unsure of a word, use the Hindi one.",
    Language.MUNDARI: "Reply in Mundari. If unsure of a word, use the Hindi one.",
}


def _prompt(beneficiary: Optional[Beneficiary], question: str, language: Language) -> List[ChatMessage]:
    system = (
        "You are Kaushal AI, a warm, patient livelihood and skilling counsellor for "
        "SC-community beneficiaries under India's PM-AJAY scheme in Jharkhand.\n"
        f"{_LANGUAGE_INSTRUCTION.get(language, _LANGUAGE_INSTRUCTION[Language.HINDI])}\n"
        "Keep answers under 4 short sentences. Be concrete and encouraging.\n\n"
        "GROUND RULES — this is a government service, so accuracy matters more than "
        "helpfulness:\n"
        "- Use ONLY the profile facts below for anything specific (their match, programme, "
        "fee, stipend, seats, timeline).\n"
        "- Never invent scheme names, subsidy amounts, eligibility rules or deadlines. If a "
        "fact isn't below, say you will check it rather than guessing.\n"
        "- Never promise a job, a placement, or a certain income.\n\n"
        f"--- BENEFICIARY PROFILE ---\n{_context(beneficiary)}"
    )
    return [ChatMessage("system", system), ChatMessage("user", question)]


def answer(db: Session, beneficiary: Optional[Beneficiary], question: str, language: Language) -> str:
    """Answer a beneficiary's question, grounded in their own record."""
    llm = get_llm()
    # The bundled mock provider only implements the interview's NEXT_PROMPT
    # protocol — asked anything else it answers with a bare acknowledgement — so
    # it is never consulted here. Zero-credential installs get the grounded
    # answerer, which is the better answer anyway.
    if llm.name != "mock":
        try:
            result = llm.chat(_prompt(beneficiary, question, language), temperature=0.3, max_tokens=400)
            if result.content and result.content.strip():
                return result.content.strip()
        except Exception as exc:  # noqa: BLE001
            log.warning("assistant_llm_failed", provider=llm.name, error=str(exc))
    return _deterministic_answer(beneficiary, question)


def stream(db: Session, beneficiary: Optional[Beneficiary], question: str, language: Language) -> Iterator[str]:
    """Yield the answer progressively, for the app's typing effect.

    A streaming provider is passed straight through so the first words reach the
    phone while the model is still writing. Everything else — including the
    grounded fallback — is chunked here so the app sees one uniform token stream
    and never has to care which path produced it.
    """
    llm = get_llm()
    if llm.name != "mock" and llm.supports_streaming:
        try:
            produced = False
            for delta in llm.stream(_prompt(beneficiary, question, language), temperature=0.3, max_tokens=400):
                produced = True
                yield delta
            if produced:
                return
        except Exception as exc:  # noqa: BLE001
            log.warning("assistant_stream_failed", provider=llm.name, error=str(exc))
            # Mid-stream failure: the app has partial text, so start a fresh
            # paragraph rather than splicing two answers into one sentence.
            yield "\n\n"

    for token in re.findall(r"\S+\s*", answer(db, beneficiary, question, language)):
        yield token
