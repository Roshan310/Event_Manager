import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import DomainError, ForbiddenError
from app.core.security import decode_access_claims
from app.db.database import get_db
from app.db.repository import user as user_repo
from app.models.token import RefreshToken
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise DomainError("not_authenticated", "Authentication is required", 401)
    claims = decode_access_claims(credentials.credentials)
    user = user_repo.by_id(db, uuid.UUID(claims["sub"]))
    if not user:
        raise DomainError("invalid_token", "Token user no longer exists", 401)
    if not user.is_active:
        raise DomainError("account_inactive", "This account is inactive", 403)
    active_session = db.scalar(
        select(RefreshToken.id)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.family_id == uuid.UUID(claims["sid"]),
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(UTC),
        )
        .limit(1)
    )
    if claims["ver"] != user.auth_version or not active_session:
        raise DomainError("session_revoked", "Session has been revoked", 401)
    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError()
        return user

    return dependency


admin_user = require_roles(UserRole.ADMIN)
event_manager = require_roles(UserRole.ADMIN, UserRole.ORGANIZER)
