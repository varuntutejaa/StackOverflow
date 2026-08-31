from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class LocationBase(BaseModel):
    state: str
    district: str
    block: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None
    sc_population: Optional[int] = None
    literacy_rate: Optional[float] = None
    lgd_code: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    block: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None
    sc_population: Optional[int] = None
    literacy_rate: Optional[float] = None


class LocationOut(LocationBase):
    id: str
    model_config = {"from_attributes": True}
