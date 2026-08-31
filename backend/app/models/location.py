from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Location(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("state", "district", "block", name="uq_location_admin"),)

    state: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    block: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    population: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sc_population: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    literacy_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 2011-census style code, useful for GIS joins
    lgd_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
