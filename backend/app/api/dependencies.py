from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import DomainError, ForbiddenError
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.repository import user as user_repo
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise DomainError("not_authenticated", "Authentication is required", 401)
    user = user_repo.by_id(db, decode_access_token(credentials.credentials))
    if not user:
        raise DomainError("invalid_token", "Token user no longer exists", 401)
    if not user.is_active:
        raise DomainError("account_inactive", "This account is inactive", 403)
    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError()
        return user

    return dependency


admin_user = require_roles(UserRole.ADMIN)
event_manager = require_roles(UserRole.ADMIN, UserRole.ORGANIZER)
