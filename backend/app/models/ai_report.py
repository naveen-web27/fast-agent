"""Private AI reports, consented family details, and durable rate budgets."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import CHAR, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AIReport(Base):
    __tablename__ = "ai_reports"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'completed', 'failed')"),
        CheckConstraint("language IN ('ta', 'en')"),
        CheckConstraint("tier = 'basic'"),
        CheckConstraint("attempt_count BETWEEN 1 AND 5"),
        CheckConstraint("generation_attempt = attempt_count"),
        CheckConstraint("token_hash ~ '^[0-9a-f]{64}$'"),
        Index("ix_ai_reports_user_created", "user_id", "created_at"),
        Index("ix_ai_reports_created", "created_at"),
        Index("ix_ai_reports_pending", "last_attempt_at", postgresql_where=text("status = 'pending'")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    service_type: Mapped[str] = mapped_column(String(40), nullable=False)
    inputs: Mapped[dict] = mapped_column("user_inputs", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    calculated_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    variants: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", server_default="pending")
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="ta", server_default="ta")
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    tier: Mapped[str] = mapped_column(String(16), nullable=False, default="basic", server_default="basic")
    engine_version: Mapped[str] = mapped_column(String(40), nullable=False, default="1.0.0", server_default="1.0.0")
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False, default="1.0.0", server_default="1.0.0")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    generation_attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    last_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())


class AIReportFamilyMember(Base):
    __tablename__ = "ai_report_family_members"
    __table_args__ = (CheckConstraint("char_length(label) BETWEEN 1 AND 80"), Index("ix_ai_report_family_user", "user_id"))

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())


class AIReportUsage(Base):
    __tablename__ = "ai_report_usage"
    __table_args__ = (CheckConstraint("count >= 0"), Index("ix_ai_report_usage_expires", "expires_at"))

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)