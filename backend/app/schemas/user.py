from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class UserCreateAdmin(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    phone: Optional[str] = None
    organisation: Optional[str] = None
    district: Optional[str] = None
    is_active: bool = True


class UserUpdateAdmin(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    phone: Optional[str] = None
    organisation: Optional[str] = None
    district: Optional[str] = None
    is_active: Optional[bool] = None
    is_email_verified: Optional[bool] = None


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    organisation: Optional[str] = None
    district: Optional[str] = None
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    model_config = {"from_attributes": True}
