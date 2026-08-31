"""OpenAI-backed providers. Only used when AI_*_PROVIDER=openai and
OPENAI_API_KEY is set. Kept import-safe (httpx only) so the app runs without
the openai SDK installed.
"""
from __future__ import annotations

import base64
from typing import List

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.enums import Language
from app.services.ai.base import (
    ChatMessage,
    LLMProvider,
    LLMResult,
    STTProvider,
    STTResult,
    TTSProvider,
    TTSResult,
)
from app.services.ai.mock_providers import MockTranslationProvider

log = get_logger("ai.openai")
_BASE = "https://api.openai.com/v1"

_LANG_NAME = {
    Language.HINDI: "Hindi",
    Language.ENGLISH: "English",
    Language.SANTHALI: "Santhali",
    Language.HO: "Ho",
    Language.MUNDARI: "Mundari",
}


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.openai_api_key}"}


class OpenAISTTProvider(STTProvider):
    name = "openai"

    def transcribe(self, audio_base64: str, language: Language) -> STTResult:
        audio_bytes = base64.b64decode(audio_base64 + "===")
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": "whisper-1", "language": language.value[:2]}
        with httpx.Client(timeout=60) as c:
            r = c.post(f"{_BASE}/audio/transcriptions", headers=_headers(), files=files, data=data)
            r.raise_for_status()
            text_original = r.json().get("text", "")
        text_english = text_original
        if language != Language.ENGLISH:
            text_english = OpenAILLMProvider().chat(
                [
                    ChatMessage("system", "Translate the user text to English. Output only the translation."),
                    ChatMessage("user", text_original),
                ]
            ).content
        return STTResult(text_original, text_english, language, 0.9, self.name)


class OpenAITTSProvider(TTSProvider):
    name = "openai"

    def synthesize(self, text: str, language: Language) -> TTSResult:
        with httpx.Client(timeout=60) as c:
            r = c.post(
                f"{_BASE}/audio/speech",
                headers=_headers(),
                json={"model": "tts-1", "voice": "alloy", "input": text},
            )
            r.raise_for_status()
            b64 = base64.b64encode(r.content).decode()
        return TTSResult(f"data:audio/mpeg;base64,{b64}", b64, self.name)


class OpenAITranslationProvider(MockTranslationProvider):
    name = "openai"

    def translate(self, text: str, source: Language, target: Language) -> str:
        if source == target:
            return text
        return OpenAILLMProvider().chat(
            [
                ChatMessage(
                    "system",
                    f"Translate from {_LANG_NAME.get(source, source.value)} to "
                    f"{_LANG_NAME.get(target, target.value)}. Output only the translation.",
                ),
                ChatMessage("user", text),
            ]
        ).content


class OpenAILLMProvider(LLMProvider):
    name = "openai"
    model = "gpt-4o-mini"

    def chat(self, messages: List[ChatMessage], *, temperature: float = 0.4, max_tokens: int = 512) -> LLMResult:
        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        with httpx.Client(timeout=60) as c:
            r = c.post(f"{_BASE}/chat/completions", headers=_headers(), json=payload)
            r.raise_for_status()
            body = r.json()
        content = body["choices"][0]["message"]["content"]
        return LLMResult(content=content, provider=self.name, model=self.model, raw=body)
