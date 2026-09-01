from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from app.models.enums import UserRole


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    organisation: Optional[str] = None
    district: Optional[str] = None
    is_active: bool
    is_email_verified: bool

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)
    phone: Optional[str] = Field(default=None, max_length=20)
    role: UserRole = UserRole.BENEFICIARY
    organisation: Optional[str] = None
    district: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SupabaseLoginRequest(BaseModel):
    access_token: str = Field(min_length=16)
    role: UserRole = UserRole.BENEFICIARY


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class RefreshRequest(BaseModel):
    # The dashboard posts `refresh_token`, the Android app posts `refreshToken`.
    # One path, one handler — so accept both spellings.
    model_config = ConfigDict(populate_by_name=True)

    refresh_token: str = Field(alias="refreshToken")


class AccessToken(BaseModel):
    """Refresh response, served to both clients at once.

    The dashboard reads `access_token`; the Android app reads `accessToken`,
    `refreshToken` and `expiresIn` and ignores keys it doesn't know. Emitting the
    union of both spellings keeps a single `/auth/refresh` honest for both.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

    @computed_field
    @property
    def accessToken(self) -> str:  # noqa: N802 — camelCase is the wire name
        return self.access_token

    @computed_field
    @property
    def refreshToken(self) -> Optional[str]:  # noqa: N802
        return self.refresh_token

    @computed_field
    @property
    def expiresIn(self) -> int:  # noqa: N802
        return self.expires_in


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    phone: Optional[str] = Field(default=None, max_length=20)
    organisation: Optional[str] = None
    district: Optional[str] = None


class DevTokenHint(BaseModel):
    """Returned by dev-only endpoints so the demo can complete the flow
    without an email provider configured."""

    detail: str
    token: Optional[str] = None
    verification_url: Optional[str] = None
