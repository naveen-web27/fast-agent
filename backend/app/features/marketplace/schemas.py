"""Validation models owned by the marketplace discovery feature."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.features.profiles.schemas import EducationOut, ExperienceOut


class ProfileSummary(BaseModel):
    """A single search result shown on the discover page."""

    id: UUID
    kind: Literal["expert", "company"]
    display_name: str
    headline: str
    city: str | None
    years_experience: int | None
    languages: list[str]
    avatar_url: str | None
    verified: bool
    average_rating: float
    review_count: int
    response_minutes: int | None
    tags: list[str]
    # None when the owner has hidden this badge (see ProfileVisibilityUpdate).
    resolved_clients_count: int | None


class ProfileListResponse(BaseModel):
    """Paged list of marketplace profiles."""

    results: list[ProfileSummary]
    total: int
    page: int
    page_size: int


class ReviewSummary(BaseModel):
    """A single review shown on a profile's detail page."""

    reviewer_name: str
    rating: int
    body: str
    created_at: datetime


class ProfileLink(BaseModel):
    platform: str
    url: str


class PublicCredential(BaseModel):
    title: str
    issuing_body: str | None
    verified: bool


class PublicOffering(BaseModel):
    title: str
    description: str | None
    price_min_inr: int | None
    price_max_inr: int | None


class ProfileDetail(ProfileSummary):
    """Full profile detail including bio and reviews, for the profile preview page."""

    bio: str | None
    reviews: list[ReviewSummary]
    intro_video_url: str | None = None
    portfolio_url: str | None = None
    social_links: list[ProfileLink] = []
    credentials: list[PublicCredential] = []
    offerings: list[PublicOffering] = []
    experiences: list[ExperienceOut] = []
    educations: list[EducationOut] = []
    founded_year: int | None = None
    team_size: str | None = None
    member_since: datetime | None = None
    # Paid provider with published weekly slots: customers can pick a time once the request is accepted.
    bookable: bool = False


class ProfileVisibilityUpdate(BaseModel):
    """Lets an expert or company admin toggle their public resolved-clients badge."""

    show_resolved_count: bool

