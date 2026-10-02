"""Validation models for the lightweight admin verification console."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PendingProfile(BaseModel):
    """A marketplace profile as shown in the admin console."""

    id: UUID
    kind: Literal["expert", "company"]
    display_name: str
    headline: str
    city: str | None
    verification: Literal["pending", "verified", "rejected"]
    owner_email: str | None
    organization_id: UUID | None
    blocked_at: datetime | None = None
    blocked_reason: str | None = None
    created_at: datetime | None = None


class VerificationDecision(BaseModel):
    status: Literal["verified", "rejected"]


class BlockProfilePayload(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
