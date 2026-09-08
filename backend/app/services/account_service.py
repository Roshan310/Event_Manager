import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.security import (
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    token_cipher,
    verify_password,
)
from app.core.time import as_utc
from app.models.features import ActionToken
from app.models.outbox import OutboxMessage
from app.models.user import User
from app.services.auth_service import revoke_all


def locked_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not user or not user.is_active:
        raise DomainError("account_inactive", "This account is unavailable", 403)
    return user


def require_verified(user: User) -> None:
    if not user.email_verified:
        raise DomainError("email_not_verified", "Verify your email before continuing", 403)


def request_token(db: Session, email: str, purpose: str, *, commit: bool = True) -> None:
    user = db.scalar(select(User).where(User.email == email.strip().casefold()).with_for_update())
    if not user or not user.is_active or (purpose == "verify" and user.email_verified):
        return
    now = datetime.now(UTC)
    db.execute(
        update(ActionToken)
        .where(
            ActionToken.user_id == user.id,
            ActionToken.purpose == purpose,
            ActionToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    raw, hashed = new_refresh_token()
    expires = now + timedelta(minutes=30 if purpose == "reset" else 1440)
    token = ActionToken(user_id=user.id, token_hash=hashed, purpose=purpose, expires_at=expires)
    db.add(token)
    db.flush()
    db.add(
        OutboxMessage(
            topic=f"account.{purpose}",
            payload={
                "email": user.email,
                "name": user.name,
                "action_id": str(token.id),
                "encrypted_token": token_cipher().encrypt(raw.encode()).decode(),
            },
        )
    )
    if commit:
        db.commit()


def consume_token(db: Session, raw: str, purpose: str, password: str | None = None) -> None:
    token = db.scalar(select(ActionToken).where(ActionToken.token_hash == hash_refresh_token(raw)))
    if not token:
        raise DomainError("invalid_action_token", "Token is invalid or expired", 400)
    user = locked_user(db, token.user_id)
    db.refresh(token, with_for_update=True)
    if token.purpose != purpose or token.used_at or as_utc(token.expires_at) <= datetime.now(UTC):
        raise DomainError("invalid_action_token", "Token is invalid or expired", 400)
    token.used_at = datetime.now(UTC)
    if purpose == "verify":
        user.email_verified = True
    else:
        assert password is not None
        user.password_hash = hash_password(password)
        revoke_all(db, user)
        db.execute(
            update(ActionToken)
            .where(
                ActionToken.user_id == user.id,
                ActionToken.purpose == "reset",
                ActionToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )
    db.commit()


def change_password(db: Session, actor: User, current: str, password: str) -> None:
    user = locked_user(db, actor.id)
    if not verify_password(current, user.password_hash):
        raise DomainError("invalid_credentials", "Current password is incorrect", 401)
    user.password_hash = hash_password(password)
    revoke_all(db, user)
    db.execute(
        update(ActionToken)
        .where(
            ActionToken.user_id == user.id,
            ActionToken.purpose == "reset",
            ActionToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )
    db.commit()


def logout_all(db: Session, actor: User) -> None:
    revoke_all(db, locked_user(db, actor.id))
    db.commit()


def update_profile(db: Session, actor: User, name: str) -> User:
    user = locked_user(db, actor.id)
    user.name = " ".join(name.split())
    if len(user.name) < 2:
        raise DomainError("invalid_name", "Name must contain at least two characters", 422)
    db.commit()
    return user
