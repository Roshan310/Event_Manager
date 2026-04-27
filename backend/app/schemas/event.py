from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.schemas.user import UserOut

class EventCreate(BaseModel):
    event_name: str
    event_details: str
    user_id: Optional[int]


class EventUpdate(BaseModel):
    event_name: Optional[str] = None
    event_details: Optional[str] = None

class EventShow(BaseModel):
    id: int
    event_name: str
    event_details: str
    created_by: UserOut

    model_config = ConfigDict(from_attributes=True)