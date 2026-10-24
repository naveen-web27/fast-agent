"""Signed-in Thirumana porutham history and prepaid report packs."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import CHAR, Boolean, CheckConstraint, DateTime, Index, Integer, SmallInteger, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PoruthamHistory(Base):
    __tablename__ = "porutham_history"
    __table_args__ = (
        UniqueConstraint("auth_user_id", "couple_key"),
        CheckConstraint("level IN ('high', 'medium', 'low')"),
        CheckConstraint("kind IN ('kattam', 'jathagam')"),
        Index("ix_porutham_history_owner", "auth_user_id", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    # Supabase auth id, so Google sign-in is enough without marketplace onboarding.
    auth_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default="kattam", server_default="kattam")
    couple_key: Mapped[str] = mapped_column(CHAR(48), nullable=False)
    bride_name: Mapped[str] = mapped_column(String(100), nullable=False, default="", server_default="")
    groom_name: Mapped[str] = mapped_column(String(100), nullable=False, default="", server_default="")
    inputs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    level: Mapped[str] = mapped_column(String(6), nullable=False)
    stars_matched: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    kattam_matched: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    unlocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    report_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())


class PoruthamPack(Base):
    __tablename__ = "porutham_packs"
    __table_args__ = (
        CheckConstraint("amount_paise >= 100"),
        CheckConstraint("reports_total > 0"),
        CheckConstraint("reports_used BETWEEN 0 AND reports_total"),
        CheckConstraint("days > 0"),
        CheckConstraint("status IN ('pending', 'paid')"),
        Index("ix_porutham_packs_owner", "auth_user_id", "status", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    auth_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    razorpay_order_id: Mapped[str | None] = mapped_column(Text, unique=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(Text, unique=True)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    reports_total: Mapped[int] = mapped_column(Integer, nullable=False)
    reports_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False, default="pending", server_default="pending")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
