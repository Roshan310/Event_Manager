from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.rsvp import Rsvp

def get_all_events(db: Session, limit: int = 10, offset: int = 0):
    """Get all events with pagination"""
    query = db.query(Event)
    total = query.count()
    events = query.offset(offset).limit(limit).all()
    return events, total

def get_event_by_id(db: Session, event_id: int):
    return db.query(Event).filter(Event.id == event_id).first()

def get_user_events(db: Session, user_id: int, limit: int = 10, offset: int = 0):
    """Get user's created events with pagination"""
    query = db.query(Event).filter(Event.user_id == user_id)
    total = query.count()
    user_event = query.offset(offset).limit(limit).all()
    return user_event, total

def create_event(db: Session, event: Event):
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, event: Event):
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: Event):
    db.delete(event)
    db.commit()

def count_total_events(db: Session):
    return db.query(Event).count() 

def get_my_registered_events(db: Session, user_id: int, limit: int = 10, offset: int = 0):
    """Get user's registered events with pagination"""
    query = db.query(Event).join(
        Rsvp, Event.id == Rsvp.event_id, isouter=True
    ).filter(Rsvp.user_id == user_id)
    total = query.count()
    events = query.offset(offset).limit(limit).all()
    return events, total