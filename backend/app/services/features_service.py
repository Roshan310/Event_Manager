import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.time import as_utc
from app.models.event import Event, EventStatus
from app.models.features import AuditLog, Bookmark, Category, Notification, WorkerHeartbeat
from app.models.outbox import OutboxMessage
from app.models.user import User, UserRole
from app.services import event_service
from app.services.account_service import locked_user
from app.services.notification_service import audit


def categories(db: Session, all_categories: bool = False) -> list[Category]:
    statement = select(Category)
    if not all_categories:
        statement = statement.where(Category.is_active.is_(True))
    return list(db.scalars(statement.order_by(Category.name, Category.id)))


def save_category(
    db: Session, name: str, actor: User, category_id: uuid.UUID | None = None, active: bool = True
) -> Category:
    row = db.get(Category, category_id) if category_id else Category()
    if not row:
        raise NotFoundError("category")
    row.name, row.is_active = name, active
    db.add(row)
    try:
        db.flush()
        audit(db, actor, "category.updated", row.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("category_exists", "Category name already exists") from exc
    return row


def bookmark(db: Session, event_id: uuid.UUID, actor: User, remove: bool = False) -> None:
    locked_user(db, actor.id)
    if not remove:
        event_service.public_get(db, event_id)
    row = db.get(Bookmark, (actor.id, event_id))
    if remove and row:
        db.delete(row)
    elif not remove and not row:
        db.add(Bookmark(user_id=actor.id, event_id=event_id))
    db.commit()


def bookmarks(
    db: Session, actor: User, limit: int, offset: int
) -> tuple[list[dict[str, object]], int]:
    statement = (
        select(Event)
        .join(Bookmark)
        .where(Bookmark.user_id == actor.id, Event.status != EventStatus.DRAFT)
    )
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = list(
        db.scalars(
            statement.order_by(Bookmark.created_at.desc(), Event.id).limit(limit).offset(offset)
        )
    )
    return event_service.serialize_many(db, rows), total


def notifications(
    db: Session, actor: User, limit: int, offset: int, unread_only: bool
) -> tuple[list[Notification], int]:
    statement = select(Notification).where(Notification.user_id == actor.id)
    if unread_only:
        statement = statement.where(Notification.read_at.is_(None))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    return list(
        db.scalars(
            statement.order_by(Notification.created_at.desc(), Notification.id)
            .limit(limit)
            .offset(offset)
        )
    ), total


def read_notification(db: Session, actor: User, notification_id: uuid.UUID) -> Notification:
    row = db.scalar(
        select(Notification)
        .where(Notification.id == notification_id, Notification.user_id == actor.id)
        .with_for_update()
    )
    if not row:
        raise NotFoundError("notification")
    row.read_at = row.read_at or datetime.now(UTC)
    db.commit()
    return row


def read_all(db: Session, actor: User) -> None:
    db.execute(
        update(Notification)
        .where(Notification.user_id == actor.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    db.commit()


def preferences(db: Session, actor: User, reminder_emails: bool | None = None) -> dict[str, bool]:
    if reminder_emails is not None:
        actor = locked_user(db, actor.id)
        actor.reminder_emails = reminder_emails
        db.commit()
    return {"reminder_emails": actor.reminder_emails}


def transfer(
    db: Session, event_id: uuid.UUID, organizer_id: uuid.UUID, actor: User
) -> dict[str, object]:
    event = db.scalar(select(Event).where(Event.id == event_id).with_for_update())
    if not event:
        raise NotFoundError("event")
    owner = db.get(User, organizer_id)
    if not owner or not owner.is_active or owner.role not in (UserRole.ADMIN, UserRole.ORGANIZER):
        raise ConflictError("invalid_organizer", "Choose an active organizer or administrator")
    event.organizer_id = organizer_id
    audit(db, actor, "event.transferred", event.id, {"organizer_id": str(organizer_id)})
    db.commit()
    return event_service.serialize(db, event)


def audit_logs(
    db: Session, limit: int, offset: int, target_id: uuid.UUID | None = None
) -> tuple[list[AuditLog], int]:
    statement = select(AuditLog)
    if target_id:
        statement = statement.where(AuditLog.target_id == target_id)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    return list(
        db.scalars(
            statement.order_by(AuditLog.created_at.desc(), AuditLog.id).limit(limit).offset(offset)
        )
    ), total


def outbox(
    db: Session, limit: int, offset: int, failed_only: bool
) -> tuple[list[OutboxMessage], int]:
    statement = select(OutboxMessage)
    if failed_only:
        statement = statement.where(OutboxMessage.failed_at.is_not(None))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    return list(
        db.scalars(
            statement.order_by(OutboxMessage.created_at.desc(), OutboxMessage.id)
            .limit(limit)
            .offset(offset)
        )
    ), total


def retry(db: Session, message_id: uuid.UUID, actor: User) -> OutboxMessage:
    row = db.scalar(select(OutboxMessage).where(OutboxMessage.id == message_id).with_for_update())
    if not row:
        raise NotFoundError("outbox_message")
    if not row.failed_at or row.topic.startswith("account."):
        raise ConflictError("cannot_retry", "Only failed non-security notifications can be retried")
    row.failed_at, row.last_error, row.claim_id, row.lease_until = None, None, None, None
    row.attempts, row.available_at = 0, datetime.now(UTC)
    audit(db, actor, "notification.retried", row.id)
    db.commit()
    return row


def worker_status(db: Session) -> dict[str, Any]:
    row = db.get(WorkerHeartbeat, "notifications")
    pending = (
        db.scalar(
            select(func.count())
            .select_from(OutboxMessage)
            .where(OutboxMessage.processed_at.is_(None), OutboxMessage.failed_at.is_(None))
        )
        or 0
    )
    failed = (
        db.scalar(
            select(func.count())
            .select_from(OutboxMessage)
            .where(OutboxMessage.failed_at.is_not(None))
        )
        or 0
    )
    return {
        "last_seen_at": row.seen_at if row else None,
        "healthy": bool(row and as_utc(row.seen_at) > datetime.now(UTC) - timedelta(minutes=5)),
        "pending": pending,
        "failed": failed,
    }
