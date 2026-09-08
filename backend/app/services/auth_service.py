import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, DomainError
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.core.time import as_utc
from app.db.repository import token as token_repo
from app.db.repository import user as user_repo
from app.models.token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse
from app.schemas.user import UserRegister


def _normalize_email(email: str) -> str:
    return email.strip().casefold()


def register(db: Session, request: UserRegister) -> User:
    user = User(
        name=request.name,
        email=_normalize_email(str(request.email)),
        password_hash=hash_password(request.password),
        role=UserRole.ATTENDEE,
    )
    db.add(user)
    try:
        db.flush()
        from app.services.account_service import request_token

        request_token(db, user.email, "verify", commit=False)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("email_exists", "An account with this email already exists") from exc
    db.refresh(user)
    return user


def _issue_pair(db: Session, user: User, family_id: uuid.UUID | None = None) -> TokenResponse:
    family_id = family_id or uuid.uuid4()
    access_token, expires_in = create_access_token(user.id, family_id, user.auth_version)
    raw_refresh, token_hash = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expires_days),
        )
    )
    db.flush()
    return TokenResponse(
        access_token=access_token, refresh_token=raw_refresh, expires_in=expires_in, user=user
    )


def login(db: Session, email: str, password: str) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == _normalize_email(email)).with_for_update())
    valid = verify_password(password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if not user or not valid:
        raise DomainError("invalid_credentials", "Email or password is incorrect", 401)
    if not user.is_active:
        raise DomainError("account_inactive", "This account is inactive", 403)
    response = _issue_pair(db, user)
    db.commit()
    return response


def refresh(db: Session, raw_token: str) -> TokenResponse:
    now = datetime.now(UTC)
    lock_token_user(db, raw_token)
    record = token_repo.by_hash(db, hash_refresh_token(raw_token), for_update=True)
    if not record:
        raise DomainError("invalid_refresh_token", "Refresh token is invalid", 401)
    if record.revoked_at is not None:
        token_repo.revoke_family(db, record.family_id, now)
        db.commit()
        raise DomainError(
            "refresh_token_reused", "Refresh token reuse detected; session revoked", 401
        )
    if as_utc(record.expires_at) <= now:
        record.revoked_at = now
        db.commit()
        raise DomainError("refresh_token_expired", "Refresh token has expired", 401)
    user = user_repo.by_id(db, record.user_id)
    if not user or not user.is_active:
        raise DomainError("account_inactive", "This account is unavailable", 403)
    response = _issue_pair(db, user, record.family_id)
    record.revoked_at = now
    record.replaced_by_hash = hash_refresh_token(response.refresh_token)
    db.commit()
    return response


def logout(db: Session, raw_token: str) -> None:
    lock_token_user(db, raw_token)
    record = token_repo.by_hash(db, hash_refresh_token(raw_token), for_update=True)
    if record:
        token_repo.revoke_family(db, record.family_id, datetime.now(UTC))
        db.commit()


DUMMY_PASSWORD_HASH = hash_password("constant-unusable-timing-padding-password")


def lock_token_user(db: Session, raw_token: str) -> None:
    user_id = db.scalar(
        select(RefreshToken.user_id).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    if user_id:
        db.scalar(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )


def revoke_all(db: Session, user: User) -> None:
    user.auth_version += 1
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
