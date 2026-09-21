"""Validation models owned by the marketplace discovery feature."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


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


class ProfileListResponse(BaseModel):
    """Paged list of marketplace profiles."""

    results: list[ProfileSummary]
    total: int


class ReviewSummary(BaseModel):
    """A single review shown on a profile's detail page."""

    reviewer_name: str
    rating: int
    body: str
    created_at: datetime


class ProfileDetail(ProfileSummary):
    """Full profile detail including bio and reviews, for the profile preview page."""

    bio: str | None
    reviews: list[ReviewSummary]

