from pydantic import BaseModel, EmailStr
from typing import Literal

UserRole = Literal['admin', 'organizer', 'user']

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = 'user'

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    class Config:
        orm_mode = True