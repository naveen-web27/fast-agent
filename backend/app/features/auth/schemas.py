"""Validation models owned by the authentication and onboarding feature."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

Role = Literal["customer", "expert", "company_admin"]


class OnboardingRequest(BaseModel):
    """Profile information collected after an identity provider verified the user."""

    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    role: Role
    city: str | None = Field(default=None, max_length=100)
    preferred_language: str | None = Field(default=None, max_length=50)
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
    onboarding_status: Literal["complete", "verification_pending"]