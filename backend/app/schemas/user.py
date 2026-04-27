from pydantic import BaseModel, EmailStr, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)