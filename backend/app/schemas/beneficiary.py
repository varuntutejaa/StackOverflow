from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    BeneficiaryStatus,
    EducationLevel,
    EmploymentPreference,
    Gender,
    Language,
    Mobility,
)
from app.schemas.location import LocationOut


class BeneficiaryBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    age: Optional[int] = Field(default=None, ge=10, le=100)
    gender: Gender = Gender.UNDISCLOSED
    phone: Optional[str] = Field(default=None, max_length=20)
    preferred_language: Language = Language.HINDI

    social_category: str = "SC"
    pmajay_id: Optional[str] = None
    household_id: Optional[str] = None

    location_id: Optional[str] = None
    village: Optional[str] = None
    address: Optional[str] = None

    education_level: EducationLevel = EducationLevel.NONE
    education_notes: Optional[str] = None
    current_occupation: Optional[str] = None
    family_occupation: Optional[str] = None
    monthly_income: Optional[int] = Field(default=None, ge=0)

    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)

    mobility: Mobility = Mobility.LOCAL
    employment_preference: EmploymentPreference = EmploymentPreference.ANY
    has_smartphone: bool = False
    has_bank_account: bool = True


class BeneficiaryCreate(BeneficiaryBase):
    is_demo: bool = False


class BeneficiaryUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Gender] = None
    phone: Optional[str] = None
    preferred_language: Optional[Language] = None
    location_id: Optional[str] = None
    village: Optional[str] = None
    address: Optional[str] = None
    education_level: Optional[EducationLevel] = None
    education_notes: Optional[str] = None
    current_occupation: Optional[str] = None
    family_occupation: Optional[str] = None
    monthly_income: Optional[int] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    mobility: Optional[Mobility] = None
    employment_preference: Optional[EmploymentPreference] = None
    has_smartphone: Optional[bool] = None
    has_bank_account: Optional[bool] = None
    status: Optional[BeneficiaryStatus] = None


class BeneficiaryOut(BeneficiaryBase):
    id: str
    status: BeneficiaryStatus
    ai_profile: Optional[dict] = None
    is_demo: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    location: Optional[LocationOut] = None

    model_config = {"from_attributes": True}


class BeneficiaryListItem(BaseModel):
    id: str
    full_name: str
    age: Optional[int]
    gender: Gender
    preferred_language: Language
    education_level: EducationLevel
    current_occupation: Optional[str]
    status: BeneficiaryStatus
    village: Optional[str]
    is_demo: bool
    created_at: datetime
    district: Optional[str] = None

    model_config = {"from_attributes": True}


class BeneficiaryFilter(BaseModel):
    district: Optional[str] = None
    education_level: Optional[EducationLevel] = None
    occupation: Optional[str] = None
    skill: Optional[str] = None
    status: Optional[BeneficiaryStatus] = None
    language: Optional[Language] = None
    is_demo: Optional[bool] = None
    include_archived: bool = False
