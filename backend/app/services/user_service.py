import uuid

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.db.repository import user as user_repo
from app.models.user import User, UserRole


def list_users(db: Session, limit: int, offset: int) -> tuple[list[User], int]:
    return user_repo.list_users(db, limit, offset)


def change_role(db: Session, user_id: uuid.UUID, role: UserRole, actor: User) -> User:
    user = user_repo.by_id(db, user_id)
    if not user:
        raise NotFoundError("user")
    if user.id == actor.id and role != UserRole.ADMIN:
        raise ConflictError("cannot_demote_self", "Administrators cannot demote themselves")
    user.role = role
    db.commit()
    db.refresh(user)
    return user
