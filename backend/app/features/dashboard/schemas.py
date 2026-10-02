"""Response models for the customer, expert and company dashboards."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RequestCounts(BaseModel):
    total: int = 0
    waiting: int = 0
    active: int = 0
    completed: int = 0


class MeetingOut(BaseModel):
    request_id: UUID
    request_title: str
    with_name: str
    starts_at: datetime


class MiniProfile(BaseModel):
    id: UUID
    kind: Literal["expert", "company"]
    display_name: str
    headline: str
    average_rating: float
    review_count: int
    verified: bool


class InterestRecommendations(BaseModel):
    interest: str
    profiles: list[MiniProfile]


class CustomerDashboard(BaseModel):
    requests: RequestCounts
    pending_actions: int
    saved_count: int
    upcoming_meetings: list[MeetingOut]
    recommendations: list[InterestRecommendations]


class Completeness(BaseModel):
    percent: int
    missing: list[str]


class MonthCount(BaseModel):
    month: str
    count: int


class DomainCount(BaseModel):
    domain: str
    count: int


class TeamMemberStat(BaseModel):
    user_id: UUID
    full_name: str
    member_role: Literal["admin", "staff"]
    open: int
    completed: int


class ProviderInsights(BaseModel):
    """Paid-plan analytics."""

    profile_views: int
    accept_rate: int | None
    avg_response_minutes: int | None
    leads_by_month: list[MonthCount]
    clients_by_domain: list[DomainCount]
    pipeline: dict[str, int] | None = None
    team: list[TeamMemberStat] | None = None


class ProviderDashboard(BaseModel):
    kind: Literal["expert", "company"]
    profile_id: UUID | None
    name: str
    organization_id: UUID | None = None
    member_role: Literal["admin", "staff"] | None = None
    plan: Literal["pro", "enterprise"]
    plan_active: bool
    plan_expires_at: datetime | None
    leads: RequestCounts
    average_rating: float
    review_count: int
    resolved_clients: int
    completeness: Completeness
    has_availability: bool
    upcoming_meetings: list[MeetingOut]
    insights: ProviderInsights | None = None
    locked_insights: list[str] = Field(default_factory=list)
