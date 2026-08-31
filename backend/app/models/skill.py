from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

# NSQF job-role  <->  skill  many-to-many
role_skill_link = Table(
    "role_skill_link",
    Base.metadata,
    Column("role_id", ForeignKey("nsqf_roles.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Skill(UUIDMixin, TimestampMixin, Base):
    """An NSQF-aligned skill / competency (maps to a QP where relevant)."""

    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(40), unique=True, nullable=True)  # e.g. QP code
    sector: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    nsqf_level: Mapped[int] = mapped_column(Integer, index=True, nullable=False, default=3)
    min_education: Mapped[str] = mapped_column(String(24), default="none", nullable=False)
    min_age: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    max_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    typical_duration_hours: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    avg_wage_monthly: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    self_employable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # keyword tags used for interest / skill matching
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # National demand index 0-100 (simulated baseline, overridden per-district by SkillDemand)
    demand_index: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles = relationship("NsqfRole", secondary=role_skill_link, back_populates="skills")
    training_programs = relationship("TrainingProgram", back_populates="skill")


class NsqfRole(UUIDMixin, TimestampMixin, Base):
    """A job role in the NSQF catalogue (NCO / QP aligned)."""

    __tablename__ = "nsqf_roles"

    title: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    nco_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    qp_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sector: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    nsqf_level: Mapped[int] = mapped_column(Integer, index=True, nullable=False, default=3)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    eligibility: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entry_wage_monthly: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    growth_outlook: Mapped[str] = mapped_column(String(20), default="stable", nullable=False)  # declining|stable|growing|high
    self_employment_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    skills = relationship("Skill", secondary=role_skill_link, back_populates="roles")
