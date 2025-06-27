from pydantic import BaseModel, conint

class Rsvp(BaseModel):
    event_id: int
    dir: conint(le=1)