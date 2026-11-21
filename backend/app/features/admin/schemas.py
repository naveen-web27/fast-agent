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
    claim_status: Literal["unclaimed", "claimed"] | None = None
    contact_email: str | None = None
    blocked_at: datetime | None = None
    blocked_reason: str | None = None
    deleted_at: datetime | None = None
    created_at: datetime | None = None


class VerificationDecision(BaseModel):
    status: Literal["verified", "rejected"]


class BlockProfilePayload(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class AdminUser(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None
    role: Literal["customer", "expert", "company_admin", "platform_admin", "worker"]
    created_at: datetime
    blocked_at: datetime | None
    blocked_reason: str | None
    deleted_at: datetime | None
    has_expert_profile: bool
    companies: list[str]
    requests_sent: int


class AdminStats(BaseModel):
    users_total: int
    users_new_7d: int
    users_blocked: int
    users_deleted: int
    experts_live: int
    companies_live: int
    profiles_pending: int
    profiles_blocked: int
    requests_open: int
    requests_new_7d: int
    requests_completed: int
    disputes_open: int
    companies_unclaimed: int = 0
    claims_pending: int = 0
    workers_live: int = 0
    workers_unclaimed: int = 0


class AdminDispute(BaseModel):
    participant_id: UUID
    request_id: UUID
    request_title: str
    customer_name: str
    customer_email: str | None
    provider_name: str
    provider_role: str
    disputed_at: datetime
    reason: str | None


class DisputeResolution(BaseModel):
    action: Literal["open_ratings", "reopen"]


class AdminActivity(BaseModel):
    id: UUID
    admin_name: str | None
    action: str
    target_type: str
    target_id: UUID
    target_label: str | None
    reason: str | None
    created_at: datetime
