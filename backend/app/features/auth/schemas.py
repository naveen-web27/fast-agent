"""Validation models owned by the authentication and onboarding feature."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

Role = Literal["customer", "expert", "company_admin", "platform_admin"]
OnboardingRole = Literal["customer", "expert", "company_admin"]


class OnboardingRequest(BaseModel):
    """Profile information collected after an identity provider verified the user."""

    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    role: OnboardingRole
    city: str | None = Field(default=None, max_length=100)
    preferred_language: str | None = Field(default=None, max_length=50)
    interest: str | None = Field(default=None, max_length=120)
    primary_service: str | None = Field(default=None, max_length=120)
    years_experience: int | None = Field(default=None, ge=0, le=80)
    credential_number: str | None = Field(default=None, max_length=160)
    company_name: str | None = Field(default=None, max_length=160)
    work_email: EmailStr | None = None
    website: str | None = Field(default=None, max_length=255)
    business_registration: str | None = Field(default=None, max_length=160)


class UserResponse(BaseModel):
    """Onboarding result returned to the frontend."""

    id: UUID
    full_name: str
    email: EmailStr
    role: Role
    interests: list[str]
    onboarding_status: Literal["complete", "verification_pending"]


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


class CompanyRequest(BaseModel):
    """Fields needed to register a new company and become its first admin."""

    company_name: str = Field(min_length=2, max_length=160)
    work_email: EmailStr
    website: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    business_registration: str | None = Field(default=None, max_length=160)


class CompanyMembership(BaseModel):
    organization_id: UUID
    name: str
    member_role: Literal["admin", "staff"]
    verification: Literal["pending", "verified", "rejected"]
    email_domain_verified: bool


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
