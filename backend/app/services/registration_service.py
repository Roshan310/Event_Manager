import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.time import as_utc
from app.db.repository import event as event_repo
from app.db.repository import outbox as outbox_repo
from app.db.repository import registration as registration_repo
from app.models.event import EventStatus
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User, UserRole


def _email_payload(user: User, event_title: str) -> dict[str, object]:
    return {"email": user.email, "name": user.name, "event_title": event_title}


def register(db: Session, event_id: uuid.UUID, actor: User) -> Registration:
    if actor.role != UserRole.ATTENDEE:
        raise ForbiddenError("Only attendee accounts can register for events")
    event = event_repo.by_id(db, event_id, for_update=True)
    if not event:
        raise NotFoundError("event")
    now = datetime.now(UTC)
    if event.status != EventStatus.PUBLISHED or as_utc(event.ends_at) <= now:
        raise ConflictError("registration_closed", "Registration is not open for this event")
    existing = registration_repo.by_attendee_event(db, event_id, actor.id, for_update=True)
    if existing and existing.status != RegistrationStatus.CANCELLED:
        raise ConflictError("already_registered", "You already have an active registration")
    status = (
        RegistrationStatus.CONFIRMED
        if registration_repo.confirmed_count(db, event_id) < event.capacity
        else RegistrationStatus.WAITLISTED
    )
    if existing:
        existing.status, existing.cancelled_at, existing.created_at = status, None, now
        registration = existing
    else:
        registration = Registration(event_id=event_id, attendee_id=actor.id, status=status)
        db.add(registration)
    topic = (
        "registration.confirmed"
        if status == RegistrationStatus.CONFIRMED
        else "registration.waitlisted"
    )
    outbox_repo.enqueue(db, topic, _email_payload(actor, event.title))
    db.commit()
    db.refresh(registration)
    return registration


def cancel(db: Session, event_id: uuid.UUID, actor: User) -> None:
    event = event_repo.by_id(db, event_id, for_update=True)
    if not event:
        raise NotFoundError("event")
    registration = registration_repo.by_attendee_event(db, event_id, actor.id, for_update=True)
    if not registration or registration.status == RegistrationStatus.CANCELLED:
        raise NotFoundError("registration")
    was_confirmed = registration.status == RegistrationStatus.CONFIRMED
    registration.status = RegistrationStatus.CANCELLED
    registration.cancelled_at = datetime.now(UTC)
    outbox_repo.enqueue(db, "registration.cancelled", _email_payload(actor, event.title))
    if was_confirmed and event.status == EventStatus.PUBLISHED:
        promoted = registration_repo.next_waitlisted(db, event_id)
        if promoted:
            promoted.status = RegistrationStatus.CONFIRMED
            outbox_repo.enqueue(
                db, "registration.promoted", _email_payload(promoted.attendee, event.title)
            )
    db.commit()


def list_mine(db: Session, actor: User, limit: int, offset: int) -> tuple[list[Registration], int]:
    return registration_repo.list_for_attendee(db, actor.id, limit, offset)


def roster(
    db: Session, event_id: uuid.UUID, actor: User, limit: int, offset: int
) -> tuple[list[Registration], int]:
    event = event_repo.by_id(db, event_id)
    if not event:
        raise NotFoundError("event")
    if actor.role != UserRole.ADMIN and event.organizer_id != actor.id:
        raise ForbiddenError()
    return registration_repo.list_roster(db, event_id, limit, offset)
