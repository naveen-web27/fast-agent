"""Validation models for the customer <-> expert/company request workflow."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

RequestStatusLiteral = Literal["submitted", "accepted", "meeting_booked", "provider_invited", "completed", "cancelled"]
ParticipantRole = Literal["customer", "expert", "company"]


class CreateRequestPayload(BaseModel):
    """Submitted when a customer requests a consultation from a specific profile."""

    profile_id: UUID
    service_id: UUID | None = None
    title: str = Field(min_length=3, max_length=160)
    requirements: str = Field(min_length=10, max_length=4000)
    city: str | None = Field(default=None, max_length=100)


class AddEventPayload(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class InviteCompanyPayload(BaseModel):
    """Submitted by an accepted expert to bring a company into their request."""

    profile_id: UUID


class SocialLinkOut(BaseModel):
    platform: str
    url: str


class ContactInfo(BaseModel):
    """Revealed only once both sides of a request pair have accepted."""

    full_name: str
    email: str | None
    phone: str | None
    website_url: str | None = None
    social_links: list[SocialLinkOut] = Field(default_factory=list)


class RequestParticipantOut(BaseModel):
    participant_role: ParticipantRole
    name: str
    accepted_at: datetime | None
    contact: ContactInfo | None = None


class RequestEventOut(BaseModel):
    id: UUID
    author_name: str | None
    event_type: str
    message: str
    created_at: datetime


class DomainClientStat(BaseModel):
    domain: str
    client_count: int


class ExpertReferralInfo(BaseModel):
    """Credibility snapshot of the expert on this request, shown to a company being invited in."""

    profile_id: UUID
    display_name: str
    headline: str
    verified: bool
    average_rating: float
    review_count: int
    client_stats: list[DomainClientStat]


class RequestSummary(BaseModel):
    """One row in the caller's request list, whichever side of it they're on."""

    id: UUID
    title: str
    requirements: str
    city: str | None
    status: RequestStatusLiteral
    my_role: ParticipantRole
    counterpart_name: str
    created_at: datetime
    updated_at: datetime


class RequestDetail(RequestSummary):
    """Full detail for one request, including its participants and message timeline."""

    participants: list[RequestParticipantOut]
    events: list[RequestEventOut]
    expert_referral: ExpertReferralInfo | None = None


class RequestListResponse(BaseModel):
    results: list[RequestSummary]
