"""Validation models for the local workforce hub."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.location import normalize_pincode
from app.features.auth.schemas import normalize_phone

AvailabilityValue = Literal["available", "busy", "offline"]
RateUnit = Literal["hour", "day", "month"]
HireStatusValue = Literal["pending", "accepted", "declined", "cancelled", "completed"]
MAX_SKILLS = 25


def clean_list(values: list[str], limit: int, max_len: int = 60) -> list[str]:
    """Trim, collapse spaces, drop blanks and case-insensitive duplicates (first spelling wins)."""
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = " ".join((value or "").split())[:max_len]
        if item and item.lower() not in seen:
            seen.add(item.lower())
            result.append(item)
    return result[:limit]


def blank_to_none(value):
    return (value.strip() or None) if isinstance(value, str) else value


class WorkerFields(BaseModel):
    """Profile fields a worker (or an admin, for an unclaimed profile) can edit."""

    headline: str = Field(min_length=2, max_length=120, description="Main work, e.g. Cook, Driver, Sales staff")
    bio: str | None = Field(default=None, max_length=1500)
    city: str = Field(min_length=2, max_length=100)
    area: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=10)
    languages: list[str] = Field(default_factory=list, max_length=10)
    years_experience: int | None = Field(default=None, ge=0, le=70)
    skills: list[str] = Field(default_factory=list, max_length=MAX_SKILLS)
    # Pay range: rate_amount is the lower end (or the only amount), rate_max the optional upper end.
    rate_amount: int | None = Field(default=None, ge=0, le=10_000_000)
    rate_max: int | None = Field(default=None, ge=0, le=10_000_000)
    rate_unit: RateUnit | None = None
    rate_hidden: bool = False
    # Phone/WhatsApp number for direct contact; blank keeps the current one (default: the account phone).
    contact_phone: str | None = Field(default=None, max_length=30)
    show_contact: bool = False

    @field_validator("contact_phone")
    @classmethod
    def _contact_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("headline", "city")
    @classmethod
    def _collapse(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("bio", "area", mode="before")
    @classmethod
    def _optional(cls, value):
        return blank_to_none(value)

    @field_validator("skills")
    @classmethod
    def _skills(cls, values: list[str]) -> list[str]:
        return clean_list(values, MAX_SKILLS)

    @field_validator("pincode")
    @classmethod
    def _pincode(cls, value: str | None) -> str | None:
        return normalize_pincode(value)

    @field_validator("languages")
    @classmethod
    def _languages(cls, values: list[str]) -> list[str]:
        return clean_list(values, 10, 40)

    @model_validator(mode="after")
    def _rate(self):
        if self.rate_max is not None and self.rate_amount is None:
            self.rate_amount, self.rate_max = self.rate_max, None
        if self.rate_max is not None and self.rate_max == self.rate_amount:
            self.rate_max = None
        if self.rate_max is not None and self.rate_max < self.rate_amount:
            raise ValueError("The highest pay must be more than the lowest pay")
        if (self.rate_amount is None) != (self.rate_unit is None):
            raise ValueError("Enter both the pay and whether it is per hour, day or month")
        return self


class WorkerCreate(WorkerFields):
    adult_confirmed: bool

    @field_validator("adult_confirmed")
    @classmethod
    def _adult(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Workers must be 18 or older")
        return value


class WorkerUpdate(WorkerFields):
    pass


class AvailabilityUpdate(BaseModel):
    availability: AvailabilityValue
    busy_until: date | None = None

    @model_validator(mode="after")
    def _busy(self):
        if self.availability != "busy":
            self.busy_until = None
        return self


class LocationUpdate(BaseModel):
    """Just the place, set from the location picker without resubmitting the whole profile."""

    pincode: str
    city: str | None = Field(default=None, max_length=100)
    area: str | None = Field(default=None, max_length=100)

    @field_validator("pincode")
    @classmethod
    def _pincode(cls, value: str) -> str:
        normalized = normalize_pincode(value)
        if normalized is None:
            raise ValueError("Enter a valid 6-digit PIN code")
        return normalized

    @field_validator("city", "area", mode="before")
    @classmethod
    def _optional(cls, value):
        return blank_to_none(value)


class AdminWorkerCreate(WorkerCreate):
    """An admin adding a real local worker who isn't on RightConnect yet; adult_confirmed is the admin's check."""

    full_name: str = Field(min_length=2, max_length=120)
    contact_email: EmailStr | None = None

    @field_validator("contact_email", mode="before")
    @classmethod
    def _blank_email(cls, value):
        return blank_to_none(value)


class ClaimCodeOut(BaseModel):
    worker_id: UUID
    display_name: str
    claim_code: str
    expires_at: datetime


class ClaimWorkerPayload(BaseModel):
    code: str = Field(min_length=6, max_length=20)


class SkillOut(BaseModel):
    name: str
    verified: bool
    # Companies that confirmed this skill through the worker's work history.
    verified_by: list[str] = []
    self_declared: bool


class ExperienceOut(BaseModel):
    id: UUID
    employer_name: str
    organization_id: UUID | None
    role_title: str
    start_date: date | None
    end_date: date | None
    description: str | None
    skills: list[str]
    status: Literal["self", "pending", "verified", "declined"]
    added_by: Literal["worker", "employer"]
    # True only when confirmed by a company RightConnect has verified.
    employer_verified: bool
    verified_at: datetime | None


class WorkerReviewOut(BaseModel):
    reviewer_name: str
    rating: int
    body: str | None
    created_at: datetime


class WorkerSummary(BaseModel):
    id: UUID
    display_name: str
    headline: str
    city: str | None
    area: str | None
    pincode: str | None = None
    # 4 same area, 3 same district/city, 2 same state, 1 same region, 0 elsewhere; None when the searcher gave no location.
    nearness: int | None = None
    languages: list[str]
    years_experience: int | None
    # Null when the worker hides their pay (rate_hidden=True); the worker's own profile always has them.
    rate_amount: int | None
    rate_max: int | None = None
    rate_unit: RateUnit | None
    rate_hidden: bool = False
    # True when signed-in users can fetch a number to call/WhatsApp this worker.
    contact_available: bool = False
    availability: AvailabilityValue
    busy_until: date | None
    # The worker hasn't touched the light for a while, so "available" may be out of date.
    availability_stale: bool
    avatar_url: str | None
    average_rating: float
    review_count: int
    verified_skill_count: int
    skills: list[SkillOut]
    claimed: bool


class WorkerDetail(WorkerSummary):
    bio: str | None
    experiences: list[ExperienceOut]
    reviews: list[WorkerReviewOut]
    member_since: datetime | None


class MyWorkerProfile(WorkerDetail):
    contact_phone: str | None
    contact_email: str | None = None
    show_contact: bool = False
    self_skills: list[str]


class WorkerListResponse(BaseModel):
    results: list[WorkerSummary]
    total: int
    page: int
    page_size: int


class ExperienceCreate(BaseModel):
    role_title: str = Field(min_length=2, max_length=120)
    employer_name: str | None = Field(default=None, max_length=160)
    # A company on RightConnect; it is asked to confirm this job.
    organization_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=1000)
    skills: list[str] = Field(default_factory=list, max_length=15)

    @field_validator("employer_name", "description", mode="before")
    @classmethod
    def _optional(cls, value):
        return blank_to_none(value)

    @field_validator("skills")
    @classmethod
    def _skills(cls, values: list[str]) -> list[str]:
        return clean_list(values, 15)

    @model_validator(mode="after")
    def _check(self):
        if not self.organization_id and not self.employer_name:
            raise ValueError("Enter the employer's name or pick the company")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("End date must be after the start date")
        if self.start_date and self.start_date > date.today():
            raise ValueError("Start date can't be in the future")
        return self


class EmployerExperienceCreate(ExperienceCreate):
    """A company admin adding verified work history for someone who worked for them."""

    organization_id: UUID
    hire_id: UUID | None = None


class ExperienceConfirm(BaseModel):
    # The employer can correct the skills the worker listed; those become employer-verified.
    skills: list[str] | None = Field(default=None, max_length=15)
    role_title: str | None = Field(default=None, min_length=2, max_length=120)

    @field_validator("skills")
    @classmethod
    def _skills(cls, values: list[str] | None) -> list[str] | None:
        return clean_list(values, 15) if values is not None else None


class VerificationRequestOut(BaseModel):
    experience: ExperienceOut
    worker_id: UUID
    worker_name: str
    organization_name: str


class CompanyOption(BaseModel):
    organization_id: UUID
    name: str
    city: str | None
    verified: bool


class HireCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    details: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=160)
    start_date: date | None = None
    pay_offer: str | None = Field(default=None, max_length=80)
    # Hire on behalf of a company the caller administers, so the job can become verified work history.
    organization_id: UUID | None = None

    @field_validator("details", "location", "pay_offer", mode="before")
    @classmethod
    def _optional(cls, value):
        return blank_to_none(value)


class JobApply(BaseModel):
    message: str | None = Field(default=None, max_length=1000)

    @field_validator("message", mode="before")
    @classmethod
    def _optional(cls, value):
        return blank_to_none(value)


class Contact(BaseModel):
    name: str
    phone: str | None
    email: str | None


class HireOut(BaseModel):
    id: UUID
    worker_id: UUID
    worker_name: str
    worker_headline: str
    employer_name: str
    organization_id: UUID | None
    organization_name: str | None
    job_id: UUID | None
    initiated_by: Literal["employer", "worker"]
    title: str
    details: str | None
    location: str | None
    start_date: date | None
    pay_offer: str | None
    status: HireStatusValue
    created_at: datetime
    responded_at: datetime | None
    completed_at: datetime | None
    # 'worker' when the caller is the worker on this hire, 'employer' otherwise.
    my_side: Literal["worker", "employer"]
    # Shared only after the hire is accepted.
    counterpart_contact: Contact | None
    can_review: bool
    reviewed: bool
    can_add_experience: bool


class HiresResponse(BaseModel):
    as_worker: list[HireOut]
    as_employer: list[HireOut]


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    body: str | None = Field(default=None, max_length=1000)

    @field_validator("body", mode="before")
    @classmethod
    def _optional(cls, value):
        return blank_to_none(value)


class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    skill: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=2, max_length=100)
    area: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=10)
    openings: int = Field(default=1, ge=1, le=500)
    pay: str | None = Field(default=None, max_length=80)
    starts_on: date | None = None
    description: str | None = Field(default=None, max_length=2000)
    organization_id: UUID | None = None
    # Number workers can call/WhatsApp about this job; blank uses the poster's account phone.
    contact_phone: str | None = Field(default=None, max_length=30)
    show_contact: bool = False

    @field_validator("contact_phone")
    @classmethod
    def _contact_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("area", "pay", "description", mode="before")
    @classmethod
    def _optional(cls, value):
        return blank_to_none(value)

    @field_validator("pincode")
    @classmethod
    def _pincode(cls, value: str | None) -> str | None:
        return normalize_pincode(value)


class JobOut(BaseModel):
    id: UUID
    title: str
    skill: str
    city: str
    area: str | None
    pincode: str | None = None
    # 4 same area, 3 same district/city, 2 same state, 1 same region, 0 elsewhere; None when the searcher gave no location.
    nearness: int | None = None
    openings: int
    pay: str | None
    starts_on: date | None
    description: str | None
    status: Literal["open", "closed"]
    poster_name: str
    organization_name: str | None
    organization_verified: bool
    created_at: datetime
    mine: bool
    applied: bool
    contact_available: bool = False
    # Only for the poster.
    application_count: int | None


class DirectContact(BaseModel):
    """A phone number to call or WhatsApp; only returned to signed-in users when the owner allows it."""

    name: str
    phone: str | None
    email: str | None = None
    # Worker contacts only: the viewer's daily limit of new contacts and how many are left today (None = no limit).
    daily_limit: int | None = None
    left_today: int | None = None


class ContactViewOut(BaseModel):
    """Someone who viewed the worker's number, shown to the worker so they know who may call."""

    id: UUID
    viewer_name: str
    company_name: str | None
    first_viewed_at: datetime
    last_viewed_at: datetime
    view_count: int
    reported: bool


class ContactReport(BaseModel):
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def _collapse(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 3:
            raise ValueError("Tell us briefly what happened")
        return value


class AdminContactReportOut(BaseModel):
    id: UUID
    worker_id: UUID
    worker_name: str
    viewer_user_id: UUID
    viewer_name: str
    viewer_email: str
    viewer_blocked: bool
    view_count: int
    first_viewed_at: datetime
    reported_at: datetime
    report_reason: str | None
    # How many different workers reported this viewer.
    report_count: int = 1


class WorkerMerge(BaseModel):
    """Merge an admin-made worker profile into the worker's own account profile."""

    into_worker_id: UUID


class WorkerLinkOut(BaseModel):
    """A new personal link key, shown to the admin once so it can be sent to the worker."""

    worker_id: UUID
    display_name: str
    key: str
    contact_phone: str | None


class LinkProfile(BaseModel):
    """What a worker sees on their personal link page."""

    display_name: str
    headline: str
    city: str | None
    area: str | None
    availability: AvailabilityValue
    busy_until: date | None
    # True once the profile is attached to a Google/email account.
    connected: bool
    hires: list[HireOut]
    contact_views: list[ContactViewOut] = []


class AdminWorkerOut(BaseModel):
    id: UUID
    display_name: str
    headline: str
    city: str | None
    area: str | None
    pincode: str | None = None
    claim_status: Literal["unclaimed", "claimed"]
    contact_phone: str | None
    owner_email: str | None
    availability: AvailabilityValue
    review_count: int
    blocked_at: datetime | None
    blocked_reason: str | None
    deleted_at: datetime | None
    created_at: datetime
    has_link: bool = False
    # Another live worker profile uses the same phone number (e.g. the worker also signed up on their own).
    possible_duplicate: bool = False
    contact_email: str | None = None
    # For an admin-made profile: the worker's own account profile with the same phone, which it can be merged into.
    merge_into_id: UUID | None = None
    merge_into_email: str | None = None
