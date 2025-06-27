from app.models.rsvp import Rsvp
from app.models.event import Event

def get_event_rsvp(db, event_id: int):
    return db.query(Event).filter(Rsvp.event_id == event_id).first()

def rsvp_already_exists(db, event_id: int, user_id: int):
    return db.query(Rsvp).filter(Rsvp.event_id == event_id, Rsvp.user_id == user_id).first()

def delete_rsvp(db, event_id: int, user_id: int):
    rsvp_query = db.query(Rsvp).filter(Rsvp.event_id == event_id, Rsvp.user_id == user_id)
    rsvp_query.delete()
    db.commit()
    return rsvp_query.first() 

def create_rsvp(db, rsvp):
    db.add(rsvp)
    db.commit()
    db.refresh(rsvp)
    return rsvp