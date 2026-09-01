"""Groq-backed LLM provider.

Groq serves an OpenAI-compatible Chat Completions API, so this is a thin client
rather than a new integration surface — but it is the one provider here that
streams, which is what makes the app's assistant type its answer out instead of
blocking for a second and dumping a paragraph.

Only the LLM is Groq. STT, TTS and translation stay on their own providers, so
`AI_LLM_PROVIDER=groq` is a safe, isolated switch. In particular the app's UI
strings are *not* translated through here — they ship preloaded in the APK, so
the interface never waits on a network call to render a label.
"""
from __future__ import annotations

import json
from typing import Iterator, List

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.base import ChatMessage, LLMProvider, LLMResult

log = get_logger("ai.groq")

_BASE = "https://api.groq.com/openai/v1"

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }


def _payload(messages: List[ChatMessage], temperature: float, max_tokens: int, stream: bool) -> dict:
    return {
        "model": settings.groq_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
    }


class GroqLLMProvider(LLMProvider):
    name = "groq"

    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set")
        self.model = settings.groq_model

    def chat(
        self, messages: List[ChatMessage], *, temperature: float = 0.4, max_tokens: int = 512
    ) -> LLMResult:
        with httpx.Client(timeout=settings.groq_timeout_seconds) as c:
            r = c.post(
                f"{_BASE}/chat/completions",
                headers=_headers(),
                json=_payload(messages, temperature, max_tokens, stream=False),
            )
            r.raise_for_status()
            body = r.json()
        return LLMResult(
            content=body["choices"][0]["message"]["content"],
            provider=self.name,
            model=self.model,
            raw=body,
        )

    def stream(
        self, messages: List[ChatMessage], *, temperature: float = 0.4, max_tokens: int = 512
    ) -> Iterator[str]:
        """Yield content deltas as they arrive (SSE).

        Anything malformed in the stream is skipped rather than raised: a dropped
        delta should degrade the typing effect, not fail the whole answer.
        """
        with httpx.Client(timeout=settings.groq_timeout_seconds) as c:
            with c.stream(
                "POST",
                f"{_BASE}/chat/completions",
                headers=_headers(),
                json=_payload(messages, temperature, max_tokens, stream=True),
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        return
                    try:
                        delta = json.loads(data)["choices"][0]["delta"].get("content")
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
                    if delta:
                        yield delta
