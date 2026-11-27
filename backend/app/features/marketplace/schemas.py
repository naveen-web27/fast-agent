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
    pincode: str | None = None
    locality: str | None = None
    # 4 same area, 3 same district/city, 2 same state, 1 same region, 0 elsewhere; None when the searcher gave no location.
    nearness: int | None = None
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
    # False for admin-added company listings the owner hasn't claimed; they can't receive requests yet.
    claimed: bool = True
    # True when signed-in users can open this provider's phone/WhatsApp/email with "View contact".
    contact_available: bool = False


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


class ProfileContactViewOut(BaseModel):
    """Someone who opened the provider's contact, shown to the owner so they know who may call."""

    id: UUID
    viewer_name: str
    company_name: str | None
    first_viewed_at: datetime
    last_viewed_at: datetime
    view_count: int

