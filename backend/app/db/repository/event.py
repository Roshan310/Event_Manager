from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.rsvp import Rsvp

def get_all_events(db: Session):
    return db.query(Event).all()

def get_event_by_id(db: Session, event_id: int):
    return db.query(Event).filter(Event.id == event_id).first()

def get_user_events(db: Session, user_id: int):
    user_event =  db.query(Event).filter(Event.user_id == user_id).all()
    if not user_event:
        return None
    return user_event

def create_event(db: Session, event: Event):
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def count_total_events(db: Session):
    return db.query(Event).count() 

def get_my_registered_events(db: Session, user_id: int):
    return db.query(Event).join(
        Rsvp, Event.id == Rsvp.event_id, isouter=True
    ).filter(Rsvp.user_id == user_id).all()