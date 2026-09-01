from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_current_user
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_generic_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AccessToken,
    ChangePasswordRequest,
    DevTokenHint,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SupabaseLoginRequest,
    TokenPair,
    UpdateProfileRequest,
    UserPublic,
    VerifyEmailRequest,
)
from app.schemas.common import Message
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger("auth")


def _token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserPublic.model_validate(user),
    )


def _dev_link(path: str, token: str) -> str | None:
    if settings.is_production:
        return None
    origin = settings.cors_origins[0] if settings.cors_origins else "http://localhost:3000"
    return f"{origin}{path}?token={token}"


def _verify_supabase_user(access_token: str) -> dict:
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Supabase Auth is not configured")

    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
            headers={
                "apikey": settings.supabase_anon_key,
                "authorization": f"Bearer {access_token}",
            },
            timeout=10,
        )
    except httpx.HTTPError as exc:
        log.warning("supabase_auth_unreachable", error=str(exc))
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Supabase Auth is unavailable") from exc

    if response.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Supabase session")
    return response.json()


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    exists = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        organisation=payload.organisation,
        district=payload.district,
        hashed_password=hash_password(payload.password),
        is_email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    audit.record(db, action="auth.register", actor=user, entity_type="user", entity_id=user.id, ip_address=client_ip(request))

    token = create_generic_token(user.id, "verify_email", 60 * 24)
    log.info("verification_token_issued", email=user.email, token=token if not settings.is_production else "<hidden>")
    return _token_pair(user)


@router.post("/login", response_model=TokenPair)
def login_json(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        audit.record(db, action="auth.login", status="failure", entity_type="user", ip_address=client_ip(request), changes={"email": payload.email})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    audit.record(db, action="auth.login", actor=user, entity_type="user", entity_id=user.id, ip_address=client_ip(request))
    return _token_pair(user)


@router.post("/supabase", response_model=TokenPair)
def login_supabase(payload: SupabaseLoginRequest, request: Request, db: Session = Depends(get_db)):
    supabase_user = _verify_supabase_user(payload.access_token)
    email = (supabase_user.get("email") or "").lower()
    supabase_uid = supabase_user.get("id")
    if not email or not supabase_uid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Supabase account is missing email or subject")

    user = db.execute(select(User).where(User.supabase_uid == supabase_uid)).scalar_one_or_none()
    if not user:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    metadata = supabase_user.get("user_metadata") or {}
    full_name = metadata.get("full_name") or metadata.get("name") or email.split("@")[0]
    avatar_provider = supabase_user.get("app_metadata", {}).get("provider")

    if user:
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
        user.supabase_uid = user.supabase_uid or supabase_uid
        user.is_email_verified = True
        if not user.full_name:
            user.full_name = full_name
    else:
        user = User(
            email=email,
            full_name=full_name,
            role=payload.role,
            hashed_password=None,
            supabase_uid=supabase_uid,
            is_email_verified=True,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    audit.record(
        db,
        action="auth.supabase_login",
        actor=user,
        entity_type="user",
        entity_id=user.id,
        ip_address=client_ip(request),
        changes={"provider": avatar_provider or "supabase"},
    )
    return _token_pair(user)


@router.post("/token", response_model=AccessToken, include_in_schema=False)
def login_oauth_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password flow — powers the 'Authorize' button in Swagger UI."""
    user = db.execute(select(User).where(User.email == form.username.lower())).scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return AccessToken(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=AccessToken)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Shared by the dashboard and the Android app — see `AccessToken`."""
    try:
        data = decode_token(payload.refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))
    user = db.get(User, data.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return AccessToken(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=settings.access_token_expire_minutes * 60,
        # Rotated so the app's stored refresh token never expires underneath it;
        # the dashboard keeps its own and ignores this field.
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", response_model=Message)
def logout(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Stateless JWT — client discards tokens. We record the event for audit.
    audit.record(db, action="auth.logout", actor=user, entity_type="user", entity_id=user.id, ip_address=client_ip(request))
    return Message(detail="Logged out")


@router.post("/forgot-password", response_model=DevTokenHint)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    # Always return 200 to avoid account enumeration.
    if not user:
        return DevTokenHint(detail="If the account exists, a reset link has been sent.")
    token = create_generic_token(user.id, "reset_password", 30)
    log.info("password_reset_requested", email=user.email)
    return DevTokenHint(
        detail="If the account exists, a reset link has been sent.",
        token=token if not settings.is_production else None,
        verification_url=_dev_link("/reset-password", token),
    )


@router.post("/reset-password", response_model=Message)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        data = decode_token(payload.token, expected_type="reset_password")
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    user = db.get(User, data.get("sub"))
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    audit.record(db, action="auth.reset_password", actor=user, entity_type="user", entity_id=user.id)
    return Message(detail="Password updated. You can now sign in.")


@router.post("/verify-email", response_model=Message)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    try:
        data = decode_token(payload.token, expected_type="verify_email")
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    user = db.get(User, data.get("sub"))
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token")
    user.is_email_verified = True
    db.commit()
    return Message(detail="Email verified")


@router.post("/resend-verification", response_model=DevTokenHint)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if not user:
        return DevTokenHint(detail="If the account exists, a verification link has been sent.")
    if user.is_email_verified:
        return DevTokenHint(detail="Email is already verified.")
    token = create_generic_token(user.id, "verify_email", 60 * 24)
    return DevTokenHint(
        detail="Verification link sent.",
        token=token if not settings.is_production else None,
        verification_url=_dev_link("/verify-email", token),
    )


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return UserPublic.model_validate(user)


@router.patch("/me", response_model=UserPublic)
def update_me(payload: UpdateProfileRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user)


@router.post("/change-password", response_model=Message)
def change_password(payload: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.hashed_password or not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    audit.record(db, action="auth.change_password", actor=user, entity_type="user", entity_id=user.id)
    return Message(detail="Password changed")
