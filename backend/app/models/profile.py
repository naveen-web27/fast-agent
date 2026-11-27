"""ORM models for marketplace profiles: experts, companies, and their services."""
import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import ARRAY, Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import SubscriptionTier


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ProfileKind(StrEnum):
    EXPERT = "expert"
    COMPANY = "company"


class ClaimStatus(StrEnum):
    UNCLAIMED = "unclaimed"
    CLAIMED = "claimed"


def _enum(enum_cls: type[StrEnum], name: str) -> Enum:
    return Enum(enum_cls, name=name, create_type=False, values_callable=lambda members: [m.value for m in members])


class Organization(Base):
    """A company that offers services through one or more company profiles."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    verification: Mapped[VerificationStatus] = mapped_column(
        _enum(VerificationStatus, "verification_status"), nullable=False, default=VerificationStatus.PENDING
    )
    email_domain_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        _enum(SubscriptionTier, "subscription_tier"), nullable=False, default=SubscriptionTier.FREE
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Admin-added listings stay 'unclaimed' (no members) until an owner's claim is approved.
    claim_status: Mapped[str] = mapped_column(String, nullable=False, default=ClaimStatus.CLAIMED.value)
    # Admin-only contact details used to match and follow up on claims; never shown publicly.
    contact_email: Mapped[str | None] = mapped_column(String)
    contact_phone: Mapped[str | None] = mapped_column(String)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Service(Base):
    """A bookable service category, e.g. health insurance advice."""

    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)


class ProfileService(Base):
    """Join table linking a profile to the services it offers."""

    __tablename__ = "profile_services"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), primary_key=True
    )


class Profile(Base):
    """A searchable marketplace listing for an expert or a company."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE")
    )
    kind: Mapped[ProfileKind] = mapped_column(_enum(ProfileKind, "profile_kind"), nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    headline: Mapped[str] = mapped_column(String, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String)
    # 6-digit Indian PIN code; drives "nearest first" ranking (see app/core/location.py).
    pincode: Mapped[str | None] = mapped_column(String)
    # Area name chosen in the location picker, e.g. "Idappadi" (city holds the district, e.g. "Salem").
    locality: Mapped[str | None] = mapped_column(String)
    years_experience: Mapped[int | None] = mapped_column(SmallInteger)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    # Owner-chosen search words; matched by search but not shown on the card.
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    avatar_url: Mapped[str | None] = mapped_column(String)
    verification: Mapped[VerificationStatus] = mapped_column(
        _enum(VerificationStatus, "verification_status"), nullable=False, default=VerificationStatus.PENDING
    )
    average_rating: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(nullable=False, default=0)
    response_minutes: Mapped[int | None] = mapped_column()
    # Owner-controlled: whether the "N clients resolved" badge is shown publicly on this profile.
    show_resolved_count: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # "View contact": signed-in users see the phone/WhatsApp/email (logged in profile_contact_views).
    # Blank phone/email fall back to the expert's account, or for companies the listing's and an admin's.
    contact_phone: Mapped[str | None] = mapped_column(String)
    contact_email: Mapped[str | None] = mapped_column(String)
    show_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Pro plan for expert profiles; company profiles use their organization's plan instead.
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        _enum(SubscriptionTier, "subscription_tier"), nullable=False, default=SubscriptionTier.FREE
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    intro_video_url: Mapped[str | None] = mapped_column(String)
    portfolio_url: Mapped[str | None] = mapped_column(String)
    founded_year: Mapped[int | None] = mapped_column(SmallInteger)
    team_size: Mapped[str | None] = mapped_column(String)
    view_count: Mapped[int] = mapped_column(nullable=False, default=0)
    # Set by a platform admin; blocked profiles are hidden from discovery and can't receive new requests.
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    services: Mapped[list[Service]] = relationship(secondary=ProfileService.__table__, lazy="selectin")


class ProfileContactView(Base):
    """Someone signed in viewed this expert's/company's contact; new rows share the daily limit with worker contacts."""

    __tablename__ = "profile_contact_views"
    __table_args__ = (UniqueConstraint("profile_id", "viewer_user_id", name="profile_contact_views_once"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    viewer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    first_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
