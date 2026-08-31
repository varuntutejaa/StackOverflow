from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import InterviewStatus, Language, MessageRole


class InterviewCreate(BaseModel):
    beneficiary_id: str
    language: Language = Language.HINDI
    channel: str = "voice"
    is_demo: bool = False


class InterviewMessageOut(BaseModel):
    id: str
    sequence: int
    role: MessageRole
    language: Language
    text_original: Optional[str] = None
    text_english: Optional[str] = None
    audio_url: Optional[str] = None
    stt_confidence: Optional[float] = None
    intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    model_config = {"from_attributes": True}


class InterviewOut(BaseModel):
    id: str
    beneficiary_id: str
    language: Language
    channel: str
    status: InterviewStatus
    current_step: int
    total_steps: int
    completion_pct: float
    transcript: Optional[str] = None
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    structured_profile: Optional[dict] = None
    stt_provider: str
    llm_provider: str
    is_demo: bool
    created_at: datetime
    updated_at: datetime
    messages: List[InterviewMessageOut] = Field(default_factory=list)
    model_config = {"from_attributes": True}


class TurnRequest(BaseModel):
    """A single conversational turn from the beneficiary."""

    text: Optional[str] = Field(default=None, description="Transcribed / typed text in the interview language")
    text_english: Optional[str] = Field(
        default=None,
        description="Optional English translation already produced by a client-side STT/MT step. "
        "When present the server skips its own translation.",
    )
    audio_base64: Optional[str] = Field(default=None, description="Optional base64 WAV/OGG for STT")
    language: Optional[Language] = None


class TurnResponse(BaseModel):
    interview: InterviewOut
    assistant_message: InterviewMessageOut
    is_complete: bool
    next_prompt_tts_url: Optional[str] = None


class TranscribeRequest(BaseModel):
    audio_base64: str
    language: Language = Language.HINDI


class TranscribeResponse(BaseModel):
    text_original: str
    text_english: str
    language: Language
    confidence: float


class SynthesizeRequest(BaseModel):
    text: str
    language: Language = Language.HINDI


class SynthesizeResponse(BaseModel):
    audio_url: str
    audio_base64: Optional[str] = None
    provider: str
