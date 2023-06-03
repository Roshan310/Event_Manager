from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, oauth2

router = APIRouter(
    prefix='/events',
    tags=['Events']
)


@router.get('/', response_model=List[schemas.EventShow])
def get_events(db: Session = Depends(database.get_db)):
    events = db.query(models.Event).all()
    return events

@router.post('/add_event', response_model=schemas.EventShow)
def add_event(request: schemas.EventCreate, db: Session = Depends(database.get_db), current_user: int = Depends(oauth2.get_current_user)):
    user_id = current_user.id
    new_event = models.Event(event_name = request.event_name, event_details = request.event_details, user_id=user_id)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event

@router.get('/my_events', response_model=List[schemas.EventShow])
def my_events(db: Session = Depends(database.get_db), current_user: int = Depends(oauth2.get_current_user)):
    events = db.query(models.Event).filter(models.Event.user_id == current_user.id).all()
    return events

@router.get('/registered_events')
def my_registered_events(db: Session = Depends(database.get_db), current_user: int = Depends(oauth2.get_current_user)):
    result = db.query(models.Event).join(models.Rsvp, models.Event.id == models.Rsvp.event_id, isouter=True).filter(models.Rsvp.user_id==current_user.id).all()
    return result