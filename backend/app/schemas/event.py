from pydantic import BaseModel
from typing import Optional
from app.schemas.user import UserOut

class EventCreate(BaseModel):
    event_name: str
    event_details: str
    user_id: Optional[int]

class EventShow(BaseModel):
    id: int
    event_name: str
    event_details: str
    created_by: UserOut

    class Config:
        orm_mode = True