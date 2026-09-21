"""Query logic for searching live marketplace profiles."""
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.marketplace.schemas import ProfileDetail, ProfileListResponse, ProfileSummary, ReviewSummary
from app.models.profile import Profile, VerificationStatus
from app.models.review import Review
from app.models.user import User


def _to_summary(profile: Profile) -> ProfileSummary:
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
    )


async def search_profiles(
    session: AsyncSession,
    query: str | None = None,
    city: str | None = None,
    kind: str | None = None,
) -> ProfileListResponse:
    """Return verified profiles matching the optional search filters."""
    stmt = select(Profile)
    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(or_(Profile.display_name.ilike(pattern), Profile.headline.ilike(pattern)))
    if city:
        stmt = stmt.where(Profile.city.ilike(f"%{city}%"))
    if kind:
        stmt = stmt.where(Profile.kind == kind)
    stmt = stmt.order_by(Profile.average_rating.desc(), Profile.review_count.desc())

    profiles = (await session.scalars(stmt)).all()
    results = [_to_summary(profile) for profile in profiles]
    return ProfileListResponse(results=results, total=len(results))


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
    return ProfileDetail(**_to_summary(profile).model_dump(), bio=profile.bio, reviews=reviews)
