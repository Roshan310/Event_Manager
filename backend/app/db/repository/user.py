import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


def by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def list_users(db: Session, limit: int, offset: int) -> tuple[list[User], int]:
    total = db.scalar(select(func.count()).select_from(User)) or 0
    users = list(
        db.scalars(select(User).order_by(User.created_at, User.id).offset(offset).limit(limit))
    )
    return users, total
