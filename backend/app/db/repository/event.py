import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus
from app.models.registration import Registration, RegistrationStatus


def by_id(db: Session, event_id: uuid.UUID, *, for_update: bool = False) -> Event | None:
    statement = select(Event).where(Event.id == event_id)
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def list_public(db: Session, now: datetime, limit: int, offset: int) -> tuple[list[Event], int]:
    condition = (Event.status == EventStatus.PUBLISHED, Event.ends_at > now)
    total = db.scalar(select(func.count()).select_from(Event).where(*condition)) or 0
    events = list(
        db.scalars(
            select(Event)
            .where(*condition)
            .order_by(Event.starts_at, Event.id)
            .offset(offset)
            .limit(limit)
        )
    )
    return events, total


def list_owned(
    db: Session, organizer_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[Event], int]:
    condition = Event.organizer_id == organizer_id
    total = db.scalar(select(func.count()).select_from(Event).where(condition)) or 0
    events = list(
        db.scalars(
            select(Event)
            .where(condition)
            .order_by(Event.created_at.desc(), Event.id)
            .offset(offset)
            .limit(limit)
        )
    )
    return events, total


def list_all(db: Session, limit: int, offset: int) -> tuple[list[Event], int]:
    total = db.scalar(select(func.count()).select_from(Event)) or 0
    events = list(
        db.scalars(
            select(Event).order_by(Event.created_at.desc(), Event.id).offset(offset).limit(limit)
        )
    )
    return events, total


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
