from pydantic import BaseModel

class Event(BaseModel):
    id: int
    event_name: str
    event_details: str

    class Config:
        orm_mode = True

class User(BaseModel):
    id: int
    name: str
    email: str
    password: str

    class Config:
        orm_mode = True
        