import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.user import User, UserRole
from app.services.auth_service import revoke_all
from app.services.notification_service import audit


def list_users(db: Session, limit: int, offset: int, **filters: object) -> tuple[list[User], int]:
    statement = select(User)
    if filters.get("q"):
        term = str(filters["q"])
        statement = statement.where(
            or_(
                User.email.icontains(term, autoescape=True),
                User.name.icontains(term, autoescape=True),
            )
        )
    if filters.get("role"):
        statement = statement.where(User.role == filters["role"])
    if filters.get("is_active") is not None:
        statement = statement.where(User.is_active == filters["is_active"])
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    return list(
        db.scalars(statement.order_by(User.created_at, User.id).limit(limit).offset(offset))
    ), total


def change_role(db: Session, user_id: uuid.UUID, role: UserRole, actor: User) -> User:
    lock_admins(db)
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        raise NotFoundError("user")
    if user.id == actor.id and role != UserRole.ADMIN:
        raise ConflictError("cannot_demote_self", "Administrators cannot demote themselves")
    if user.role == UserRole.ADMIN and role != UserRole.ADMIN:
        protect_last_admin(db, user)
    user.role = role
    audit(db, actor, "user.role_changed", user.id, {"role": role.value})
    db.commit()
    db.refresh(user)
    return user


def lock_admins(db: Session) -> None:
    # Serializes changes even when different administrator rows are targeted.
    from sqlalchemy import text

    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(80173521)"))


def protect_last_admin(db: Session, user: User) -> None:
    count = (
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == UserRole.ADMIN, User.is_active.is_(True))
        )
        or 0
    )
    if user.role == UserRole.ADMIN and user.is_active and count <= 1:
        raise ConflictError("last_admin", "The last active administrator cannot be removed")


def change_status(db: Session, user_id: uuid.UUID, active: bool, actor: User) -> User:
    lock_admins(db)
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        raise NotFoundError("user")
    if not active:
        if user.id == actor.id:
            raise ConflictError("cannot_suspend_self", "Administrators cannot suspend themselves")
        protect_last_admin(db, user)
        revoke_all(db, user)
    user.is_active = active
    audit(db, actor, "user.status_changed", user.id, {"is_active": active})
    db.commit()
    return user
