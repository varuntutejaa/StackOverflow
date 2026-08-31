"""Deterministic multilingual interview engine.

Flow:  voice/text turn
   ->  STT (+ translation to English)
   ->  keyword/regex entity extraction on the English text
   ->  scripted next question (localised) phrased by the LLM provider
   ->  TTS for the next question
   ->  on completion: assemble a structured beneficiary profile

The question script is data, not code, so new languages / questions are added
without touching logic. When a real LLM provider is configured it still only
*phrases* the next scripted prompt — extraction stays deterministic and
auditable, which matters for a government system.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from app.models.enums import (
    EducationLevel,
    EmploymentPreference,
    Language,
    Mobility,
)
from app.services.ai.base import ChatMessage
from app.services.ai.registry import get_llm

# ─────────────────────────────────────────────────────────────
# Question script — one entry per interview step.
# `field` names the profile key this step fills.
# ─────────────────────────────────────────────────────────────
QUESTION_SCRIPT: List[Dict] = [
    {
        "id": "intro",
        "field": None,
        "prompts": {
            Language.HINDI: "नमस्ते! मैं कौशAI हूँ। मैं आपके लिए सही हुनर और रोज़गार ढूँढने में मदद करूँगा। क्या हम शुरू करें?",
            Language.ENGLISH: "Hello! I am KaushAI. I will help you find the right skills and livelihood. Shall we begin?",
            Language.SANTHALI: "Johar! Iɲ KaushAI kana. Iɲ am lagit thik hunar ar rojgar ɲam re gohan em a. Ete a?",
            Language.HO: "Johar! Aiñ KaushAI tana. Aiñ am nangte thik hunar ar rojgar ɲam re gohan emaa. Ete ya?",
            Language.MUNDARI: "Johar! Aiñ KaushAI tanae. Aiñ am nangte thik hunar ar rojgar ɲam re gohan emaae. Eterube?",
        },
    },
    {
        "id": "name",
        "field": "full_name",
        "prompts": {
            Language.HINDI: "आपका पूरा नाम क्या है?",
            Language.ENGLISH: "What is your full name?",
            Language.SANTHALI: "Amaɡ pura ɲutum oka?",
            Language.HO: "Amaa pura ɲutum chikan?",
            Language.MUNDARI: "Amaa pura ɲutum chikanae?",
        },
    },
    {
        "id": "age_gender",
        "field": "age",
        "prompts": {
            Language.HINDI: "आपकी उम्र कितनी है?",
            Language.ENGLISH: "How old are you?",
            Language.SANTHALI: "Amaɡ umer tinaɡ?",
            Language.HO: "Amaa umer tinaa?",
            Language.MUNDARI: "Amaa umer tinaae?",
        },
    },
    {
        "id": "location",
        "field": "village",
        "prompts": {
            Language.HINDI: "आप किस गाँव और ज़िले में रहते हैं?",
            Language.ENGLISH: "Which village and district do you live in?",
            Language.SANTHALI: "Am okoy ato ar zila re tahen kana?",
            Language.HO: "Am okoy hatu ar zila re menaa?",
            Language.MUNDARI: "Am okoy hatu ar zila re menaae?",
        },
    },
    {
        "id": "education",
        "field": "education_level",
        "prompts": {
            Language.HINDI: "आपने कहाँ तक पढ़ाई की है? जैसे पाँचवीं, आठवीं, दसवीं, बारहवीं या आईटीआई?",
            Language.ENGLISH: "Up to what level have you studied? For example class 5, 8, 10, 12 or ITI?",
            Language.SANTHALI: "Am okoy dhap dhoreɡ padhao akat? class 5, 8, 10, 12 se ITI?",
            Language.HO: "Am okoy dhap padhao akan? class 5, 8, 10, 12 se ITI?",
            Language.MUNDARI: "Am okoy dhap padhao akanae? class 5, 8, 10, 12 se ITI?",
        },
    },
    {
        "id": "current_work",
        "field": "current_occupation",
        "prompts": {
            Language.HINDI: "अभी आप क्या काम करते हैं?",
            Language.ENGLISH: "What work do you currently do?",
            Language.SANTHALI: "Nitok am chet kami em?",
            Language.HO: "Naa am chikan kami tana?",
            Language.MUNDARI: "Niya am chikan kami tanae?",
        },
    },
    {
        "id": "family_work",
        "field": "family_occupation",
        "prompts": {
            Language.HINDI: "आपके परिवार का पारंपरिक काम क्या है?",
            Language.ENGLISH: "What is your family's traditional occupation?",
            Language.SANTHALI: "Amaɡ pariwar aɡ purana kami chet?",
            Language.HO: "Amaa pariwar aa purni kami chikan?",
            Language.MUNDARI: "Amaa pariwar aa purni kami chikanae?",
        },
    },
    {
        "id": "skills",
        "field": "skills",
        "prompts": {
            Language.HINDI: "आपको कौन-कौन से काम आते हैं? जैसे सिलाई, बिजली, मरम्मत, खेती, ड्राइविंग?",
            Language.ENGLISH: "What skills do you already have? Such as tailoring, electrical, repair, farming, driving?",
            Language.SANTHALI: "Amaɡ chet chet kami baɖay? sui-suhi, bijli, marammat, kheti, driving?",
            Language.HO: "Amaa chikan kami baɖay? sui kami, bijli, marammat, kheti, driving?",
            Language.MUNDARI: "Amaa chikan kami baɖayae? sui kami, bijli, marammat, kheti, driving?",
        },
    },
    {
        "id": "interests",
        "field": "interests",
        "prompts": {
            Language.HINDI: "आप किस क्षेत्र में काम सीखना चाहते हैं? जैसे इलेक्ट्रॉनिक्स, सोलर, ब्यूटी, ऑटो, कृषि?",
            Language.ENGLISH: "Which field do you want to build a livelihood in? Electronics, solar, beauty, auto, agriculture?",
            Language.SANTHALI: "Am okoy field re kami sikhao sanao? electronics, solar, beauty, auto, kheti?",
            Language.HO: "Am okoy field re kami sikhao sanang? electronics, solar, beauty, auto, kheti?",
            Language.MUNDARI: "Am okoy field re kami itu sanang? electronics, solar, beauty, auto, kheti?",
        },
    },
    {
        "id": "mobility_pref",
        "field": "mobility",
        "prompts": {
            Language.HINDI: "क्या आप काम या ट्रेनिंग के लिए अपने ज़िले से बाहर जा सकते हैं?",
            Language.ENGLISH: "Can you travel outside your district for work or training?",
            Language.SANTHALI: "Am kami se training lagit zila baherre calaɡ darea?",
            Language.HO: "Am kami se training nangte zila baherre senoa dareya?",
            Language.MUNDARI: "Am kami se training nangte zila baherre senoa dareyae?",
        },
    },
    {
        "id": "employment_pref",
        "field": "employment_preference",
        "prompts": {
            Language.HINDI: "क्या आप नौकरी करना चाहते हैं या अपना काम/दुकान शुरू करना चाहते हैं?",
            Language.ENGLISH: "Do you want a wage job, or to start your own work or business?",
            Language.SANTHALI: "Am naukri sanao se aɡ kami / dukan ehop sanao?",
            Language.HO: "Am naukri sanang se aa kami / dukan ehop sanang?",
            Language.MUNDARI: "Am naukri sanang se aa kami / dukan ehop sanang?",
        },
    },
    {
        "id": "constraints",
        "field": "constraints",
        "prompts": {
            Language.HINDI: "क्या कोई परेशानी है जो आपको ट्रेनिंग करने से रोकती है? जैसे पैसा, समय, परिवार, दूरी?",
            Language.ENGLISH: "Any constraints that could stop you from training? Money, time, family, distance?",
            Language.SANTHALI: "Chet badha menaɡ training lagit? taka, oɖe, pariwar, sange?",
            Language.HO: "Chikan baadha menaa training nangte? taka, samay, pariwar, sangin?",
            Language.MUNDARI: "Chikan baadha menaae training nangte? taka, samay, pariwar, sangin?",
        },
    },
    {
        "id": "closing",
        "field": None,
        "prompts": {
            Language.HINDI: "धन्यवाद! मैं आपकी जानकारी के आधार पर सबसे अच्छे हुनर और ट्रेनिंग सुझा रहा हूँ।",
            Language.ENGLISH: "Thank you! Based on your answers I am now preparing your best-fit skills and training.",
            Language.SANTHALI: "Sarhao! Amaɡ jawab khon iɲ thik hunar ar training tayar kana.",
            Language.HO: "Sarhao! Amaa jawab khon aiñ thik hunar ar training tayar tana.",
            Language.MUNDARI: "Sarhao! Amaa jawab khon aiñ thik hunar ar training tayar tanae.",
        },
    },
]

TOTAL_STEPS = len(QUESTION_SCRIPT)
# index of the last entry that expects a spoken answer (everything after is the
# closing statement, which needs no user turn)
LAST_ANSWERABLE_INDEX = TOTAL_STEPS - 2

# ─────────────────────────────────────────────────────────────
# Extraction dictionaries (matched against the English text)
# ─────────────────────────────────────────────────────────────
_EDU_PATTERNS: List[Tuple[str, EducationLevel]] = [
    (r"\b(post ?graduat|m\.?a\.?|m\.?sc|mba)\b", EducationLevel.POSTGRADUATE),
    (r"\b(graduat|b\.?a\.?|b\.?sc|b\.?com|degree)\b", EducationLevel.GRADUATE),
    (r"\b(diploma|polytechnic)\b", EducationLevel.DIPLOMA),
    (r"\b(iti|i\.t\.i)\b", EducationLevel.ITI),
    (r"\b(12th|twelfth|class 12|intermediate|senior secondary|\+2)\b", EducationLevel.SENIOR_SECONDARY),
    (r"\b(10th|tenth|class 10|matric|secondary)\b", EducationLevel.SECONDARY),
    (r"\b(8th|eighth|class 8|middle)\b", EducationLevel.MIDDLE),
    (r"\b(5th|fifth|class 5|primary)\b", EducationLevel.PRIMARY),
    (r"\b(never|no schooling|illiterate|not stud|nothing)\b", EducationLevel.NONE),
]

_SKILL_KEYWORDS = {
    "tailoring": ["tailor", "sewing", "stitch", "silai", "sui"],
    "electrical": ["electric", "wiring", "bijli", "lineman"],
    "solar": ["solar", "pv", "panel"],
    "mobile repair": ["mobile repair", "phone repair", "mobile"],
    "electronics": ["electronic", "circuit", "tv repair"],
    "driving": ["driv", "gaadi", "vehicle", "truck", "auto rickshaw"],
    "masonry": ["mason", "raj mistri", "construction", "brick"],
    "welding": ["weld", "fabricat"],
    "farming": ["farm", "agricultur", "kheti", "crop", "cultivat"],
    "poultry": ["poultry", "hen", "chicken", "murgi"],
    "dairy": ["dairy", "milk", "cattle", "cow", "buffalo"],
    "beautician": ["beauty", "parlour", "makeup", "salon"],
    "computer": ["computer", "typing", "data entry", "ms office"],
    "carpentry": ["carpent", "wood", "furniture"],
    "plumbing": ["plumb", "pipe fitting"],
    "handloom": ["handloom", "weav", "loom"],
    "food processing": ["pickle", "papad", "food processing", "snack"],
    "retail": ["shop", "dukan", "retail", "kirana", "store"],
}

_INTEREST_KEYWORDS = _SKILL_KEYWORDS  # same vocabulary for aspirations

_OCCUPATION_KEYWORDS = {
    "agriculture": ["farm", "agricultur", "kheti", "crop", "field work"],
    "daily wage labour": ["daily wage", "labour", "labor", "mazdoor", "manrega", "mgnrega", "coolie"],
    "construction": ["construction", "mason", "helper"],
    "domestic work": ["domestic", "house help", "maid"],
    "shopkeeper": ["shop", "dukan", "vendor", "hawker"],
    "driver": ["driver", "driving"],
    "unemployed": ["nothing", "no work", "unemploy", "jobless", "sitting at home"],
    "student": ["student", "studying"],
    "weaver": ["weav", "handloom", "loom"],
    "artisan": ["artisan", "craft", "pottery", "bamboo"],
}


def _match_education(text: str) -> Optional[EducationLevel]:
    t = text.lower()
    for pattern, level in _EDU_PATTERNS:
        if re.search(pattern, t):
            return level
    return None


def _match_multi(text: str, vocab: Dict[str, List[str]]) -> List[str]:
    t = text.lower()
    found = []
    for label, kws in vocab.items():
        if any(k in t for k in kws):
            found.append(label)
    return found


def _match_occupation(text: str) -> Optional[str]:
    hits = _match_multi(text, _OCCUPATION_KEYWORDS)
    return hits[0] if hits else None


def _match_mobility(text: str) -> Mobility:
    t = text.lower()
    if re.search(r"\b(anywhere|any state|metro|city|outside state|migrat)\b", t):
        return Mobility.ANYWHERE
    if re.search(r"\b(yes|can go|other district|nearby town|block)\b", t):
        return Mobility.DISTRICT
    if re.search(r"\b(state)\b", t):
        return Mobility.STATE
    if re.search(r"\b(no|cannot|only village|stay here|local|nearby)\b", t):
        return Mobility.LOCAL
    return Mobility.LOCAL


def _match_employment_pref(text: str) -> EmploymentPreference:
    t = text.lower()
    if re.search(r"\b(own|self|business|shop|dukan|entrepreneur|start)\b", t):
        return EmploymentPreference.SELF_EMPLOYMENT
    if re.search(r"\b(job|naukri|salary|company|wage|employ)\b", t):
        return EmploymentPreference.WAGE_EMPLOYMENT
    if re.search(r"\b(apprentice|trainee)\b", t):
        return EmploymentPreference.APPRENTICESHIP
    return EmploymentPreference.ANY


def _match_age(text: str) -> Optional[int]:
    m = re.search(r"\b(1[0-9]|[2-6][0-9])\b", text)
    return int(m.group(1)) if m else None


_CONSTRAINT_KEYWORDS = {
    "financial": ["money", "paisa", "taka", "poor", "afford", "fees", "financial"],
    "family responsibility": ["family", "children", "parents", "look after", "marriage"],
    "distance": ["far", "distance", "transport", "no bus", "remote"],
    "time": ["time", "busy", "season", "harvest"],
    "health": ["health", "sick", "disability", "unwell"],
    "language": ["language", "hindi", "english", "cannot read"],
    "childcare": ["small child", "infant", "baby"],
}


def extract_entities(step_id: str, text_english: str) -> Dict:
    """Return a dict of profile-relevant entities for one answer."""
    out: Dict = {}
    if step_id == "name":
        # take the longest capitalised-ish token span, else first 4 words
        cleaned = re.sub(r"(?i)\b(my name is|i am|this is|mera naam|naam)\b", "", text_english).strip(" .,")
        if cleaned:
            out["full_name"] = " ".join(cleaned.split()[:4]).title()
    elif step_id == "age_gender":
        age = _match_age(text_english)
        if age:
            out["age"] = age
        if re.search(r"\b(female|woman|girl|mahila|aurat)\b", text_english.lower()):
            out["gender"] = "female"
        elif re.search(r"\b(male|man|boy|purush|aadmi)\b", text_english.lower()):
            out["gender"] = "male"
    elif step_id == "location":
        m = re.search(r"(?:village|gaon|gram)\s+([a-z]+)", text_english.lower())
        if m:
            out["village"] = m.group(1).title()
        m2 = re.search(r"(?:district|zila|jila)\s+([a-z]+)", text_english.lower())
        if m2:
            out["district"] = m2.group(1).title()
        if "village" not in out:
            toks = [w for w in re.findall(r"[A-Za-z]+", text_english) if len(w) > 2]
            if toks:
                out["village"] = toks[0].title()
    elif step_id == "education":
        lvl = _match_education(text_english)
        if lvl:
            out["education_level"] = lvl.value
        out["education_notes"] = text_english.strip()[:200]
    elif step_id == "current_work":
        occ = _match_occupation(text_english)
        out["current_occupation"] = occ or text_english.strip()[:80]
    elif step_id == "family_work":
        occ = _match_occupation(text_english)
        out["family_occupation"] = occ or text_english.strip()[:80]
    elif step_id == "skills":
        out["skills"] = _match_multi(text_english, _SKILL_KEYWORDS)
    elif step_id == "interests":
        out["interests"] = _match_multi(text_english, _INTEREST_KEYWORDS)
    elif step_id == "mobility_pref":
        out["mobility"] = _match_mobility(text_english).value
    elif step_id == "employment_pref":
        out["employment_preference"] = _match_employment_pref(text_english).value
    elif step_id == "constraints":
        out["constraints"] = _match_multi(text_english, _CONSTRAINT_KEYWORDS)
    return out


def next_question(step_index: int, language: Language) -> Optional[Dict]:
    if step_index >= TOTAL_STEPS:
        return None
    entry = QUESTION_SCRIPT[step_index]
    return {
        "id": entry["id"],
        "field": entry["field"],
        "text": entry["prompts"].get(language, entry["prompts"][Language.ENGLISH]),
        "language": language.value,
    }


def phrase_question(question_text: str, language: Language, had_previous_answer: bool) -> str:
    """Let the configured LLM provider add a natural acknowledgement."""
    llm = get_llm()
    system = f"NEXT_PROMPT::{language.value}::{question_text}\n" + (
        "You are KaushAI, a warm, patient livelihood counsellor for rural SC youth. "
        "Briefly acknowledge the last answer in the SAME language, then ask the given next question. "
        "Keep it under 2 sentences. Do not add new questions."
    )
    messages = [ChatMessage("system", system)]
    if had_previous_answer:
        messages.append(ChatMessage("user", "(previous answer recorded)"))
    try:
        result = llm.chat(messages, temperature=0.3, max_tokens=160)
        return result.content or question_text
    except Exception:  # noqa: BLE001
        return question_text


def build_structured_profile(entities: Dict) -> Dict:
    """Merge accumulated entities into the canonical beneficiary profile shape."""
    profile = {
        "full_name": entities.get("full_name"),
        "age": entities.get("age"),
        "gender": entities.get("gender", "undisclosed"),
        "village": entities.get("village"),
        "district": entities.get("district"),
        "education_level": entities.get("education_level", "none"),
        "education_notes": entities.get("education_notes"),
        "current_occupation": entities.get("current_occupation"),
        "family_occupation": entities.get("family_occupation"),
        "skills": sorted(set(entities.get("skills", []))),
        "interests": sorted(set(entities.get("interests", []))),
        "constraints": sorted(set(entities.get("constraints", []))),
        "mobility": entities.get("mobility", "local"),
        "employment_preference": entities.get("employment_preference", "any"),
        "confidence": _profile_confidence(entities),
        "source": "kaushai-interview-engine/1.0",
    }
    return profile


def _profile_confidence(entities: Dict) -> float:
    key_fields = [
        "age",
        "education_level",
        "current_occupation",
        "skills",
        "interests",
        "mobility",
        "employment_preference",
    ]
    present = sum(1 for k in key_fields if entities.get(k))
    return round(present / len(key_fields), 2)
