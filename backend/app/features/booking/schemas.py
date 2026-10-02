"""Validation models for booking meetings on a request."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class BookAppointmentPayload(BaseModel):
    profile_id: UUID
    starts_at: datetime

    @field_validator("starts_at")
    @classmethod
    def _require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("starts_at must include a timezone")
        return value


class SlotsResponse(BaseModel):
    profile_id: UUID
    name: str
    slot_minutes: int
    slots: list[datetime]
