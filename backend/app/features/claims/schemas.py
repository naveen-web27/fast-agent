"""Validation models for admin-created company listings and their ownership claims."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.links import normalize_url
from app.features.auth.schemas import normalize_phone


class UnclaimedListingCreate(BaseModel):
    """What a platform admin enters for a real local business that hasn't joined yet."""

    company_name: str = Field(min_length=2, max_length=160)
    primary_service: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    website: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=30)

    @field_validator("company_name", "primary_service", "city")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Enter at least 2 characters")
        return value

    @field_validator("description")
    @classmethod
    def _blank_description(cls, value: str | None) -> str | None:
        return (value.strip() or None) if value else None

    @field_validator("website")
    @classmethod
    def _website(cls, value: str | None) -> str | None:
        return normalize_url(value) if value and value.strip() else None

    @field_validator("contact_phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)


class UnclaimedListingOut(BaseModel):
    """Public view of a claimable listing; the admin-only contact details are never included."""

    profile_id: UUID
    organization_id: UUID
    name: str
    headline: str
    city: str | None
    website_url: str | None
    claim_status: Literal["unclaimed", "claimed"]


class ClaimCodeRequest(BaseModel):
    profile_id: UUID
    email: EmailStr


class ClaimSubmit(BaseModel):
    profile_id: UUID
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")
    phone: str | None = Field(default=None, max_length=30)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("note")
    @classmethod
    def _note(cls, value: str | None) -> str | None:
        return (value.strip() or None) if value else None


class MyClaimOut(BaseModel):
    id: UUID
    profile_id: UUID | None
    organization_name: str
    business_email: str
    status: Literal["pending", "approved", "rejected"]
    review_reason: str | None
    created_at: datetime
    reviewed_at: datetime | None


class AdminClaimOut(BaseModel):
    id: UUID
    organization_id: UUID
    profile_id: UUID | None
    organization_name: str
    city: str | None
    listing_contact_email: str | None
    listing_contact_phone: str | None
    claimant_name: str
    claimant_email: str
    business_email: str
    email_matches_listing: bool
    phone: str | None
    note: str | None
    status: Literal["pending", "approved", "rejected"]
    review_reason: str | None
    created_at: datetime
    reviewed_at: datetime | None


class ClaimRejection(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
