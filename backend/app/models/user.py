"""ORM model for an authenticated RightConnect user."""
import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, Select, String, Text, func, select, true
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(StrEnum):
    CUSTOMER = "customer"
    EXPERT = "expert"
    COMPANY_ADMIN = "company_admin"
    PLATFORM_ADMIN = "platform_admin"


class SubscriptionTier(StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    """Application profile associated with one external auth identity."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String)
    interests: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    # Off once the customer's need is finished; experts/companies then stop seeing them as an active lead.
    looking_for_help: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    need_fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Light public profile, shown to experts/companies the customer sent a request to.
    bio: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String)
    avatar_url: Mapped[str | None] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            create_type=False,
            values_callable=lambda roles: [role.value for role in roles],
        ),
        nullable=False,
    )
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(
            SubscriptionTier,
            name="subscription_tier",
            create_type=False,
            values_callable=lambda tiers: [tier.value for tier in tiers],
        ),
        nullable=False,
        default=SubscriptionTier.FREE,
        server_default=SubscriptionTier.FREE.value,
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Soft delete: the row stays until a purge job runs, but the login/email are free to sign up again.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def active_user_by_auth_id(auth_user_id: uuid.UUID) -> Select[tuple[User]]:
    """The caller's live (not soft-deleted) account."""
    return select(User).where(User.auth_user_id == auth_user_id, User.deleted_at.is_(None))