"""ORM models for the rich-profile extras: credentials and the priced service catalogue."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.profile import VerificationStatus, _enum


class Credential(Base):
    """A licence or certification an expert/company claims; admins verify it separately."""

    __tablename__ = "credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    issuing_body: Mapped[str | None] = mapped_column(String)
    credential_number: Mapped[str | None] = mapped_column(String)
    document_url: Mapped[str | None] = mapped_column(String)
    verification: Mapped[VerificationStatus] = mapped_column(
        _enum(VerificationStatus, "verification_status"), nullable=False, default=VerificationStatus.PENDING
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProfileOffering(Base):
    """One priced item in a profile's service catalogue, e.g. "Family floater review · ₹999-₹2,499"."""

    __tablename__ = "profile_offerings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_min_inr: Mapped[int | None] = mapped_column(Integer)
    price_max_inr: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
