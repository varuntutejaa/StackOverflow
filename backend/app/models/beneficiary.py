from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import (
    BeneficiaryStatus,
    EducationLevel,
    EmploymentPreference,
    Gender,
    Language,
    Mobility,
)


class Beneficiary(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "beneficiaries"

    # ── Identity ───────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Gender] = mapped_column(
        Enum(Gender, native_enum=False, length=16), default=Gender.UNDISCLOSED, nullable=False
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), index=True, nullable=True)
    preferred_language: Mapped[Language] = mapped_column(
        Enum(Language, native_enum=False, length=8), default=Language.HINDI, nullable=False, index=True
    )

    # PM-AJAY / social identifiers (stored, never exposed raw in list APIs)
    social_category: Mapped[str] = mapped_column(String(16), default="SC", nullable=False)
    pmajay_id: Mapped[Optional[str]] = mapped_column(String(32), unique=True, nullable=True)
    household_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # ── Location ───────────────────────────────────────────
    location_id: Mapped[Optional[str]] = mapped_column(ForeignKey("locations.id"), index=True, nullable=True)
    village: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Education & work ───────────────────────────────────
    education_level: Mapped[EducationLevel] = mapped_column(
        Enum(EducationLevel, native_enum=False, length=24), default=EducationLevel.NONE, nullable=False, index=True
    )
    education_notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_occupation: Mapped[Optional[str]] = mapped_column(String(120), index=True, nullable=True)
    family_occupation: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    monthly_income: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Aspirations & constraints (JSON arrays of strings) ──
    skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    interests: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    constraints: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    mobility: Mapped[Mobility] = mapped_column(
        Enum(Mobility, native_enum=False, length=16), default=Mobility.LOCAL, nullable=False
    )
    employment_preference: Mapped[EmploymentPreference] = mapped_column(
        Enum(EmploymentPreference, native_enum=False, length=24),
        default=EmploymentPreference.ANY,
        nullable=False,
    )
    has_smartphone: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_bank_account: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Pipeline state ─────────────────────────────────────
    status: Mapped[BeneficiaryStatus] = mapped_column(
        Enum(BeneficiaryStatus, native_enum=False, length=24),
        default=BeneficiaryStatus.REGISTERED,
        nullable=False,
        index=True,
    )
    # Structured profile produced by the AI interview extraction step
    ai_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Who registered / owns this record
    created_by_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_account_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)

    location = relationship("Location", lazy="joined")
    interviews = relationship("Interview", back_populates="beneficiary", cascade="all, delete-orphan")
    recommendations = relationship(
        "Recommendation", back_populates="beneficiary", cascade="all, delete-orphan"
    )
    applications = relationship("Application", back_populates="beneficiary", cascade="all, delete-orphan")
    outcomes = relationship("Outcome", back_populates="beneficiary", cascade="all, delete-orphan")
