import uuid
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventFields(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1, max_length=20_000)
    location: str = Field(min_length=2, max_length=300)
    timezone: str = Field(max_length=64)
    starts_at: datetime
    ends_at: datetime
    capacity: int = Field(ge=1, le=1_000_000)

    @model_validator(mode="after")
    def validate_schedule(self) -> "EventFields":
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("event timestamps must include a timezone offset")
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return self


class EventCreate(EventFields):
    pass


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=20_000)
    location: str | None = Field(default=None, min_length=2, max_length=300)
    timezone: str | None = Field(default=None, max_length=64)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    capacity: int | None = Field(default=None, ge=1, le=1_000_000)

    @model_validator(mode="after")
    def validate_values(self) -> "EventUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        if (self.starts_at and self.starts_at.tzinfo is None) or (
            self.ends_at and self.ends_at.tzinfo is None
        ):
            raise ValueError("event timestamps must include a timezone offset")
        if self.timezone:
            try:
                ZoneInfo(self.timezone)
            except ZoneInfoNotFoundError as exc:
                raise ValueError("timezone must be a valid IANA timezone") from exc
        return self


class EventOut(BaseModel):
    id: uuid.UUID
    organizer_id: uuid.UUID
    title: str
    description: str
    location: str
    timezone: str
    starts_at: datetime
    ends_at: datetime
    capacity: int
    status: str
    confirmed_count: int = 0
    available_seats: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
