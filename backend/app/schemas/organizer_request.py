import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrganizerRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    organization: str = Field(min_length=2, max_length=120)
    intent: str = Field(min_length=20, max_length=2000)


class OrganizerRequestReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    status: Literal["approved", "rejected"]
    feedback: str | None = Field(None, min_length=3, max_length=500)

    @model_validator(mode="after")
    def rejection_feedback(self) -> "OrganizerRequestReview":
        if self.status == "rejected" and not self.feedback:
            raise ValueError("Rejection requires feedback")
        return self


class OrganizerRequestOut(OrganizerRequestCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    status: Literal["pending", "approved", "rejected"]
    feedback: str | None
    reviewer_id: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class AdminOverview(BaseModel):
    users_by_role: dict[str, int]
    users_by_status: dict[str, int]
    events_by_status: dict[str, int]
    registrations_by_status: dict[str, int]
    check_ins: int
    pending_applications: int
    generated_at: datetime
