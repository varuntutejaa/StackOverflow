"""Fully-functional MOCK providers.

These make the entire voice → STT → understanding → conversation → TTS loop
work end-to-end with **no external credentials**. They are deterministic and
clearly labelled so a demo is reproducible. Everything they emit is marked
`provider="mock"`.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import Dict, List

from app.models.enums import Language
from app.services.ai.base import (
    ChatMessage,
    LLMProvider,
    LLMResult,
    STTProvider,
    STTResult,
    TranslationProvider,
    TTSProvider,
    TTSResult,
)

# ── tiny bilingual lexicon used to fake translation of common livelihood terms ──
_LEXICON: Dict[str, Dict[str, str]] = {
    "kheti": {"en": "farming", "src": "hi"},
    "खेती": {"en": "farming", "src": "hi"},
    "मजदूरी": {"en": "daily wage labour", "src": "hi"},
    "बिजली": {"en": "electricity", "src": "hi"},
    "सोलर": {"en": "solar", "src": "hi"},
    "इलेक्ट्रॉनिक": {"en": "electronics", "src": "hi"},
    "सिलाई": {"en": "tailoring", "src": "hi"},
    "दुकान": {"en": "shop", "src": "hi"},
    "गाड़ी": {"en": "vehicle", "src": "hi"},
    "मोबाइल": {"en": "mobile phone", "src": "hi"},
    "अपना": {"en": "own", "src": "hi"},
    "काम": {"en": "work", "src": "hi"},
}

_STT_SAMPLE_BY_LANG = {
    Language.HINDI: "मैं दसवीं पास हूँ और अभी खेती का काम करता हूँ, मुझे बिजली और सोलर का काम सीखना है",
    Language.ENGLISH: "I have passed class 10 and currently do farming, I want to learn solar and electrical work",
    Language.SANTHALI: "iɲ class 10 pass kana ar nitok kheti kami, iɲ solar kami tege sikhao lagit",
    Language.HO: "aiñ class 10 pass tana ar naa kheti kami, aiñ solar kami sikhao sanao tana",
    Language.MUNDARI: "aiñ class 10 pass tanae ar niya kheti kami, aiñ solar kami itu sanang tanae",
}


def _fake_audio_data_uri(text: str, language: Language) -> str:
    digest = hashlib.sha1(f"{language.value}:{text}".encode()).hexdigest()[:16]
    payload = json.dumps({"mock_tts": True, "lang": language.value, "hash": digest, "text": text[:120]})
    b64 = base64.b64encode(payload.encode()).decode()
    return f"data:audio/mock;base64,{b64}"


class MockSTTProvider(STTProvider):
    name = "mock"

    def transcribe(self, audio_base64: str, language: Language) -> STTResult:
        # If the "audio" actually carries a JSON {"text": "..."} payload (used by
        # the web demo which sends typed text), honour it. Otherwise return a
        # deterministic sample utterance for the language.
        text_original = _STT_SAMPLE_BY_LANG.get(language, _STT_SAMPLE_BY_LANG[Language.ENGLISH])
        try:
            decoded = base64.b64decode(audio_base64 + "===").decode("utf-8", "ignore")
            obj = json.loads(decoded)
            if isinstance(obj, dict) and obj.get("text"):
                text_original = str(obj["text"])
        except Exception:  # noqa: BLE001 - best effort
            pass

        translator = MockTranslationProvider()
        text_english = translator.translate(text_original, language, Language.ENGLISH)
        # deterministic pseudo-confidence
        conf = 0.78 + (int(hashlib.md5(text_original.encode()).hexdigest(), 16) % 20) / 100
        return STTResult(
            text_original=text_original,
            text_english=text_english,
            language=language,
            confidence=round(min(conf, 0.98), 2),
            provider=self.name,
        )


class MockTranslationProvider(TranslationProvider):
    name = "mock"

    def translate(self, text: str, source: Language, target: Language) -> str:
        if source == target:
            return text
        if target != Language.ENGLISH:
            # We only mock translation *into* English for analysis.
            return text
        out = text
        for token, meta in _LEXICON.items():
            out = re.sub(re.escape(token), meta["en"], out, flags=re.IGNORECASE)
        # crude Devanagari / tribal-script stripping fallback
        if re.search(r"[^\x00-\x7F]", out):
            out = f"{out}  [auto-translated · mock]"
        return out


class MockTTSProvider(TTSProvider):
    name = "mock"

    def synthesize(self, text: str, language: Language) -> TTSResult:
        return TTSResult(
            audio_url=_fake_audio_data_uri(text, language),
            audio_base64=None,
            provider=self.name,
            duration_seconds=round(len(text) / 14.0, 1),
        )


class MockLLMProvider(LLMProvider):
    """A deterministic 'assistant' that rephrases the scripted interview prompt
    and lightly acknowledges the last user answer. Real reasoning lives in the
    interview engine; this only adds natural phrasing."""

    name = "mock"
    model = "kaushai-mock-1"

    _ACK = {
        Language.HINDI: "समझ गया। ",
        Language.ENGLISH: "Got it. ",
        Language.SANTHALI: "Bujhaw ena. ",
        Language.HO: "Bujha jana. ",
        Language.MUNDARI: "Bujhaw jana. ",
    }

    def chat(self, messages: List[ChatMessage], *, temperature: float = 0.4, max_tokens: int = 512) -> LLMResult:
        system = next((m.content for m in messages if m.role == "system"), "")
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        # The engine passes the desired next question as the system directive:
        #   "NEXT_PROMPT::<lang>::<text>"
        lang = Language.HINDI
        prompt_text = ""
        for line in system.splitlines():
            if line.startswith("NEXT_PROMPT::"):
                _, lang_code, prompt_text = line.split("::", 2)
                try:
                    lang = Language(lang_code)
                except ValueError:
                    lang = Language.HINDI
        ack = self._ACK.get(lang, "") if last_user else ""
        content = f"{ack}{prompt_text}".strip()
        return LLMResult(content=content, provider=self.name, model=self.model, raw={"mock": True})
