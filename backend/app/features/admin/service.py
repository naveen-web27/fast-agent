"""Admin review workflow for verifying expert and company marketplace profiles."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Organization, Profile, VerificationStatus
from app.models.user import User


class ProfileNotFoundError(Exception):
    """Raised when the target profile does not exist."""


async def list_profiles_for_review(session: AsyncSession, verification: str | None) -> list[dict]:
    """Return marketplace profiles for admin review, optionally filtered by verification status."""
    query = select(Profile, User.email).outerjoin(User, User.id == Profile.user_id)
    if verification:
        query = query.where(Profile.verification == VerificationStatus(verification))
    rows = (await session.execute(query.order_by(Profile.created_at.desc()))).all()
    return [
        {
            "id": profile.id,
            "kind": profile.kind.value,
            "display_name": profile.display_name,
            "headline": profile.headline,
            "city": profile.city,
            "verification": profile.verification.value,
            "owner_email": email,
            "organization_id": profile.organization_id,
        }
        for profile, email in rows
    ]


async def set_profile_verification(session: AsyncSession, profile_id: UUID, decision: VerificationStatus) -> None:
    """Mark a profile (and its organization, if it belongs to one) as verified or rejected."""
    profile = await session.get(Profile, profile_id)
    if profile is None:
        raise ProfileNotFoundError("Profile not found")
    profile.verification = decision
    if profile.organization_id is not None:
        organization = await session.get(Organization, profile.organization_id)
        if organization is not None:
            organization.verification = decision
    await session.commit()
