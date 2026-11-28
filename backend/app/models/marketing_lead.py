"""ORM models for RightConnect Marketing (posters + ads agency): client leads and their follow-up history."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketingLead(Base):
    __tablename__ = "marketing_leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str | None] = mapped_column(String)
    # E.164 (+919876543210); unique, so the same number is never added twice.
    phone: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    business_name: Mapped[str | None] = mapped_column(String)
    business_type: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    service: Mapped[str | None] = mapped_column(String)
    source: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="new")
    # Whole rupees. Money received is the sum of this lead's payment activities.
    deal_amount: Mapped[int | None] = mapped_column(Integer)
    follow_up_on: Mapped[date | None] = mapped_column(Date)
    next_action: Mapped[str | None] = mapped_column(String)
    rating: Mapped[int | None] = mapped_column(SmallInteger)
    feedback: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarketingLeadActivity(Base):
    __tablename__ = "marketing_lead_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_leads.id", ondelete="CASCADE"), nullable=False
    )
    # note, call, whatsapp, meeting, payment (amount required) or status (written automatically on status change).
    kind: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
