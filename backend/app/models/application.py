from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ApplicationStatus


class Application(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    beneficiary_id: Mapped[str] = mapped_column(
        ForeignKey("beneficiaries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    program_id: Mapped[str] = mapped_column(
        ForeignKey("training_programs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    recommendation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("recommendations.id"), nullable=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=16),
        default=ApplicationStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    eligibility_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    eligibility_report: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    enrolled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    progress_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    attendance_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    assessment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    certificate_number: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)
    certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    beneficiary = relationship("Beneficiary", back_populates="applications")
    program = relationship("TrainingProgram", back_populates="applications", lazy="joined")
