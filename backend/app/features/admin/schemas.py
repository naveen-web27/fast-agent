"""Validation models for the lightweight admin verification console."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class PendingProfile(BaseModel):
    """A marketplace profile awaiting (or already given) an admin verification decision."""

    id: UUID
    kind: Literal["expert", "company"]
    display_name: str
    headline: str
    city: str | None
    verification: Literal["pending", "verified", "rejected"]
    owner_email: str | None
    organization_id: UUID | None


class VerificationDecision(BaseModel):
    status: Literal["verified", "rejected"]
