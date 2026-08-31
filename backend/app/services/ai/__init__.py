"""AI provider abstraction layer.

Every external capability (speech-to-text, text-to-speech, translation, LLM
conversation) is accessed through a narrow interface. Swap providers by
changing environment variables only — no application code changes.
"""
from app.services.ai.base import (
    ChatMessage,
    LLMProvider,
    STTProvider,
    STTResult,
    TranslationProvider,
    TTSProvider,
    TTSResult,
)
from app.services.ai.registry import get_llm, get_stt, get_translator, get_tts

__all__ = [
    "ChatMessage",
    "LLMProvider",
    "STTProvider",
    "STTResult",
    "TranslationProvider",
    "TTSProvider",
    "TTSResult",
    "get_llm",
    "get_stt",
    "get_translator",
    "get_tts",
]
