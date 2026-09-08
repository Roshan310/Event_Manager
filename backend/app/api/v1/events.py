import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import event_manager
from app.core.errors import DomainError
from app.db.database import get_db
from app.models.user import User
from app.schemas.event import EventCreate, EventOut, EventUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import event_service

router = APIRouter(prefix="/events", tags=["Events"])
organizer_router = APIRouter(prefix="/organizer/events", tags=["Organizer events"])


@router.get("", response_model=PaginatedResponse[EventOut])
def list_events(
    q: str | None = Query(None, min_length=1, max_length=200),
    category_id: uuid.UUID | None = None,
    location: str | None = Query(None, min_length=1, max_length=300),
    starts_after: datetime | None = None,
    starts_before: datetime | None = None,
    available_only: bool = False,
    sort: Literal["starts_at", "newest", "title"] = "starts_at",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedResponse[EventOut]:
    if any(value is not None and value.tzinfo is None for value in (starts_after, starts_before)):
        raise DomainError("invalid_schedule", "Date filters require a timezone offset", 422)
    if starts_after and starts_before and starts_before < starts_after:
        raise DomainError("invalid_schedule", "Date range is reversed", 422)
    rows, total = event_service.public_list(
        db,
        limit,
        offset,
        q=q,
        category_id=category_id,
        location=location,
        starts_after=starts_after,
        starts_before=starts_before,
        available_only=available_only,
        sort=sort,
    )
    events = [EventOut.model_validate(row) for row in rows]
    return PaginatedResponse.create(events, total, limit, offset)


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, object]:
    return event_service.public_get(db, event_id)


@organizer_router.get("", response_model=PaginatedResponse[EventOut])
def owned_events(
    q: str | None = Query(None, min_length=1, max_length=200),
    status: Literal["draft", "published", "completed", "cancelled"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    actor: User = Depends(event_manager),
) -> PaginatedResponse[EventOut]:
    rows, total = event_service.owned_list(db, actor, limit, offset, q=q, status=status)
    events = [EventOut.model_validate(row) for row in rows]
    return PaginatedResponse.create(events, total, limit, offset)


@organizer_router.get("/{event_id}", response_model=EventOut)
def managed_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(event_manager),
) -> dict[str, object]:
    return event_service.managed_get(db, event_id, actor)


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    request: EventCreate, db: Session = Depends(get_db), actor: User = Depends(event_manager)
) -> dict[str, object]:
    return event_service.create(db, request, actor)


@router.patch("/{event_id}", response_model=EventOut)
def update_event(
    event_id: uuid.UUID,
    request: EventUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(event_manager),
) -> dict[str, object]:
    return event_service.update(db, event_id, request, actor)


@router.post("/{event_id}/publish", response_model=EventOut)
def publish_event(
    event_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(event_manager)
) -> dict[str, object]:
    return event_service.publish(db, event_id, actor)


@router.post("/{event_id}/cancel", response_model=EventOut)
def cancel_event(
    event_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(event_manager)
) -> dict[str, object]:
    return event_service.cancel(db, event_id, actor)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(event_manager)
) -> Response:
    event_service.delete_draft(db, event_id, actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
