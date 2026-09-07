import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import current_user, event_manager
from app.db.database import get_db
from app.models.user import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.registration import MyRegistrationOut, RegistrationOut, RosterEntry
from app.services import registration_service

router = APIRouter(tags=["Registrations"])


@router.post(
    "/events/{event_id}/registrations",
    response_model=RegistrationOut,
    status_code=status.HTTP_201_CREATED,
)
def register(
    event_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(current_user)
) -> RegistrationOut:
    return RegistrationOut.model_validate(registration_service.register(db, event_id, actor))


@router.delete("/events/{event_id}/registrations/me", status_code=status.HTTP_204_NO_CONTENT)
def cancel(
    event_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(current_user)
) -> Response:
    registration_service.cancel(db, event_id, actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/me/registrations", response_model=PaginatedResponse[MyRegistrationOut])
def mine(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    actor: User = Depends(current_user),
) -> PaginatedResponse[MyRegistrationOut]:
    rows, total = registration_service.list_mine(db, actor, limit, offset)
    items = [MyRegistrationOut.model_validate(row) for row in rows]
    return PaginatedResponse.create(items, total, limit, offset)


@router.get("/events/{event_id}/registrations", response_model=PaginatedResponse[RosterEntry])
def roster(
    event_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    actor: User = Depends(event_manager),
) -> PaginatedResponse[RosterEntry]:
    rows, total = registration_service.roster(db, event_id, actor, limit, offset)
    items = [RosterEntry.model_validate(row) for row in rows]
    return PaginatedResponse.create(items, total, limit, offset)
