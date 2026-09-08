import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, DomainError, ForbiddenError, NotFoundError
from app.core.time import as_utc
from app.db.repository import event as event_repo
from app.db.repository import registration as registration_repo
from app.models.event import Event, EventStatus
from app.models.features import Category
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User, UserRole
from app.schemas.event import EventCreate, EventUpdate
from app.services.account_service import require_verified
from app.services.notification_service import audit, notify, schedule_reminder


def _can_manage(actor: User, event: Event) -> bool:
    return (
        actor.role == UserRole.ADMIN
        or actor.role == UserRole.ORGANIZER
        and actor.id == event.organizer_id
    )


def serialize(db: Session, event: Event, confirmed: int | None = None) -> dict[str, object]:
    if confirmed is None:
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
        "category_id": event.category_id,
        "cover_url": (
            f"{settings.public_base_url}/api/v1/"
            f"{'organizer/' if event.status == EventStatus.DRAFT else ''}events/{event.id}/cover"
            if event.cover_filename
            else None
        ),
        "revision": event.revision,
    }


def serialize_many(db: Session, events: list[Event]) -> list[dict[str, object]]:
    counts: dict[uuid.UUID, int] = (
        dict(
            db.execute(
                select(Registration.event_id, func.count())
                .where(
                    Registration.event_id.in_([e.id for e in events]),
                    Registration.status == RegistrationStatus.CONFIRMED,
                )
                .group_by(Registration.event_id)
            )
            .tuples()
            .all()
        )
        if events
        else {}
    )
    return [serialize(db, e, counts.get(e.id, 0)) for e in events]


def public_list(
    db: Session, limit: int, offset: int, **filters: Any
) -> tuple[list[dict[str, object]], int]:
    events, total = event_repo.search(db, limit, offset, public=True, **filters)
    return serialize_many(db, events), total


def public_get(db: Session, event_id: uuid.UUID) -> dict[str, object]:
    event = event_repo.by_id(db, event_id)
    if not event or event.status == EventStatus.DRAFT:
        raise NotFoundError("event")
    return serialize(db, event)


def owned_list(
    db: Session, actor: User, limit: int, offset: int, **filters: Any
) -> tuple[list[dict[str, object]], int]:
    events, total = event_repo.search(
        db,
        limit,
        offset,
        organizer_id=None if actor.role == UserRole.ADMIN else actor.id,
        **filters,
    )
    return serialize_many(db, events), total


def managed_get(db: Session, event_id: uuid.UUID, actor: User) -> dict[str, object]:
    event = event_repo.by_id(db, event_id)
    if not event:
        raise NotFoundError("event")
    if not _can_manage(actor, event):
        raise ForbiddenError()
    return serialize(db, event)


def create(db: Session, request: EventCreate, actor: User) -> dict[str, object]:
    validate_category(db, request.category_id)
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
    if event.status == EventStatus.PUBLISHED and as_utc(event.starts_at) <= datetime.now(UTC):
        raise ConflictError("event_started", "An event that has started cannot be edited")
    values = request.model_dump(exclude_unset=True)
    if "category_id" in values:
        validate_category(db, request.category_id)
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
    event.revision += 1
    db.flush()
    if event.status == EventStatus.PUBLISHED:
        from app.services.registration_service import promote_waitlist

        promote_waitlist(db, event)
        if {"starts_at", "ends_at", "location", "timezone"} & values.keys():
            for registration in registration_repo.active_for_event(db, event.id):
                notify(db, registration.attendee, event, "event.updated")
                if registration.status == RegistrationStatus.CONFIRMED:
                    schedule_reminder(db, registration, event)
        else:
            # Revision changes also invalidate reminders; replace eligible pending reminders.
            for registration in db.scalars(
                select(Registration).where(
                    Registration.event_id == event.id,
                    Registration.status == RegistrationStatus.CONFIRMED,
                )
            ):
                schedule_reminder(db, registration, event)
    audit(db, actor, "event.updated", event.id)
    db.commit()
    db.refresh(event)
    return serialize(db, event)


def publish(db: Session, event_id: uuid.UUID, actor: User) -> dict[str, object]:
    require_verified(actor)
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
    event.ever_published = True
    event.revision += 1
    audit(db, actor, "event.published", event.id)
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
    if as_utc(event.ends_at) <= datetime.now(UTC):
        raise ConflictError("event_completed", "Completed events cannot be cancelled")
    event.status = EventStatus.CANCELLED
    event.revision += 1
    for registration in registration_repo.active_for_event(db, event.id):
        notify(db, registration.attendee, event, "event.cancelled")
        registration.status = RegistrationStatus.CANCELLED
        registration.cancelled_at = datetime.now(UTC)
        registration.ticket_nonce = None
    audit(db, actor, "event.cancelled", event.id)
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
    audit(db, actor, "event.deleted", event.id)
    db.commit()


def validate_category(db: Session, category_id: uuid.UUID | None) -> None:
    if category_id:
        category = db.get(Category, category_id)
        if not category or not category.is_active:
            raise DomainError("invalid_category", "Choose an active category", 422)
