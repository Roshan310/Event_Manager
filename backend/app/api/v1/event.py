from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core import security
from app.db import database
from app.schemas.event import EventCreate, EventShow, EventUpdate
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.services import event_service

router = APIRouter(
    prefix='/events',
    tags=['Events']
)

@router.get('/', response_model=PaginatedResponse[EventShow])
def get_events(
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    db: Session = Depends(database.get_db)
):
    events, total = event_service.list_events(db, limit, offset)
    return PaginatedResponse.create(items=events, total=total, limit=limit, offset=offset)


@router.post('/add_event', response_model=EventShow)
def add_event(request: EventCreate, db: Session = Depends(database.get_db), current_user: int = Depends(security.get_current_user)):
    new_event, error = event_service.create_event(db, request, current_user)
    if error == "forbidden":
        raise HTTPException(status_code=403, detail="Only admin or organizer can create events")
    if not new_event:
        raise HTTPException(status_code=400, detail="Event creation failed")
    return new_event

@router.get('/my_events', response_model=PaginatedResponse[EventShow])
def my_events(
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    db: Session = Depends(database.get_db),
    current_user: int = Depends(security.get_current_user)
):
    user_events, total = event_service.my_events(db, current_user.id, limit, offset)
    return PaginatedResponse.create(items=user_events, total=total, limit=limit, offset=offset)

@router.get('/registered_events', response_model=PaginatedResponse[EventShow])
def my_registered_events(
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    db: Session = Depends(database.get_db),
    current_user: int = Depends(security.get_current_user)
):
    events, total = event_service.my_registered_events(db, current_user.id, limit, offset)
    return PaginatedResponse.create(items=events, total=total, limit=limit, offset=offset)

@router.get('/total_events')
def total_events(db: Session = Depends(database.get_db)):
    return {"total_events": event_service.total_events(db)}

@router.get('/{event_id}', response_model=EventShow)
def get_event(event_id: int, db: Session = Depends(database.get_db)):   
    event = event_service.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put('/{event_id}', response_model=EventShow)
def update_event(
    event_id: int,
    request: EventUpdate,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(security.get_current_user)
):
    updated_event, error = event_service.update_event(db, event_id, current_user, request)

    if error == "not_found":
        raise HTTPException(status_code=404, detail="Event not found")

    if error == "forbidden":
        raise HTTPException(status_code=403, detail="Only admin or owning organizer can update this event")

    if error == "empty_payload":
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    return updated_event


@router.delete('/{event_id}')
def delete_event(
    event_id: int,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(security.get_current_user)
):
    error = event_service.delete_event(db, event_id, current_user)

    if error == "not_found":
        raise HTTPException(status_code=404, detail="Event not found")

    if error == "forbidden":
        raise HTTPException(status_code=403, detail="Only admin or owning organizer can delete this event")

    return {"detail": "Event deleted successfully"}