from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import JSON, Boolean, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import OutcomeStage, OutcomeType


class Outcome(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "outcomes"

    beneficiary_id: Mapped[str] = mapped_column(
        ForeignKey("beneficiaries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    application_id: Mapped[Optional[str]] = mapped_column(ForeignKey("applications.id"), nullable=True)
    recommendation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("recommendations.id"), nullable=True)

    stage: Mapped[OutcomeStage] = mapped_column(
        Enum(OutcomeStage, native_enum=False, length=20), nullable=False, index=True
    )
    outcome_type: Mapped[Optional[OutcomeType]] = mapped_column(
        Enum(OutcomeType, native_enum=False, length=20), nullable=True, index=True
    )
    occurred_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    employer_or_venture: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(120), index=True, nullable=True)

    income_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    income_after: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_source: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    beneficiary = relationship("Beneficiary", back_populates="outcomes")

    @property
    def income_delta_pct(self) -> Optional[float]:
        if self.income_before and self.income_after and self.income_before > 0:
            return round((self.income_after - self.income_before) / self.income_before * 100, 1)
        return None
