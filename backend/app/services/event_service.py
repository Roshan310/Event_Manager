import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, DomainError, ForbiddenError, NotFoundError
from app.core.time import as_utc
from app.db.repository import event as event_repo
from app.db.repository import outbox as outbox_repo
from app.db.repository import registration as registration_repo
from app.models.event import Event, EventStatus
from app.models.registration import RegistrationStatus
from app.models.user import User, UserRole
from app.schemas.event import EventCreate, EventUpdate


def _can_manage(actor: User, event: Event) -> bool:
    return (
        actor.role == UserRole.ADMIN
        or actor.role == UserRole.ORGANIZER
        and actor.id == event.organizer_id
    )


def serialize(db: Session, event: Event) -> dict[str, object]:
    confirmed = event_repo.confirmed_count(db, event.id)
    status = (
        "completed"
        if event.status == EventStatus.PUBLISHED and as_utc(event.ends_at) <= datetime.now(UTC)
        else event.status.value
    )
    return {
        "id": event.id,
        "organizer_id": event.organizer_id,
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "timezone": event.timezone,
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "capacity": event.capacity,
        "status": status,
        "confirmed_count": confirmed,
        "available_seats": max(event.capacity - confirmed, 0),
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }


def public_list(db: Session, limit: int, offset: int) -> tuple[list[dict[str, object]], int]:
    events, total = event_repo.list_public(db, datetime.now(UTC), limit, offset)
    return [serialize(db, event) for event in events], total


def public_get(db: Session, event_id: uuid.UUID) -> dict[str, object]:
    event = event_repo.by_id(db, event_id)
    if not event or event.status != EventStatus.PUBLISHED:
        raise NotFoundError("event")
    return serialize(db, event)


def owned_list(
    db: Session, actor: User, limit: int, offset: int
) -> tuple[list[dict[str, object]], int]:
    if actor.role == UserRole.ADMIN:
        events, total = event_repo.list_all(db, limit, offset)
    else:
        events, total = event_repo.list_owned(db, actor.id, limit, offset)
    return [serialize(db, event) for event in events], total


def managed_get(db: Session, event_id: uuid.UUID, actor: User) -> dict[str, object]:
    event = event_repo.by_id(db, event_id)
    if not event:
        raise NotFoundError("event")
    if not _can_manage(actor, event):
        raise ForbiddenError()
    return serialize(db, event)


def create(db: Session, request: EventCreate, actor: User) -> dict[str, object]:
    event = Event(organizer_id=actor.id, status=EventStatus.DRAFT, **request.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return serialize(db, event)


def update(
    db: Session, event_id: uuid.UUID, request: EventUpdate, actor: User
) -> dict[str, object]:
    event = event_repo.by_id(db, event_id, for_update=True)
    if not event:
        raise NotFoundError("event")
    if not _can_manage(actor, event):
        raise ForbiddenError()
    if event.status == EventStatus.CANCELLED:
        raise ConflictError("event_cancelled", "Cancelled events cannot be edited")
    values = request.model_dump(exclude_unset=True)
    starts_at = values.get("starts_at", event.starts_at)
    ends_at = values.get("ends_at", event.ends_at)
    if ends_at <= starts_at:
        raise DomainError("invalid_schedule", "ends_at must be after starts_at")
    if "capacity" in values and values["capacity"] < registration_repo.confirmed_count(
        db, event.id
    ):
        raise ConflictError(
            "capacity_below_confirmed", "Capacity cannot be lower than confirmed registrations"
        )
    if event.status == EventStatus.PUBLISHED and as_utc(starts_at) <= datetime.now(UTC):
        raise ConflictError("event_started", "An event that has started cannot be edited")
    for key, value in values.items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return serialize(db, event)


def publish(db: Session, event_id: uuid.UUID, actor: User) -> dict[str, object]:
    event = event_repo.by_id(db, event_id, for_update=True)
    if not event:
        raise NotFoundError("event")
    if not _can_manage(actor, event):
        raise ForbiddenError()
    if event.status != EventStatus.DRAFT:
        raise ConflictError("invalid_event_transition", "Only draft events can be published")
    if as_utc(event.starts_at) <= datetime.now(UTC):
        raise DomainError("event_start_in_past", "A published event must start in the future")
    event.status = EventStatus.PUBLISHED
    db.commit()
    db.refresh(event)
    return serialize(db, event)


def cancel(db: Session, event_id: uuid.UUID, actor: User) -> dict[str, object]:
    event = event_repo.by_id(db, event_id, for_update=True)
    if not event:
        raise NotFoundError("event")
    if not _can_manage(actor, event):
        raise ForbiddenError()
    if event.status != EventStatus.PUBLISHED:
        raise ConflictError("invalid_event_transition", "Only published events can be cancelled")
    event.status = EventStatus.CANCELLED
    rows, _ = registration_repo.list_roster(db, event.id, 1000000, 0)
    for registration in rows:
        outbox_repo.enqueue(
            db,
            "event.cancelled",
            {
                "email": registration.attendee.email,
                "name": registration.attendee.name,
                "event_title": event.title,
            },
        )
        registration.status = RegistrationStatus.CANCELLED
        registration.cancelled_at = datetime.now(UTC)
    db.commit()
    db.refresh(event)
    return serialize(db, event)


def delete_draft(db: Session, event_id: uuid.UUID, actor: User) -> None:
    event = event_repo.by_id(db, event_id, for_update=True)
    if not event:
        raise NotFoundError("event")
    if not _can_manage(actor, event):
        raise ForbiddenError()
    if event.status != EventStatus.DRAFT:
        raise ConflictError("event_not_draft", "Only draft events can be deleted")
    db.delete(event)
    db.commit()
