"""Shared FastAPI dependencies: DB session, current user, RBAC guards."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_prefix}/auth/login", auto_error=False
)

CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise CREDENTIALS_EXC
    try:
        payload = decode_token(token, expected_type="access")
    except ValueError:
        raise CREDENTIALS_EXC
    user_id = payload.get("sub")
    if not user_id:
        raise CREDENTIALS_EXC
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise CREDENTIALS_EXC
    return user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = decode_token(token, expected_type="access")
        return db.get(User, payload.get("sub"))
    except ValueError:
        return None


class RoleChecker:
    def __init__(self, *roles: UserRole):
        self.roles: set[UserRole] = set(roles)

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if self.roles and user.role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(r.value for r in self.roles)}",
            )
        return user


# Convenience guards
require_admin = RoleChecker(UserRole.ADMIN)
require_staff = RoleChecker(UserRole.ADMIN, UserRole.GOV_OFFICER)
require_provider_staff = RoleChecker(UserRole.ADMIN, UserRole.GOV_OFFICER, UserRole.TRAINING_PROVIDER)
require_any = RoleChecker()  # any authenticated user


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
