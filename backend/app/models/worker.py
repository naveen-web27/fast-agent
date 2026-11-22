"""ORM models for the local workforce hub: workers (service partners), their work history, hires, reviews and job posts."""
import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import ARRAY, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Availability(StrEnum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class ExperienceStatus(StrEnum):
    # Worker-added, no employer on RightConnect to confirm it.
    SELF = "self"
    # Worker-added against a company on RightConnect; waiting for that company to confirm.
    PENDING = "pending"
    # Confirmed (or added) by an admin of the employer company.
    VERIFIED = "verified"
    DECLINED = "declined"


class HireStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class WorkerProfile(Base):
    """A searchable worker. user_id is empty for admin-added profiles until the worker claims them."""

    __tablename__ = "worker_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    headline: Mapped[str] = mapped_column(String, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String)
    area: Mapped[str | None] = mapped_column(String)
    # 6-digit Indian PIN code; drives "nearest first" ranking (see app/core/location.py).
    pincode: Mapped[str | None] = mapped_column(String)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    years_experience: Mapped[int | None] = mapped_column(SmallInteger)
    # Self-declared skills; employer-verified skills come from verified work history.
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    # Pay range: rate_amount is the lower end, rate_max the optional upper end.
    rate_amount: Mapped[int | None] = mapped_column(Integer)
    rate_max: Mapped[int | None] = mapped_column(Integer)
    rate_unit: Mapped[str | None] = mapped_column(String)
    # Hidden pay is shown only to the worker; everyone else sees "Pay: discuss".
    rate_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Lets signed-in users view the worker's phone/email ("View contact", logged in worker_contact_views).
    show_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    availability: Mapped[str] = mapped_column(String, nullable=False, default=Availability.AVAILABLE.value)
    busy_until: Mapped[date | None] = mapped_column(Date)
    availability_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Private: shared only with an employer whose hire the worker accepted.
    contact_phone: Mapped[str | None] = mapped_column(String)
    # Collected by admins for workers without an account; self-signed workers use their account email.
    contact_email: Mapped[str | None] = mapped_column(String)
    avatar_url: Mapped[str | None] = mapped_column(String)
    claim_status: Mapped[str] = mapped_column(String, nullable=False, default="claimed")
    claim_code_hash: Mapped[str | None] = mapped_column(String)
    claim_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Personal link for workers who can't use Google/email sign-in; only the key's hash is stored.
    access_key_hash: Mapped[str | None] = mapped_column(String)
    access_key_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    adult_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    average_rating: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkerExperience(Base):
    """One job in a worker's history, e.g. 6 months as sales staff at a dress shop."""

    __tablename__ = "worker_experiences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worker_profiles.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    employer_name: Mapped[str] = mapped_column(String, nullable=False)
    role_title: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    status: Mapped[str] = mapped_column(String, nullable=False, default=ExperienceStatus.SELF.value)
    added_by: Mapped[str] = mapped_column(String, nullable=False, default="worker")
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hire_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("worker_hires.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JobPost(Base):
    """A shift or opening, e.g. a hotel needing 3 waiters this weekend."""

    __tablename__ = "job_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poster_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    skill: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    area: Mapped[str | None] = mapped_column(String)
    pincode: Mapped[str | None] = mapped_column(String)
    openings: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    pay: Mapped[str | None] = mapped_column(String)
    starts_on: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    # Number workers can call/WhatsApp about the job (shown to signed-in users when show_contact is on).
    contact_phone: Mapped[str | None] = mapped_column(String)
    show_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkerHire(Base):
    """A hire request between an employer and a worker; also used for a worker's application to a job post."""

    __tablename__ = "worker_hires"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worker_profiles.id", ondelete="CASCADE"), nullable=False
    )
    employer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Set when the employer hires on behalf of a company they administer.
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job_posts.id", ondelete="SET NULL"))
    # 'employer' = hire request waiting for the worker; 'worker' = job application waiting for the employer.
    initiated_by: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String)
    start_date: Mapped[date | None] = mapped_column(Date)
    pay_offer: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default=HireStatus.PENDING.value)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkerReview(Base):
    __tablename__ = "worker_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hire_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worker_hires.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worker_profiles.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkerContactView(Base):
    """Someone signed in viewed this worker's phone/email; new rows count toward their daily contact limit."""

    __tablename__ = "worker_contact_views"
    __table_args__ = (UniqueConstraint("worker_id", "viewer_user_id", name="worker_contact_views_once"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worker_profiles.id", ondelete="CASCADE"), nullable=False
    )
    viewer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    first_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_reason: Mapped[str | None] = mapped_column(Text)
