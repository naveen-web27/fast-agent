"""Payment records used to reconcile Razorpay orders and legacy links."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    plan: Mapped[str] = mapped_column(String, nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    razorpay_link_id: Mapped[str | None] = mapped_column(String, unique=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String, unique=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String, unique=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))