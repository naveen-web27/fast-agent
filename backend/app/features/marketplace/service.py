"""Query logic for searching live marketplace profiles."""
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.marketplace.schemas import ProfileDetail, ProfileListResponse, ProfileSummary, ReviewSummary
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Profile, ProfileKind, VerificationStatus
from app.models.request import Request, RequestParticipant, RequestStatus
from app.models.review import Review
from app.models.saved_profile import SavedProfile
from app.models.user import User


class IdentityNotFoundError(Exception):
    """Raised when the caller hasn't completed onboarding yet."""


class ProfileNotFoundError(Exception):
    """Raised when the target profile does not exist."""


class ProfileAccessError(Exception):
    """Raised when the caller doesn't manage the profile they're trying to change."""


async def _get_user(session: AsyncSession, auth_user_id: UUID) -> User:
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        raise IdentityNotFoundError("Complete onboarding before saving profiles")
    return user


async def count_resolved_clients(session: AsyncSession, profile: Profile) -> int:
    """Count distinct customers whose request with this profile reached 'completed'."""
    condition = (
        RequestParticipant.user_id == profile.user_id
        if profile.kind is ProfileKind.EXPERT
        else RequestParticipant.organization_id == profile.organization_id
    )
    stmt = (
        select(func.count(func.distinct(Request.customer_id)))
        .select_from(Request)
        .join(RequestParticipant, RequestParticipant.request_id == Request.id)
        .where(condition, Request.status == RequestStatus.COMPLETED)
    )
    return (await session.scalar(stmt)) or 0


async def _to_summary(session: AsyncSession, profile: Profile) -> ProfileSummary:
    resolved_count = await count_resolved_clients(session, profile)
    return ProfileSummary(
        id=profile.id,
        kind=profile.kind.value,
        display_name=profile.display_name,
        headline=profile.headline,
        city=profile.city,
        years_experience=profile.years_experience,
        languages=profile.languages,
        avatar_url=profile.avatar_url,
        verified=profile.verification == VerificationStatus.VERIFIED,
        average_rating=float(profile.average_rating),
        review_count=profile.review_count,
        response_minutes=profile.response_minutes,
        tags=[service.name for service in profile.services],
        resolved_clients_count=resolved_count if profile.show_resolved_count else None,
    )


async def search_profiles(
    session: AsyncSession,
    query: str | None = None,
    city: str | None = None,
    kind: str | None = None,
    page: int = 1,
    page_size: int = 12,
) -> ProfileListResponse:
    """Return a page of verified profiles matching the optional search filters."""
    stmt = select(Profile)
    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(or_(Profile.display_name.ilike(pattern), Profile.headline.ilike(pattern)))
    if city:
        stmt = stmt.where(Profile.city.ilike(f"%{city}%"))
    if kind:
        stmt = stmt.where(Profile.kind == kind)

    total = (await session.scalar(select(func.count()).select_from(stmt.subquery()))) or 0

    stmt = stmt.order_by(Profile.average_rating.desc(), Profile.review_count.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    profiles = (await session.scalars(stmt)).all()
    results = [await _to_summary(session, profile) for profile in profiles]
    return ProfileListResponse(results=results, total=total, page=page, page_size=page_size)


async def get_profile_detail(session: AsyncSession, profile_id: UUID) -> ProfileDetail | None:
    """Return the full profile detail with reviews, or None if it doesn't exist."""
    profile = await session.get(Profile, profile_id)
    if profile is None:
        return None
    review_rows = (
        await session.execute(
            select(Review, User.full_name)
            .join(User, User.id == Review.reviewer_id)
            .where(Review.profile_id == profile_id)
            .order_by(Review.created_at.desc())
        )
    ).all()
    reviews = [
        ReviewSummary(reviewer_name=name, rating=review.rating, body=review.body, created_at=review.created_at)
        for review, name in review_rows
    ]
    summary = await _to_summary(session, profile)
    return ProfileDetail(**summary.model_dump(), bio=profile.bio, reviews=reviews)


async def save_profile(session: AsyncSession, auth_user_id: UUID, profile_id: UUID) -> None:
    """Bookmark a profile for the caller, ignoring the call if it's already saved."""
    user = await _get_user(session, auth_user_id)
    if await session.get(Profile, profile_id) is None:
        raise ProfileNotFoundError("Profile not found")
    existing = await session.scalar(
        select(SavedProfile).where(SavedProfile.user_id == user.id, SavedProfile.profile_id == profile_id)
    )
    if existing is None:
        session.add(SavedProfile(user_id=user.id, profile_id=profile_id))
        await session.commit()


async def unsave_profile(session: AsyncSession, auth_user_id: UUID, profile_id: UUID) -> None:
    """Remove a bookmark, ignoring the call if it isn't saved."""
    user = await _get_user(session, auth_user_id)
    existing = await session.scalar(
        select(SavedProfile).where(SavedProfile.user_id == user.id, SavedProfile.profile_id == profile_id)
    )
    if existing is not None:
        await session.delete(existing)
        await session.commit()


async def list_saved_profiles(
    session: AsyncSession, auth_user_id: UUID, page: int = 1, page_size: int = 12
) -> ProfileListResponse:
    """Return the caller's bookmarked profiles, most recently saved first."""
    user = await _get_user(session, auth_user_id)
    stmt = (
        select(Profile)
        .join(SavedProfile, SavedProfile.profile_id == Profile.id)
        .where(SavedProfile.user_id == user.id)
        .order_by(SavedProfile.created_at.desc())
    )

    total = (await session.scalar(select(func.count()).select_from(stmt.subquery()))) or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    profiles = (await session.scalars(stmt)).all()
    results = [await _to_summary(session, profile) for profile in profiles]
    return ProfileListResponse(results=results, total=total, page=page, page_size=page_size)


async def update_resolved_visibility(
    session: AsyncSession, auth_user_id: UUID, profile_id: UUID, show_resolved_count: bool
) -> ProfileSummary:
    """Let the expert owner or a company admin toggle their public resolved-clients badge."""
    user = await _get_user(session, auth_user_id)
    profile = await session.get(Profile, profile_id)
    if profile is None:
        raise ProfileNotFoundError("Profile not found")

    if profile.kind is ProfileKind.EXPERT:
        if profile.user_id != user.id:
            raise ProfileAccessError("You do not manage this profile")
    else:
        member = await session.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == profile.organization_id,
                OrganizationMember.user_id == user.id,
                OrganizationMember.member_role == MemberRole.ADMIN.value,
            )
        )
        if member is None:
            raise ProfileAccessError("You do not manage this company profile")

    profile.show_resolved_count = show_resolved_count
    await session.commit()
    await session.refresh(profile)
    return await _to_summary(session, profile)
