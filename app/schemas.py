from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    name: str
    email: str

    class Config:
        orm_mode = True


class EventCreate(BaseModel):
    event_name: str
    event_details: str
    user_id: Optional[int]


class EventShow(BaseModel):
    event_name: str
    event_details: str
    created_by: UserOut

    class Config:
        orm_mode = True

# class User(BaseModel):
#     id: int
#     name: str
#     email: str
#     password: str

#     class Config:
#         orm_mode = True

        
class TokenData(BaseModel):
    id: Optional[str] = None