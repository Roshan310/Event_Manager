import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.event import Event
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User


def by_attendee_event(
    db: Session, event_id: uuid.UUID, attendee_id: uuid.UUID, *, for_update: bool = False
) -> Registration | None:
    statement = select(Registration).where(
        Registration.event_id == event_id, Registration.attendee_id == attendee_id
    )
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def confirmed_count(db: Session, event_id: uuid.UUID) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Registration)
            .where(
                Registration.event_id == event_id,
                Registration.status == RegistrationStatus.CONFIRMED,
            )
        )
        or 0
    )


def next_waitlisted(db: Session, event_id: uuid.UUID) -> Registration | None:
    return db.scalar(
        select(Registration)
        .where(
            Registration.event_id == event_id, Registration.status == RegistrationStatus.WAITLISTED
        )
        .order_by(Registration.queued_at, Registration.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )


def list_for_attendee(
    db: Session, attendee_id: uuid.UUID, limit: int, offset: int, **filters: object
) -> tuple[list[Registration], int]:
    conditions = [Registration.attendee_id == attendee_id]
    if filters.get("status"):
        conditions.append(Registration.status == filters["status"])
    if filters.get("period") == "upcoming":
        conditions.append(Event.ends_at > datetime.now(UTC))
    elif filters.get("period") == "past":
        conditions.append(Event.ends_at <= datetime.now(UTC))
    statement = select(Registration).join(Event).where(*conditions)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = list(
        db.scalars(
            statement.options(joinedload(Registration.event))
            .order_by(Registration.created_at.desc(), Registration.id)
            .offset(offset)
            .limit(limit)
        )
    )
    return rows, total


def list_roster(
    db: Session, event_id: uuid.UUID, limit: int, offset: int, **filters: object
) -> tuple[list[Registration], int]:
    condition = [Registration.event_id == event_id]
    if filters.get("status"):
        condition.append(Registration.status == filters["status"])
    elif not filters.get("include_cancelled"):
        condition.append(Registration.status != RegistrationStatus.CANCELLED)
    if filters.get("q"):
        term = str(filters["q"])
        condition.append(
            or_(
                User.name.icontains(term, autoescape=True),
                User.email.icontains(term, autoescape=True),
            )
        )
    statement = (
        select(Registration).join(User, User.id == Registration.attendee_id).where(*condition)
    )
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = list(
        db.scalars(
            statement.options(joinedload(Registration.attendee))
            .order_by(Registration.status, Registration.created_at, Registration.id)
            .offset(offset)
            .limit(limit)
        )
    )
    return rows, total


def active_for_event(db: Session, event_id: uuid.UUID) -> Iterator[Registration]:
    yield from db.scalars(
        select(Registration)
        .options(joinedload(Registration.attendee))
        .where(
            Registration.event_id == event_id, Registration.status != RegistrationStatus.CANCELLED
        )
        .order_by(Registration.id)
        .execution_options(yield_per=200)
    )
