from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Recommendation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"

    beneficiary_id: Mapped[str] = mapped_column(
        ForeignKey("beneficiaries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True, nullable=False)
    nsqf_role_id: Mapped[Optional[str]] = mapped_column(ForeignKey("nsqf_roles.id"), nullable=True)
    suggested_program_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("training_programs.id"), nullable=True
    )
    interview_id: Mapped[Optional[str]] = mapped_column(ForeignKey("interviews.id"), nullable=True)

    rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100

    # Explainability payload
    factor_scores: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    reasons: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    skill_gaps: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    career_pathway: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    engine_version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)
    is_accepted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    beneficiary = relationship("Beneficiary", back_populates="recommendations")
    skill = relationship("Skill", lazy="joined")
    nsqf_role = relationship("NsqfRole", lazy="joined")
    suggested_program = relationship("TrainingProgram", lazy="joined")
