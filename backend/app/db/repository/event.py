import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
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


def search(
    db: Session,
    limit: int,
    offset: int,
    *,
    public: bool = False,
    organizer_id: uuid.UUID | None = None,
    **filters: object,
) -> tuple[list[Event], int]:
    now = datetime.now().astimezone()
    statement = select(Event)
    if public:
        statement = statement.where(Event.status == EventStatus.PUBLISHED, Event.ends_at > now)
    if organizer_id:
        statement = statement.where(Event.organizer_id == organizer_id)
    if filters.get("q"):
        term = str(filters["q"])
        statement = statement.where(
            or_(
                Event.title.icontains(term, autoescape=True),
                Event.description.icontains(term, autoescape=True),
            )
        )
    if filters.get("location"):
        statement = statement.where(
            Event.location.icontains(str(filters["location"]), autoescape=True)
        )
    if filters.get("category_id"):
        statement = statement.where(Event.category_id == filters["category_id"])
    if filters.get("starts_after"):
        statement = statement.where(Event.starts_at >= filters["starts_after"])
    if filters.get("starts_before"):
        statement = statement.where(Event.starts_at <= filters["starts_before"])
    status = filters.get("status")
    if status == "completed":
        statement = statement.where(Event.status == EventStatus.PUBLISHED, Event.ends_at <= now)
    elif status == "published":
        statement = statement.where(Event.status == EventStatus.PUBLISHED, Event.ends_at > now)
    elif status:
        statement = statement.where(Event.status == status)
    if filters.get("available_only"):
        count = (
            select(func.count(Registration.id))
            .where(
                Registration.event_id == Event.id,
                Registration.status == RegistrationStatus.CONFIRMED,
            )
            .correlate(Event)
            .scalar_subquery()
        )
        statement = statement.where(Event.capacity > count, Event.starts_at > now)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    sort = filters.get("sort", "starts_at" if public else "newest")
    order = {"starts_at": Event.starts_at, "newest": Event.created_at.desc(), "title": Event.title}[
        str(sort)
    ]
    return list(db.scalars(statement.order_by(order, Event.id).limit(limit).offset(offset))), total
