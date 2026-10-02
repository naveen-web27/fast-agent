"""Admin tools for verifying, blocking, and deleting expert and company marketplace profiles."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, Profile, ProfileKind, VerificationStatus
from app.models.review import Review
from app.models.user import User


class ProfileNotFoundError(Exception):
    """Raised when the target profile does not exist."""


async def list_profiles_for_review(session: AsyncSession, status: str, q: str | None = None) -> list[dict]:
    """Return profiles filtered by pending/verified/rejected/blocked/all, optionally searched by name or email."""
    # Company profiles have no user_id, so their owner email comes from the company's first admin.
    admin_email = (
        select(User.email)
        .join(OrganizationMember, OrganizationMember.user_id == User.id)
        .where(
            OrganizationMember.organization_id == Profile.organization_id,
            OrganizationMember.member_role == MemberRole.ADMIN.value,
        )
        .order_by(OrganizationMember.created_at)
        .limit(1)
        .scalar_subquery()
    )
    owner_email = func.coalesce(User.email, admin_email)
    query = select(Profile, owner_email).outerjoin(User, User.id == Profile.user_id)
    if status == "blocked":
        query = query.where(Profile.blocked_at.is_not(None))
    elif status != "all":
        query = query.where(Profile.verification == VerificationStatus(status), Profile.blocked_at.is_(None))
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(Profile.display_name.ilike(pattern), owner_email.ilike(pattern)))
    rows = (await session.execute(query.order_by(Profile.created_at.desc()).limit(200))).all()
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
            "blocked_at": profile.blocked_at,
            "blocked_reason": profile.blocked_reason,
            "created_at": profile.created_at,
        }
        for profile, email in rows
    ]


async def _get_profile(session: AsyncSession, profile_id: UUID) -> Profile:
    profile = await session.get(Profile, profile_id)
    if profile is None:
        raise ProfileNotFoundError("Profile not found")
    return profile


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


async def set_profile_blocked(session: AsyncSession, profile_id: UUID, reason: str | None) -> None:
    """Block (reason given) or unblock (reason None) a profile. Blocked profiles vanish from discovery."""
    profile = await _get_profile(session, profile_id)
    profile.blocked_at = datetime.now(timezone.utc) if reason else None
    profile.blocked_reason = reason
    await session.commit()


async def delete_profile(session: AsyncSession, profile_id: UUID) -> None:
    """Permanently delete a profile. For a company this removes the whole organization and its memberships."""
    profile = await _get_profile(session, profile_id)
    if profile.kind is ProfileKind.COMPANY and profile.organization_id is not None:
        org_profile_ids = select(Profile.id).where(Profile.organization_id == profile.organization_id)
        # reviews.profile_id has no ON DELETE CASCADE in the DB, so clear them first.
        await session.execute(delete(Review).where(Review.profile_id.in_(org_profile_ids)))
        # Everything else (profiles, members, request participants, OTPs, saved profiles) cascades in Postgres.
        await session.execute(delete(Organization).where(Organization.id == profile.organization_id))
    else:
        await session.execute(delete(Review).where(Review.profile_id == profile.id))
        await session.execute(delete(Profile).where(Profile.id == profile.id))
    await session.commit()
