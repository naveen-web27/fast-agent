"""Validation models for the customer <-> expert/company request workflow."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

RequestStatusLiteral = Literal["submitted", "accepted", "meeting_booked", "provider_invited", "completed", "cancelled"]
ParticipantRole = Literal["customer", "expert", "company"]
PendingAction = Literal["accept", "confirm_completion", "review"]
ReviewTargetState = Literal["open", "waiting", "confirm_first", "disputed", "reviewed"]


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


class DisputeCompletionPayload(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class CreateReviewPayload(BaseModel):
    profile_id: UUID
    rating: int = Field(ge=1, le=5)
    body: str = Field(min_length=5, max_length=2000)


class AssignPayload(BaseModel):
    """Team member to hand the company's side of a request to; null unassigns."""

    user_id: UUID | None = None


class MemberOption(BaseModel):
    user_id: UUID
    full_name: str
    member_role: Literal["admin", "staff"]


class AppointmentOut(BaseModel):
    id: UUID
    profile_id: UUID | None
    with_name: str
    starts_at: datetime
    ends_at: datetime
    status: Literal["proposed", "confirmed", "cancelled", "completed"]


class BookableProfileOut(BaseModel):
    """An accepted provider on this request who publishes bookable time slots."""

    profile_id: UUID
    name: str


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
    completion_confirmed_at: datetime | None = None
    completion_disputed_at: datetime | None = None
    assigned_to_name: str | None = None
    contact: ContactInfo | None = None


class ReviewTargetOut(BaseModel):
    """A profile the viewer may rate on this request, and whether rating is unlocked yet."""

    profile_id: UUID
    name: str
    participant_role: ParticipantRole
    state: ReviewTargetState
    opens_at: datetime | None = None


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
    pending_action: PendingAction | None = None
    # For company viewers: which team member is handling it.
    assigned_to_name: str | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RequestDetail(RequestSummary):
    """Full detail for one request, including its participants and message timeline."""

    participants: list[RequestParticipantOut]
    events: list[RequestEventOut]
    expert_referral: ExpertReferralInfo | None = None
    can_mark_done: bool = False
    review_targets: list[ReviewTargetOut] = Field(default_factory=list)
    can_assign: bool = False
    assignable_members: list[MemberOption] = Field(default_factory=list)
    assigned_user_id: UUID | None = None
    appointments: list[AppointmentOut] = Field(default_factory=list)
    bookable_profiles: list[BookableProfileOut] = Field(default_factory=list)


class RequestListResponse(BaseModel):
    results: list[RequestSummary]
