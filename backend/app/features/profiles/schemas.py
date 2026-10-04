"""Validation models for owners editing their expert/company profile."""
from datetime import date, time
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, field_validator, model_validator

from app.core.links import normalize_url

TeamSize = Literal["1-10", "11-50", "51-200", "201-500", "500+"]


def _http_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return normalize_url(value)


OptionalLink = Annotated[str | None, Field(max_length=500), AfterValidator(_http_url)]


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
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    team_size: TeamSize | None = None

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
    """Any web link; the platform (Instagram, YouTube, ...) is detected when not given."""

    platform: str | None = Field(default=None, max_length=40)
    url: Annotated[str, Field(min_length=3, max_length=500), AfterValidator(normalize_url)]


class SocialLinksUpdate(BaseModel):
    links: list[SocialLinkIn] = Field(max_length=10)


class ExperienceIn(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    organization: str = Field(min_length=1, max_length=160)
    location: str | None = Field(default=None, max_length=100)
    start_date: date
    # None = current role.
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _order(self) -> "ExperienceIn":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("End date must be after the start date")
        return self


class ExperienceOut(ExperienceIn):
    id: UUID


class EducationIn(BaseModel):
    school: str = Field(min_length=2, max_length=160)
    degree: str | None = Field(default=None, max_length=160)
    field_of_study: str | None = Field(default=None, max_length=160)
    start_year: int | None = Field(default=None, ge=1900, le=2100)
    end_year: int | None = Field(default=None, ge=1900, le=2100)
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _order(self) -> "EducationIn":
        if self.start_year and self.end_year and self.end_year < self.start_year:
            raise ValueError("End year must be after the start year")
        return self


class EducationOut(EducationIn):
    id: UUID


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
    founded_year: int | None = None
    team_size: str | None = None
    social_links: list[SocialLinkOut]
    experiences: list[ExperienceOut] = []
    educations: list[EducationOut] = []
    credentials: list[CredentialOut]
    offerings: list[OfferingOut]
    availability: list[AvailabilityWindow]
    plan: Literal["pro", "enterprise"]
    plan_active: bool
    limits: PlanLimits
