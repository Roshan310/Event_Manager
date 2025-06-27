from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core import security
from app.db import database
from app.schemas.event import EventCreate, EventShow    
from app.services import event_service

router = APIRouter(
    prefix='/events',
    tags=['Events']
)

@router.get('/', response_model=List[EventShow])
def get_events(db: Session = Depends(database.get_db)):
    return event_service.list_events(db)


@router.post('/add_event', response_model=EventShow)
def add_event(request: EventCreate, db: Session = Depends(database.get_db), current_user: int = Depends(security.get_current_user)):
    new_event = event_service.create_event(db, request, current_user.id)
    if not new_event:
        raise HTTPException(status_code=400, detail="Event creation failed")
    return new_event

@router.get('/my_events', response_model=List[EventShow])
def my_events(db: Session = Depends(database.get_db), current_user: int = Depends(security.get_current_user)):
    return event_service.my_events(db, current_user.id)

@router.get('/registered_events')
def my_registered_events(db: Session = Depends(database.get_db), current_user: int = Depends(security.get_current_user)):
    return event_service.my_registered_events(db, current_user.id)

# @router.get('/total_events')
# def total_events(db: Session = Depends(database.get_db)):
#     return {"total_events": event_service.total_events(db)}

# @router.get('/{event_id}', response_model=EventShow)
# def get_event(event_id: int, db: Session = Depends(database.get_db)):   
#     event = event_service.get_event_by_id(db, event_id)
#     if not event:
#         raise HTTPException(status_code=404, detail="Event not found")
#     return event