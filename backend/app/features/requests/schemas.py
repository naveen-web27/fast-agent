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
    title: str = Field(min_length=3, max_length=160)
    requirements: str = Field(min_length=10, max_length=4000)
    city: str | None = Field(default=None, max_length=100)


class AddEventPayload(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class RequestParticipantOut(BaseModel):
    participant_role: ParticipantRole
    name: str
    accepted_at: datetime | None


class RequestEventOut(BaseModel):
    id: UUID
    author_name: str | None
    event_type: str
    message: str
    created_at: datetime


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


class RequestListResponse(BaseModel):
    results: list[RequestSummary]
