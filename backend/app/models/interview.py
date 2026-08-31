from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import InterviewStatus, Language, MessageRole


class Interview(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "interviews"

    beneficiary_id: Mapped[str] = mapped_column(
        ForeignKey("beneficiaries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    conducted_by_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)

    language: Mapped[Language] = mapped_column(
        Enum(Language, native_enum=False, length=8), default=Language.HINDI, nullable=False
    )
    channel: Mapped[str] = mapped_column(String(20), default="voice", nullable=False)  # voice|text|ivr
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus, native_enum=False, length=16),
        default=InterviewStatus.CREATED,
        nullable=False,
        index=True,
    )

    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    completion_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Full plain-text transcript (translated to English for analysis)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Named entities aggregated across the conversation
    extracted_entities: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # Final structured profile handed to the recommendation engine
    structured_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    stt_provider: Mapped[str] = mapped_column(String(24), default="mock", nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(24), default="mock", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    beneficiary = relationship("Beneficiary", back_populates="interviews")
    messages = relationship(
        "InterviewMessage",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewMessage.sequence",
    )


class InterviewMessage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "interview_messages"

    interview_id: Mapped[str] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False, length=12), nullable=False
    )

    language: Mapped[Language] = mapped_column(
        Enum(Language, native_enum=False, length=8), default=Language.HINDI, nullable=False
    )
    # what the speaker actually said, in their language
    text_original: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # English translation used for analysis
    text_english: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    stt_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    intent: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    entities: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    interview = relationship("Interview", back_populates="messages")
