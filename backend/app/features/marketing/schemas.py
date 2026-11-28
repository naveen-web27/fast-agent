"""Validation models for RightConnect Marketing lead management."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.features.leads.parsing import clean_phone

Status = Literal["new", "called", "interested", "converted", "in_progress", "completed", "lost"]
ActivityKind = Literal["note", "call", "whatsapp", "meeting", "payment", "status"]
ManualKind = Literal["note", "call", "whatsapp", "meeting", "payment"]
PaymentState = Literal["paid", "partial", "due", "none"]

TEXT_FIELDS = ("full_name", "business_name", "business_type", "city", "service", "source", "next_action", "feedback", "notes")


def _blank_to_none(value):
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


class LeadFields(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    business_name: str | None = Field(default=None, max_length=160)
    business_type: str | None = Field(default=None, max_length=80)
    city: str | None = Field(default=None, max_length=100)
    service: str | None = Field(default=None, max_length=120)
    source: str | None = Field(default=None, max_length=80)
    deal_amount: int | None = Field(default=None, ge=0, le=100_000_000)
    follow_up_on: date | None = None
    next_action: str | None = Field(default=None, max_length=200)
    rating: int | None = Field(default=None, ge=1, le=5)
    feedback: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator(*TEXT_FIELDS, "follow_up_on", "deal_amount", "rating", mode="before")
    @classmethod
    def _blank(cls, value):
        return _blank_to_none(value)


class LeadCreate(LeadFields):
    phone: str = Field(min_length=6, max_length=30)
    status: Status = "new"

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str) -> str:
        return clean_phone(value)


class LeadUpdate(LeadFields):
    """Only the fields sent are changed; send null to clear an optional field."""

    phone: str | None = Field(default=None, min_length=6, max_length=30)
    status: Status | None = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        return clean_phone(value) if value is not None else None


class LeadOut(BaseModel):
    id: UUID
    full_name: str | None
    phone: str
    business_name: str | None
    business_type: str | None
    city: str | None
    service: str | None
    source: str | None
    status: Status
    deal_amount: int | None
    paid_amount: int
    payment: PaymentState
    follow_up_on: date | None
    next_action: str | None
    rating: int | None
    feedback: str | None
    notes: str | None
    last_activity_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ActivityCreate(BaseModel):
    kind: ManualKind
    text: str | None = Field(default=None, max_length=2000)
    amount: int | None = Field(default=None, gt=0, le=100_000_000)
    # Optional next follow-up saved with the entry, e.g. "No answer, call tomorrow".
    follow_up_on: date | None = None

    @field_validator("text", "follow_up_on", mode="before")
    @classmethod
    def _blank(cls, value):
        return _blank_to_none(value)

    @model_validator(mode="after")
    def _check_kind(self):
        if self.kind == "payment" and self.amount is None:
            raise ValueError("Enter the amount received.")
        if self.kind != "payment" and self.amount is not None:
            raise ValueError("Only payments have an amount.")
        if self.kind != "payment" and not self.text:
            raise ValueError("Write what happened.")
        return self


class ActivityOut(BaseModel):
    id: UUID
    lead_id: UUID
    kind: ActivityKind
    text: str | None
    amount: int | None
    created_by_name: str | None
    created_at: datetime


class ActivityResult(BaseModel):
    """The saved entry (None after a delete) and the lead as it is now (status, paid amount, follow-up)."""

    activity: ActivityOut | None
    lead: LeadOut
