from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import JSON, Boolean, Date, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import TrainingStatus


class TrainingProvider(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "training_providers"

    name: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(40), default="pia", nullable=False)  # iti|pia|polytechnic|ngo|psu
    accreditation: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)  # NCVET / SSC
    rating: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)

    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    location_id: Mapped[Optional[str]] = mapped_column(ForeignKey("locations.id"), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # optional link to the managing user account (role = training_provider)
    manager_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)

    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    location = relationship("Location", lazy="joined")
    programs = relationship("TrainingProgram", back_populates="provider", cascade="all, delete-orphan")


class TrainingProgram(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "training_programs"

    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    provider_id: Mapped[str] = mapped_column(ForeignKey("training_providers.id"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True, nullable=False)

    nsqf_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="offline", nullable=False)  # offline|online|blended
    duration_hours: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    duration_weeks: Mapped[int] = mapped_column(Integer, default=12, nullable=False)

    total_seats: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    filled_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    fee: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 => fully funded under PM-AJAY
    stipend_monthly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_residential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    location_id: Mapped[Optional[str]] = mapped_column(ForeignKey("locations.id"), index=True, nullable=True)

    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    application_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    eligibility_min_education: Mapped[str] = mapped_column(String(24), default="none", nullable=False)
    eligibility_min_age: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    eligibility_max_age: Mapped[Optional[int]] = mapped_column(Integer, default=45, nullable=True)
    eligibility_notes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    status: Mapped[TrainingStatus] = mapped_column(
        Enum(TrainingStatus, native_enum=False, length=16), default=TrainingStatus.OPEN, nullable=False, index=True
    )
    certification_body: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    provider = relationship("TrainingProvider", back_populates="programs")
    skill = relationship("Skill", back_populates="training_programs", lazy="joined")
    location = relationship("Location", lazy="joined")
    applications = relationship("Application", back_populates="program", cascade="all, delete-orphan")

    @property
    def seats_available(self) -> int:
        return max(self.total_seats - self.filled_seats, 0)
