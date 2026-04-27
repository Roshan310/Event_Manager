from app.db.repository import rsvp as rsvp_repo
from app.models import rsvp as rsvp_model
from app.models import user as user_model
from app.schemas import rsvp as rsvp_schema
from fastapi import HTTPException

ROLE_USER = 'user'


def create_rsvp(db, rsvp: rsvp_schema.Rsvp, actor: user_model.User):
    if actor.role != ROLE_USER:
        raise HTTPException(status_code=403, detail='Only normal users can RSVP to events')

    event = rsvp_repo.get_event_rsvp(db, rsvp.event_id)
    found_rsvp = rsvp_repo.rsvp_already_exists(db, rsvp.event_id, actor.id)

    if not event:
        raise HTTPException(status_code=404, detail="Event doesn't exist!!")

    if rsvp.dir == 1:
        if found_rsvp:
            raise HTTPException(status_code=409, detail="Already rsvp'd !!")

        new_rsvp = rsvp_model.Rsvp(user_id=actor.id, event_id=rsvp.event_id)
        rsvp_repo.create_rsvp(db, new_rsvp)
        return {
            'msg': 'Successfully registered for the event! Congrats!!',
            'send_email': True,
            'email_data': {
                'recipient_email': actor.email,
                'recipient_name': actor.name,
                'event_name': event.event_name,
                'event_details': event.event_details,
            },
        }

    if not found_rsvp:
        raise HTTPException(status_code=404, detail="Doesn't exist")

    rsvp_repo.delete_rsvp(db, rsvp.event_id, actor.id)
    return {'msg': 'Canceled the registration!!', 'send_email': False, 'email_data': None}