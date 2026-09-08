import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.time import as_utc
from app.db.repository import event as event_repo
from app.db.repository import registration as registration_repo
from app.models.event import Event, EventStatus
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User, UserRole
from app.services import event_service
from app.services.account_service import require_verified
from app.services.notification_service import audit, notify, schedule_reminder


def _email_payload(user: User, event_title: str) -> dict[str, object]:
    return {"email": user.email, "name": user.name, "event_title": event_title}


def register(db: Session, event_id: uuid.UUID, actor: User) -> Registration:
    require_verified(actor)
    event = event_repo.by_id(db, event_id, for_update=True)
    if not event:
        raise NotFoundError("event")
    now = datetime.now(UTC)
    if event.status != EventStatus.PUBLISHED or as_utc(event.starts_at) <= now:
        raise ConflictError("registration_closed", "Registration is not open for this event")
    existing = registration_repo.by_attendee_event(db, event_id, actor.id, for_update=True)
    if existing and existing.status != RegistrationStatus.CANCELLED:
        raise ConflictError("already_registered", "You already have an active registration")
    promote_waitlist(db, event)
    status = (
        RegistrationStatus.CONFIRMED
        if registration_repo.confirmed_count(db, event_id) < event.capacity
        else RegistrationStatus.WAITLISTED
    )
    if existing:
        existing.status, existing.cancelled_at, existing.queued_at = status, None, now
        existing.checked_in_at = None
        existing.checked_in_by = None
        registration = existing
    else:
        registration = Registration(
            event_id=event_id, attendee_id=actor.id, status=status, queued_at=now
        )
        db.add(registration)
    registration.ticket_nonce = (
        secrets.token_urlsafe(32) if status == RegistrationStatus.CONFIRMED else None
    )
    topic = (
        "registration.confirmed"
        if status == RegistrationStatus.CONFIRMED
        else "registration.waitlisted"
    )
    notify(db, actor, event, topic)
    db.flush()
    if status == RegistrationStatus.CONFIRMED:
        schedule_reminder(db, registration, event)
    db.commit()
    db.refresh(registration)
    return registration


def cancel(db: Session, event_id: uuid.UUID, actor: User) -> None:
    event = event_repo.by_id(db, event_id, for_update=True)
    if not event:
        raise NotFoundError("event")
    if as_utc(event.starts_at) <= datetime.now(UTC):
        raise ConflictError("registration_closed", "Cancellation closes when the event starts")
    registration = registration_repo.by_attendee_event(db, event_id, actor.id, for_update=True)
    if not registration or registration.status == RegistrationStatus.CANCELLED:
        raise NotFoundError("registration")
    was_confirmed = registration.status == RegistrationStatus.CONFIRMED
    registration.status = RegistrationStatus.CANCELLED
    registration.cancelled_at = datetime.now(UTC)
    registration.ticket_nonce = None
    notify(db, actor, event, "registration.cancelled")
    db.flush()
    if was_confirmed and event.status == EventStatus.PUBLISHED:
        promote_waitlist(db, event)
    db.commit()


def list_mine(
    db: Session, actor: User, limit: int, offset: int, **filters: object
) -> tuple[list[dict[str, object]], int]:
    rows, total = registration_repo.list_for_attendee(db, actor.id, limit, offset, **filters)
    events = event_service.serialize_many(db, [row.event for row in rows])
    return [
        dict(serialize_registration(db, row), event=event)
        for row, event in zip(rows, events, strict=True)
    ], total


def roster(
    db: Session, event_id: uuid.UUID, actor: User, limit: int, offset: int, **filters: object
) -> tuple[list[Registration], int]:
    event = event_repo.by_id(db, event_id)
    if not event:
        raise NotFoundError("event")
    if actor.role != UserRole.ADMIN and event.organizer_id != actor.id:
        raise ForbiddenError()
    return registration_repo.list_roster(db, event_id, limit, offset, **filters)


def promote_waitlist(db: Session, event: Event) -> None:
    if event.status != EventStatus.PUBLISHED or as_utc(event.starts_at) <= datetime.now(UTC):
        return
    db.flush()
    available = event.capacity - registration_repo.confirmed_count(db, event.id)
    if available <= 0:
        return
    waiting = list(
        db.scalars(
            select(Registration)
            .join(User, User.id == Registration.attendee_id)
            .where(
                Registration.event_id == event.id,
                Registration.status == RegistrationStatus.WAITLISTED,
                User.is_active.is_(True),
                User.email_verified.is_(True),
            )
            .order_by(Registration.queued_at, Registration.id)
            .limit(available)
            .with_for_update(of=Registration)
        )
    )
    for row in waiting:
        row.status = RegistrationStatus.CONFIRMED
        row.ticket_nonce = secrets.token_urlsafe(32)
        notify(db, row.attendee, event, "registration.promoted")
        schedule_reminder(db, row, event)
    db.flush()


def serialize_registration(db: Session, row: Registration) -> dict[str, object]:
    from app.schemas.registration import RegistrationOut

    result = RegistrationOut.model_validate(row).model_dump()
    if row.status == RegistrationStatus.WAITLISTED:
        queue = list(
            db.scalars(
                select(Registration.id)
                .where(
                    Registration.event_id == row.event_id,
                    Registration.status == RegistrationStatus.WAITLISTED,
                )
                .order_by(Registration.queued_at, Registration.id)
            )
        )
        result["waitlist_position"] = queue.index(row.id) + 1
    return result


def mine_for_event(db: Session, event_id: uuid.UUID, actor: User) -> dict[str, object]:
    row = registration_repo.by_attendee_event(db, event_id, actor.id)
    if not row:
        raise NotFoundError("registration")
    return serialize_registration(db, row)


def remove(
    db: Session, event_id: uuid.UUID, registration_id: uuid.UUID, actor: User, reason: str
) -> None:
    event = event_repo.by_id(db, event_id, for_update=True)
    if not event:
        raise NotFoundError("event")
    if not event_service._can_manage(actor, event):
        raise ForbiddenError()
    if as_utc(event.starts_at) <= datetime.now(UTC):
        raise ConflictError("registration_closed", "Registration changes close at event start")
    row = db.get(Registration, registration_id)
    if not row or row.event_id != event_id:
        raise NotFoundError("registration")
    if row.status == RegistrationStatus.CANCELLED:
        return
    row.status = RegistrationStatus.CANCELLED
    row.cancelled_at = datetime.now(UTC)
    row.ticket_nonce = None
    notify(db, row.attendee, event, "registration.cancelled")
    audit(db, actor, "registration.removed", row.id, {"reason": reason})
    db.flush()
    promote_waitlist(db, event)
    db.commit()
