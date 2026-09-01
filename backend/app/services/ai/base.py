"""Provider interfaces + shared data types."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Iterator, List, Literal, Optional

from app.models.enums import Language


@dataclass
class STTResult:
    text_original: str
    text_english: str
    language: Language
    confidence: float
    provider: str


@dataclass
class TTSResult:
    audio_url: str
    audio_base64: Optional[str]
    provider: str
    duration_seconds: float = 0.0


@dataclass
class ChatMessage:
    role: Literal["system", "assistant", "user"]
    content: str


@dataclass
class LLMResult:
    content: str
    provider: str
    model: str
    raw: dict = field(default_factory=dict)


class STTProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def transcribe(self, audio_base64: str, language: Language) -> STTResult: ...


class TTSProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def synthesize(self, text: str, language: Language) -> TTSResult: ...


class TranslationProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def translate(self, text: str, source: Language, target: Language) -> str: ...


class LLMProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def chat(self, messages: List[ChatMessage], *, temperature: float = 0.4, max_tokens: int = 512) -> LLMResult: ...

    def stream(
        self, messages: List[ChatMessage], *, temperature: float = 0.4, max_tokens: int = 512
    ) -> Iterator[str]:
        """Yield the answer in pieces. Providers that can't stream emit it in one go."""
        yield self.chat(messages, temperature=temperature, max_tokens=max_tokens).content

    @property
    def supports_streaming(self) -> bool:
        return type(self).stream is not LLMProvider.stream
