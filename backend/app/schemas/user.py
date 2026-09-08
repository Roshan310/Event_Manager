import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: object) -> object:
        return " ".join(value.split()) if isinstance(value, str) else value


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    email_verified: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: UserRole
