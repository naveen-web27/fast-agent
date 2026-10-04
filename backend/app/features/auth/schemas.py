"""Validation models owned by the authentication and onboarding feature."""
import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.links import normalize_url

Role = Literal["customer", "expert", "company_admin", "platform_admin"]
OnboardingRole = Literal["customer", "expert", "company_admin"]


def normalize_phone(value: str | None) -> str | None:
    """Return the number in E.164 form (e.g. +919876543210), or raise if it looks mistyped."""
    if value is None:
        return None
    compact = re.sub(r"[\s()-]", "", value)
    if not compact:
        return None
    if compact.startswith("+91"):
        if not re.fullmatch(r"\+91[6-9]\d{9}", compact):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
    elif not re.fullmatch(r"\+[1-9]\d{6,14}", compact):
        raise ValueError("Enter the mobile number with its country code, e.g. +91 9876543210")
    return compact


class OnboardingRequest(BaseModel):
    """Profile information collected after an identity provider verified the user."""

    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    role: OnboardingRole
    city: str | None = Field(default=None, max_length=100)
    preferred_language: str | None = Field(default=None, max_length=50)
    interest: str | None = Field(default=None, max_length=120)
    interests: list[str] = Field(default_factory=list, max_length=20)
    primary_service: str | None = Field(default=None, max_length=120)
    years_experience: int | None = Field(default=None, ge=0, le=80)
    credential_number: str | None = Field(default=None, max_length=160)
    company_name: str | None = Field(default=None, max_length=160)
    work_email: EmailStr | None = None
    website: str | None = Field(default=None, max_length=255)
    business_registration: str | None = Field(default=None, max_length=160)

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("interests")
    @classmethod
    def _clean_interests(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip()[:120] for value in values if value and value.strip()]
        return list({value.lower(): value for value in cleaned}.values())


class UserResponse(BaseModel):
    """Onboarding result returned to the frontend."""

    id: UUID
    full_name: str
    email: EmailStr
    role: Role
    interests: list[str]
    onboarding_status: Literal["complete", "verification_pending"]
    subscription_tier: Literal["free", "pro", "enterprise"] = "free"
    subscription_expires_at: str | None = None
    looking_for_help: bool = True
    need_fulfilled_at: datetime | None = None
    bio: str | None = None
    city: str | None = None
    avatar_url: str | None = None
    member_since: datetime | None = None


class MyProfileUpdate(BaseModel):
    """The light customer profile. Only the fields sent are changed."""

    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    bio: str | None = Field(default=None, max_length=1000)
    city: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=500)

    @field_validator("avatar_url")
    @classmethod
    def _avatar(cls, value: str | None) -> str | None:
        return normalize_url(value) if value and value.strip() else None


class ExpertProfileRequest(BaseModel):
    """Fields needed to add a personal expert listing to an existing account."""

    headline: str = Field(min_length=2, max_length=160)
    bio: str | None = Field(default=None, max_length=2000)
    city: str | None = Field(default=None, max_length=100)
    primary_service: str | None = Field(default=None, max_length=120)
    years_experience: int | None = Field(default=None, ge=0, le=80)
    languages: list[str] = Field(default_factory=list)


class ExpertProfileSummary(BaseModel):
    id: UUID
    headline: str
    verification: Literal["pending", "verified", "rejected"]
    average_rating: float
    review_count: int
    resolved_clients_count: int
    show_resolved_count: bool
    plan_active: bool = False
    plan_expires_at: datetime | None = None


class CompanyRequest(BaseModel):
    """Fields needed to register a new company and become its first admin."""

    company_name: str = Field(min_length=2, max_length=160)
    work_email: EmailStr
    website: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    business_registration: str | None = Field(default=None, max_length=160)


class CompanyMembership(BaseModel):
    organization_id: UUID
    profile_id: UUID | None
    name: str
    member_role: Literal["admin", "staff"]
    verification: Literal["pending", "verified", "rejected"]
    email_domain_verified: bool
    resolved_clients_count: int
    show_resolved_count: bool
    plan_active: bool = False
    plan_expires_at: datetime | None = None


class IdentitiesResponse(BaseModel):
    """Everything this auth identity can act as: customer, expert, and/or company admin."""

    user: UserResponse
    expert_profile: ExpertProfileSummary | None
    companies: list[CompanyMembership]


class DomainOtpSendRequest(BaseModel):
    organization_id: UUID
    email: EmailStr


class DomainOtpVerifyRequest(BaseModel):
    organization_id: UUID
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class InterestRequest(BaseModel):
    interest: str = Field(min_length=1, max_length=120)


class InterestsResponse(BaseModel):
    interests: list[str]


class LookingRequest(BaseModel):
    """Turn the customer's 'looking for help' switch on (with a new need) or off."""

    looking: bool
    need: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def _need_when_looking(self) -> "LookingRequest":
        self.need = (self.need or "").strip() or None
        if self.looking and self.need is None:
            raise ValueError("Tell us what you need help with now")
        return self
