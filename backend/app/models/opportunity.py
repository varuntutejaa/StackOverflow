from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Opportunity(UUIDMixin, TimestampMixin, Base):
    """A local livelihood / job / self-employment opportunity signal."""

    __tablename__ = "opportunities"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(24), default="wage_job", nullable=False)  # wage_job|self_employment|apprenticeship|scheme
    sector: Mapped[str] = mapped_column(String(120), index=True, nullable=False)

    location_id: Mapped[Optional[str]] = mapped_column(ForeignKey("locations.id"), index=True, nullable=True)
    skill_id: Mapped[Optional[str]] = mapped_column(ForeignKey("skills.id"), index=True, nullable=True)
    nsqf_role_id: Mapped[Optional[str]] = mapped_column(ForeignKey("nsqf_roles.id"), nullable=True)

    employer: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    openings: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    wage_monthly_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wage_monthly_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    source: Mapped[str] = mapped_column(String(80), default="simulated", nullable=False)
    valid_till: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    location = relationship("Location", lazy="joined")
    skill = relationship("Skill", lazy="joined")


class SkillDemand(UUIDMixin, TimestampMixin, Base):
    """District x Skill demand/supply snapshot powering the livelihood map."""

    __tablename__ = "skill_demand"
    __table_args__ = (UniqueConstraint("location_id", "skill_id", name="uq_skill_demand"),)

    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True, nullable=False)

    demand_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)   # 0-100
    supply_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)   # 0-100 (trained/available workforce)
    open_positions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    trained_workforce: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_beneficiaries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    period: Mapped[str] = mapped_column(String(16), default="2026-Q1", nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    location = relationship("Location", lazy="joined")
    skill = relationship("Skill", lazy="joined")

    @property
    def gap_score(self) -> float:
        return round(self.demand_score - self.supply_score, 1)
