import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc
from app.models.event import Event
from app.models.features import AuditLog, Notification
from app.models.outbox import OutboxMessage
from app.models.registration import Registration
from app.models.user import User


def audit(
    db: Session,
    actor: User,
    action: str,
    target_id: uuid.UUID,
    details: dict[str, object] | None = None,
) -> None:
    db.add(AuditLog(actor_id=actor.id, action=action, target_id=target_id, details=details or {}))


def notify(
    db: Session,
    user: User,
    event: Event,
    topic: str,
    dedupe_key: str | None = None,
    email: bool = True,
) -> None:
    if dedupe_key and db.scalar(
        select(Notification.id).where(Notification.dedupe_key == dedupe_key)
    ):
        return
    db.add(
        Notification(
            user_id=user.id,
            event_id=event.id,
            topic=topic,
            message=f"{topic.replace('.', ' ').replace('_', ' ').capitalize()}: {event.title}",
            dedupe_key=dedupe_key,
        )
    )
    if email:
        db.add(
            OutboxMessage(
                topic=topic,
                dedupe_key=dedupe_key,
                payload={
                    "user_id": str(user.id),
                    "event_id": str(event.id),
                    "email": user.email,
                    "name": user.name,
                    "event_title": event.title,
                    "starts_at": event.starts_at.isoformat(),
                    "ends_at": event.ends_at.isoformat(),
                    "location": event.location,
                    "timezone": event.timezone,
                },
            )
        )


def schedule_reminder(db: Session, registration: Registration, event: Event) -> None:
    due = as_utc(event.starts_at) - timedelta(hours=24)
    if due <= datetime.now(UTC):
        return
    db.flush()
    queue_time = as_utc(registration.queued_at).isoformat()
    key = f"reminder:{registration.id}:{event.revision}:{queue_time}"
    if db.scalar(select(OutboxMessage.id).where(OutboxMessage.dedupe_key == key)):
        return
    db.add(
        OutboxMessage(
            topic="event.reminder",
            dedupe_key=key,
            available_at=due,
            payload={
                "registration_id": str(registration.id),
                "revision": event.revision,
                "queued_at": queue_time,
                "event_id": str(event.id),
                "user_id": str(registration.attendee_id),
            },
        )
    )
