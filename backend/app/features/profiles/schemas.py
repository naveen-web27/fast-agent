"""Validation models for owners editing their expert/company profile."""
import re
from datetime import time
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, field_validator, model_validator


def _http_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    value = value.strip()
    if not re.fullmatch(r"https?://\S+", value, flags=re.IGNORECASE):
        raise ValueError("Enter a full link starting with https://")
    return value


def _required_http_url(value: str) -> str:
    cleaned = _http_url(value)
    if cleaned is None:
        raise ValueError("Enter a link")
    return cleaned


OptionalLink = Annotated[str | None, Field(max_length=500), AfterValidator(_http_url)]
Link = Annotated[str, Field(max_length=500), AfterValidator(_required_http_url)]


class ProfileUpdate(BaseModel):
    """Only the fields sent are changed. Intro video and portfolio need the paid plan."""

    display_name: str | None = Field(default=None, min_length=2, max_length=160)
    headline: str | None = Field(default=None, min_length=2, max_length=160)
    bio: str | None = Field(default=None, max_length=2000)
    city: str | None = Field(default=None, max_length=100)
    years_experience: int | None = Field(default=None, ge=0, le=80)
    languages: list[str] | None = Field(default=None, max_length=10)
    avatar_url: OptionalLink = None
    services: list[str] | None = Field(default=None, max_length=10)
    keywords: list[str] | None = Field(default=None, max_length=20)
    intro_video_url: OptionalLink = None
    portfolio_url: OptionalLink = None

    @field_validator("languages", "services")
    @classmethod
    def _clean_list(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip()[:120] for value in values if value and value.strip()]
        return list({value.lower(): value for value in cleaned}.values())

    @field_validator("keywords")
    @classmethod
    def _clean_keywords(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned = [" ".join(value.split()).lower()[:40] for value in values if value and value.strip()]
        return list(dict.fromkeys(cleaned))


class SocialLinkIn(BaseModel):
    platform: str = Field(min_length=1, max_length=40)
    url: Link


class SocialLinksUpdate(BaseModel):
    links: list[SocialLinkIn] = Field(max_length=10)


class CredentialIn(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    issuing_body: str | None = Field(default=None, max_length=160)
    credential_number: str | None = Field(default=None, max_length=160)
    document_url: OptionalLink = None


class CredentialOut(BaseModel):
    id: UUID
    title: str
    issuing_body: str | None
    credential_number: str | None
    document_url: str | None
    verification: Literal["pending", "verified", "rejected"]


class OfferingIn(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    price_min_inr: int | None = Field(default=None, ge=0, le=100_000_000)
    price_max_inr: int | None = Field(default=None, ge=0, le=100_000_000)

    @model_validator(mode="after")
    def _range(self) -> "OfferingIn":
        if self.price_min_inr is not None and self.price_max_inr is not None and self.price_max_inr < self.price_min_inr:
            raise ValueError("Maximum price must be at least the minimum price")
        return self


class OfferingOut(BaseModel):
    id: UUID
    title: str
    description: str | None
    price_min_inr: int | None
    price_max_inr: int | None


class AvailabilityWindow(BaseModel):
    """Weekly window in India time. weekday: 0 = Monday ... 6 = Sunday."""

    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def _order(self) -> "AvailabilityWindow":
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        return self


class AvailabilityUpdate(BaseModel):
    windows: list[AvailabilityWindow] = Field(max_length=28)


class SocialLinkOut(BaseModel):
    platform: str
    url: str


class PlanLimits(BaseModel):
    social_links: int
    credentials: int
    offerings: int


class ManagedProfile(BaseModel):
    """Everything the owner can edit, plus what their plan unlocks."""

    id: UUID
    kind: Literal["expert", "company"]
    display_name: str
    headline: str
    bio: str | None
    city: str | None
    years_experience: int | None
    languages: list[str]
    avatar_url: str | None
    services: list[str]
    keywords: list[str]
    # Everyday words customers use for these services, offered as one-tap additions.
    suggested_keywords: list[str]
    intro_video_url: str | None
    portfolio_url: str | None
    social_links: list[SocialLinkOut]
    credentials: list[CredentialOut]
    offerings: list[OfferingOut]
    availability: list[AvailabilityWindow]
    plan: Literal["pro", "enterprise"]
    plan_active: bool
    limits: PlanLimits
