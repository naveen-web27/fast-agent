"""ORM models for marketplace profiles: experts, companies, and their services."""
import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import ARRAY, Boolean, DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, Text, func
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
    years_experience: Mapped[int | None] = mapped_column(SmallInteger)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    avatar_url: Mapped[str | None] = mapped_column(String)
    verification: Mapped[VerificationStatus] = mapped_column(
        _enum(VerificationStatus, "verification_status"), nullable=False, default=VerificationStatus.PENDING
    )
    average_rating: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(nullable=False, default=0)
    response_minutes: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    services: Mapped[list[Service]] = relationship(secondary=ProfileService.__table__, lazy="selectin")
