"""Query logic for searching live marketplace profiles."""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.marketplace.schemas import ProfileListResponse, ProfileSummary
from app.models.profile import Profile, VerificationStatus


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
    results = [
        ProfileSummary(
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
        for profile in profiles
    ]
    return ProfileListResponse(results=results, total=len(results))
