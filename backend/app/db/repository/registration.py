import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.registration import Registration, RegistrationStatus


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
        .order_by(Registration.created_at, Registration.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )


def list_for_attendee(
    db: Session, attendee_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[Registration], int]:
    condition = Registration.attendee_id == attendee_id
    total = db.scalar(select(func.count()).select_from(Registration).where(condition)) or 0
    rows = list(
        db.scalars(
            select(Registration)
            .options(joinedload(Registration.event))
            .where(condition)
            .order_by(Registration.created_at.desc(), Registration.id)
            .offset(offset)
            .limit(limit)
        )
    )
    return rows, total


def list_roster(
    db: Session, event_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[Registration], int]:
    condition = (
        Registration.event_id == event_id,
        Registration.status != RegistrationStatus.CANCELLED,
    )
    total = db.scalar(select(func.count()).select_from(Registration).where(*condition)) or 0
    rows = list(
        db.scalars(
            select(Registration)
            .options(joinedload(Registration.attendee))
            .where(*condition)
            .order_by(Registration.status, Registration.created_at, Registration.id)
            .offset(offset)
            .limit(limit)
        )
    )
    return rows, total
