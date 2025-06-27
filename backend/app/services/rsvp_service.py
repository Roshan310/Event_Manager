from app.db.repository import rsvp as rsvp_repo
from fastapi import HTTPException

def create_rsvp(db, rsvp, user_id: int):
    event = rsvp_repo.get_event_rsvp(db, rsvp.event_id)
    found_rsvp = rsvp_repo.rsvp_already_exists(db, rsvp.event_id, user_id)
    if not event:
        return HTTPException(status_code=404, detail="Event doesn't exist!!")
    if rsvp.dir == 1:
        if found_rsvp:
            return HTTPException(status_code=409, detail="Already rsvp'd !!")
        
        rsvp_repo.create_rsvp(db, rsvp)
        return {"msg": "Successfully registered for the event! Congrats!!"}
    else:
        if not found_rsvp:
            return HTTPException(status_code=404, detail="Doesn't exist")
        
        rsvp_repo.delete_rsvp(db, rsvp.event_id, user_id)
        return {"msg": "Canceled the registration!!"}
    return rsvp_repo.create_rsvp(db, rsvp)