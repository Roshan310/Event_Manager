from sqlalchemy.orm import Session
import app.db.repository.event as event_repo
from app.models import event as model_event
from app.schemas import event as event_schemas


def create_event(db: Session, event: event_schemas.EventCreate, user_id: int):
    new_event = model_event.Event(
        event_name=event.event_name,
        event_details=event.event_details,
        user_id=user_id
    )
    return event_repo.create_event(db, new_event)

def list_events(db: Session):
    return event_repo.get_all_events(db)

def my_events(db: Session, user_id: int):
    return event_repo.get_user_events(db, user_id)

def get_event_by_id(db: Session, event_id: int):    
    return event_repo.get_event_by_id(db, event_id)

def total_events(db: Session):
    return event_repo.count_total_events(db)

def my_registered_events(db: Session, user_id: int):
    return event_repo.get_my_registered_events(db, user_id)