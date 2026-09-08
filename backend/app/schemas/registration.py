import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.registration import RegistrationStatus
from app.schemas.event import EventOut
from app.schemas.user import UserOut


class RegistrationOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    attendee_id: uuid.UUID
    status: RegistrationStatus
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None
    queued_at: datetime
    checked_in_at: datetime | None = None
    waitlist_position: int | None = None
    model_config = ConfigDict(from_attributes=True)


class MyRegistrationOut(RegistrationOut):
    event: EventOut


class RosterEntry(RegistrationOut):
    attendee: UserOut
