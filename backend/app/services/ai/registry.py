"""Provider factory. Reads env config, falls back to mock on any error."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.base import LLMProvider, STTProvider, TranslationProvider, TTSProvider
from app.services.ai.mock_providers import (
    MockLLMProvider,
    MockSTTProvider,
    MockTranslationProvider,
    MockTTSProvider,
)

log = get_logger("ai.registry")


def _safe(provider_name: str, factory, mock):
    try:
        return factory()
    except Exception as exc:  # noqa: BLE001
        log.warning("ai_provider_fallback", provider=provider_name, error=str(exc))
        return mock()


@lru_cache
def get_stt() -> STTProvider:
    p = settings.ai_stt_provider.lower()
    if p == "openai" and settings.openai_api_key:
        from app.services.ai.openai_providers import OpenAISTTProvider

        return _safe("openai-stt", OpenAISTTProvider, MockSTTProvider)
    return MockSTTProvider()


@lru_cache
def get_tts() -> TTSProvider:
    p = settings.ai_tts_provider.lower()
    if p == "openai" and settings.openai_api_key:
        from app.services.ai.openai_providers import OpenAITTSProvider

        return _safe("openai-tts", OpenAITTSProvider, MockTTSProvider)
    return MockTTSProvider()


@lru_cache
def get_translator() -> TranslationProvider:
    p = settings.ai_translate_provider.lower()
    if p == "openai" and settings.openai_api_key:
        from app.services.ai.openai_providers import OpenAITranslationProvider

        return _safe("openai-translate", OpenAITranslationProvider, MockTranslationProvider)
    return MockTranslationProvider()


@lru_cache
def get_llm() -> LLMProvider:
    p = settings.ai_llm_provider.lower()
    if p == "openai" and settings.openai_api_key:
        from app.services.ai.openai_providers import OpenAILLMProvider

        return _safe("openai-llm", OpenAILLMProvider, MockLLMProvider)
    return MockLLMProvider()


def provider_status() -> dict:
    return {
        "stt": get_stt().name,
        "tts": get_tts().name,
        "translate": get_translator().name,
        "llm": get_llm().name,
        "mock_mode": get_llm().name == "mock",
    }
