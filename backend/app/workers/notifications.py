import logging
import signal
import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import token_cipher
from app.core.time import as_utc
from app.db.database import SessionLocal
from app.models.event import Event, EventStatus
from app.models.features import ActionToken, Notification, WorkerHeartbeat
from app.models.outbox import OutboxMessage
from app.models.registration import Registration, RegistrationStatus
from app.services.email_service import send_notification

logger = logging.getLogger(__name__)


def claim() -> tuple[uuid.UUID, uuid.UUID] | None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        message = db.scalar(
            select(OutboxMessage)
            .where(
                OutboxMessage.processed_at.is_(None),
                OutboxMessage.failed_at.is_(None),
                OutboxMessage.available_at <= now,
                or_(OutboxMessage.lease_until.is_(None), OutboxMessage.lease_until < now),
            )
            .order_by(OutboxMessage.available_at, OutboxMessage.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        heartbeat = insert(WorkerHeartbeat).values(name="notifications", seen_at=now)
        db.execute(
            heartbeat.on_conflict_do_update(
                index_elements=[WorkerHeartbeat.name], set_={"seen_at": now}
            )
        )
        result = None
        if message:
            message.claim_id = uuid.uuid4()
            message.lease_until = now + timedelta(seconds=settings.notification_lease_seconds)
            result = message.id, message.claim_id
        db.commit()
        return result


def prepare(db: Session, row: OutboxMessage) -> dict[str, Any] | None:
    payload: dict[str, Any] = dict(row.payload)
    if row.topic.startswith("account."):
        action = db.get(ActionToken, uuid.UUID(payload["action_id"]))
        if not action or action.used_at or as_utc(action.expires_at) <= datetime.now(UTC):
            return None
        payload["token"] = (
            token_cipher().decrypt(str(payload.pop("encrypted_token")).encode()).decode()
        )
        return payload
    if row.topic != "event.reminder":
        return payload
    event = db.scalar(
        select(Event).where(Event.id == uuid.UUID(payload["event_id"])).with_for_update()
    )
    registration = db.get(Registration, uuid.UUID(payload["registration_id"]))
    if (
        not event
        or not registration
        or (
            event.status != EventStatus.PUBLISHED
            or as_utc(event.starts_at) <= datetime.now(UTC)
            or event.revision != payload["revision"]
            or as_utc(registration.queued_at).isoformat() != payload["queued_at"]
            or registration.status != RegistrationStatus.CONFIRMED
            or not registration.attendee.is_active
        )
    ):
        return None
    if not db.scalar(select(Notification.id).where(Notification.dedupe_key == row.dedupe_key)):
        db.add(
            Notification(
                user_id=registration.attendee_id,
                event_id=event.id,
                topic=row.topic,
                message=f"Event reminder: {event.title}",
                dedupe_key=row.dedupe_key,
            )
        )
    if not registration.attendee.reminder_emails:
        return None
    return {
        "email": registration.attendee.email,
        "name": registration.attendee.name,
        "event_title": event.title,
        "starts_at": event.starts_at.isoformat(),
        "ends_at": event.ends_at.isoformat(),
        "location": event.location,
        "timezone": event.timezone,
    }


def deliver(message_id: uuid.UUID, claim_id: uuid.UUID) -> None:
    failure: str | None = None
    try:
        with SessionLocal() as db:
            row = db.get(OutboxMessage, message_id)
            if not row or row.claim_id != claim_id:
                return
            topic = row.topic
            payload = prepare(db, row)
            db.commit()
        # No database transaction or connection is held during SMTP delivery.
        if payload is not None:
            send_notification(topic, payload)
    except Exception as exc:
        failure = type(exc).__name__
        logger.warning("Notification delivery failed id=%s type=%s", message_id, failure)
    with SessionLocal() as db:
        row = db.scalar(
            select(OutboxMessage)
            .where(OutboxMessage.id == message_id, OutboxMessage.claim_id == claim_id)
            .with_for_update()
        )
        if not row:
            return
        row.attempts += 1
        now = datetime.now(UTC)
        if failure:
            row.last_error = failure
            if row.attempts >= settings.notification_max_attempts:
                row.failed_at = now
            else:
                row.available_at = now + timedelta(seconds=min(2**row.attempts * 30, 3600))
        else:
            row.processed_at = now
            row.last_error = None
        if row.topic.startswith("account.") and (row.processed_at or row.failed_at):
            row.payload = {}
        row.claim_id, row.lease_until = None, None
        db.commit()


def process_batch() -> int:
    processed = 0
    for _ in range(settings.notification_batch_size):
        claimed = claim()
        if claimed is None:
            break
        deliver(*claimed)
        processed += 1
    return processed


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    stopping = threading.Event()

    def stop(signum: int, frame: object) -> None:
        stopping.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logger.info("Notification worker started")
    while not stopping.is_set():
        try:
            if process_batch() == 0:
                stopping.wait(settings.notification_poll_seconds)
        except Exception as exc:
            logger.error("Worker database failure type=%s", type(exc).__name__)
            stopping.wait(min(30, settings.notification_poll_seconds * 5))


if __name__ == "__main__":
    main()
