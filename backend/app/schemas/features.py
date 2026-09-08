import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def trim_text(cls, value: object, info: ValidationInfo) -> object:
        if isinstance(value, str) and info.field_name not in {
            "password",
            "current_password",
            "token",
        }:
            return value.strip()
        return value


class Acknowledgement(BaseModel):
    message: str = "If the account is eligible, an email will be sent."


class ProfileUpdate(Input):
    name: str = Field(min_length=2, max_length=120)


class EmailRequest(Input):
    email: EmailStr


class TokenRequest(Input):
    token: str = Field(min_length=32, max_length=256)


class ResetPassword(TokenRequest):
    password: str = Field(min_length=10, max_length=128)


class ChangePassword(Input):
    current_password: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=10, max_length=128)


class StatusUpdate(Input):
    is_active: bool


class TransferOwner(Input):
    organizer_id: uuid.UUID


class CategoryCreate(Input):
    name: str = Field(min_length=2, max_length=80)


class CategoryUpdate(CategoryCreate):
    is_active: bool


class CategoryOut(CategoryUpdate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class Preferences(Input):
    reminder_emails: bool


class NotificationRead(Input):
    is_read: Literal[True]


class NotificationOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID | None
    topic: str
    message: str
    created_at: datetime
    read_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class AuditOut(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    target_id: uuid.UUID
    details: dict[str, object]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OutboxOut(BaseModel):
    id: uuid.UUID
    topic: str
    attempts: int
    available_at: datetime
    created_at: datetime
    processed_at: datetime | None
    failed_at: datetime | None
    lease_until: datetime | None
    model_config = ConfigDict(from_attributes=True)


class WorkerStatus(BaseModel):
    last_seen_at: datetime | None
    healthy: bool
    pending: int
    failed: int


class TicketOut(BaseModel):
    registration_id: uuid.UUID
    event_id: uuid.UUID
    event_title: str
    attendee_name: str
    qr_payload: str
    qr_url: str
    checked_in_at: datetime | None


class CheckInRequest(Input):
    token: str | None = Field(default=None, min_length=32, max_length=256)
    registration_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def exactly_one(self) -> "CheckInRequest":
        if (self.token is None) == (self.registration_id is None):
            raise ValueError("provide exactly one of token or registration_id")
        return self


class EventSummary(BaseModel):
    event_id: uuid.UUID
    confirmed: int
    waitlisted: int
    cancelled: int
    checked_in: int
    remaining_seats: int
    attendance_rate: float
