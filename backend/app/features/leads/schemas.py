"""Validation models for admin lead management."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.features.leads.parsing import clean_phone

LeadType = Literal["unknown", "customer", "expert", "company", "worker"]
LeadStatus = Literal["new", "contacted", "interested", "follow_up", "not_interested", "signed_up"]


def _blank_to_none(value):
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


class LeadFields(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    business_name: str | None = Field(default=None, max_length=160)
    service: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=100)
    source: str | None = Field(default=None, max_length=80)
    follow_up_on: date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("full_name", "business_name", "service", "city", "source", "notes", "follow_up_on", mode="before")
    @classmethod
    def _blank(cls, value):
        return _blank_to_none(value)


class LeadCreate(LeadFields):
    phone: str = Field(min_length=6, max_length=30)
    lead_type: LeadType = "unknown"
    status: LeadStatus = "new"

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str) -> str:
        return clean_phone(value)


class LeadUpdate(LeadFields):
    """Only the fields sent are changed."""

    phone: str | None = Field(default=None, min_length=6, max_length=30)
    lead_type: LeadType | None = None
    status: LeadStatus | None = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        return clean_phone(value) if value is not None else None


class LeadImportRow(BaseModel):
    """One pasted spreadsheet row; values are free text and cleaned per row, so one bad row doesn't stop the rest."""

    phone: str | None = Field(default=None, max_length=60)
    full_name: str | None = Field(default=None, max_length=300)
    lead_type: str | None = Field(default=None, max_length=120)
    business_name: str | None = Field(default=None, max_length=300)
    service: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, max_length=120)
    follow_up_on: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)
    source: str | None = Field(default=None, max_length=120)


class LeadImport(BaseModel):
    rows: list[LeadImportRow] = Field(min_length=1, max_length=2000)
    # Used for rows without their own source, e.g. "WhatsApp ad – Nov 2026".
    source: str | None = Field(default=None, max_length=80)


class LeadImportError(BaseModel):
    row: int
    message: str


class LeadImportResult(BaseModel):
    created: int
    # Already a lead: empty fields were filled in, nothing was overwritten.
    updated: int
    errors: list[LeadImportError]


class ProfileMatch(BaseModel):
    """Something on RightConnect that uses this lead's phone number."""

    kind: Literal["account", "worker", "company", "expert"]
    label: str


class LeadOut(BaseModel):
    id: UUID
    full_name: str | None
    phone: str
    lead_type: LeadType
    business_name: str | None
    service: str | None
    city: str | None
    source: str | None
    status: LeadStatus
    follow_up_on: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    # Empty when no account, worker or business on RightConnect has this number yet.
    matches: list[ProfileMatch] = []
