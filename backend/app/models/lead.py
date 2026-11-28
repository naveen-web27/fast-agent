"""ORM model for sales leads: people who enquired (e.g. on WhatsApp from ads), tracked by admins until they sign up."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str | None] = mapped_column(String)
    # E.164 (+919876543210); unique, so the same number is never added twice.
    phone: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    lead_type: Mapped[str] = mapped_column(String, nullable=False, default="unknown")
    business_name: Mapped[str | None] = mapped_column(String)
    service: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    source: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="new")
    follow_up_on: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
