"""Query logic for searching live marketplace profiles."""
from functools import reduce
from operator import add
from uuid import UUID

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import CREDENTIAL_LIMIT, SOCIAL_LINK_LIMIT, profile_plan_active
from app.features.marketplace.catalog import search_terms
from app.features.profiles.service import load_educations, load_experiences
from app.features.marketplace.schemas import (
    ProfileDetail,
    ProfileLink,
    ProfileListResponse,
    ProfileSummary,
    PublicCredential,
    PublicOffering,
    ReviewSummary,
)
from app.models.availability import AvailabilitySlot
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Profile, ProfileKind, Service, VerificationStatus
from app.models.profile_extras import Credential, ProfileOffering
from app.models.request import Request, RequestParticipant, RequestStatus
from app.models.review import Review
from app.models.saved_profile import SavedProfile
from app.models.social_link import SocialLink
from app.models.user import User, active_user_by_auth_id


class IdentityNotFoundError(Exception):
    """Raised when the caller hasn't completed onboarding yet."""


class ProfileNotFoundError(Exception):
    """Raised when the target profile does not exist."""


class ProfileAccessError(Exception):
    """Raised when the caller doesn't manage the profile they're trying to change."""


async def _get_user(session: AsyncSession, auth_user_id: UUID) -> User:
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
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


def _like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _relevance(query: str):
    """Match each meaningful word (and the service areas it implies) against services, search words,
    name, headline and bio. Returns (filter, score) or None when the query has no usable words."""
    words, related_services = search_terms(query)
    if not words and not related_services:
        return None
    keywords_text = func.array_to_string(Profile.keywords, " ")
    scored = []
    for word in words:
        pattern = _like(word)
        scored.append((or_(Profile.services.any(Service.name.ilike(pattern, escape="\\")), keywords_text.ilike(pattern, escape="\\")), 3))
        scored.append((or_(Profile.display_name.ilike(pattern, escape="\\"), Profile.headline.ilike(pattern, escape="\\")), 2))
        scored.append((Profile.bio.ilike(pattern, escape="\\"), 1))
    for name in related_services:
        pattern = _like(name)
        scored.append((or_(Profile.services.any(Service.name.ilike(pattern, escape="\\")), Profile.headline.ilike(pattern, escape="\\")), 4))
    score = reduce(add, [case((condition, weight), else_=0) for condition, weight in scored])
    return or_(*[condition for condition, _ in scored]), score


async def search_profiles(
    session: AsyncSession,
    query: str | None = None,
    city: str | None = None,
    kind: str | None = None,
    page: int = 1,
    page_size: int = 12,
) -> ProfileListResponse:
    """Return a page of profiles matching the search, best matches first."""
    stmt = select(Profile).where(Profile.blocked_at.is_(None), Profile.deleted_at.is_(None))
    # A search of only filler words ("I need help") lists everyone rather than nothing.
    relevance = _relevance(query) if query else None
    if relevance is not None:
        stmt = stmt.where(relevance[0])
    if city:
        stmt = stmt.where(Profile.city.ilike(_like(city), escape="\\"))
    if kind:
        stmt = stmt.where(Profile.kind == kind)

    total = (await session.scalar(select(func.count()).select_from(stmt.subquery()))) or 0

    ordering = [Profile.average_rating.desc(), Profile.review_count.desc()]
    if relevance is not None:
        ordering.insert(0, relevance[1].desc())
    stmt = stmt.order_by(*ordering)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    profiles = (await session.scalars(stmt)).all()
    results = [await _to_summary(session, profile) for profile in profiles]
    return ProfileListResponse(results=results, total=total, page=page, page_size=page_size)


async def get_profile_detail(session: AsyncSession, profile_id: UUID) -> ProfileDetail | None:
    """Return the full profile detail with reviews, or None if it doesn't exist."""
    profile = await session.get(Profile, profile_id)
    if profile is None or profile.blocked_at is not None or profile.deleted_at is not None:
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
    paid = await profile_plan_active(session, profile)
    links = (await session.scalars(select(SocialLink).where(SocialLink.profile_id == profile_id))).all()
    credentials = (await session.scalars(select(Credential).where(Credential.profile_id == profile_id))).all()
    offerings = (
        (await session.scalars(select(ProfileOffering).where(ProfileOffering.profile_id == profile_id).order_by(ProfileOffering.created_at))).all()
        if paid
        else []
    )
    has_slots = await session.scalar(select(AvailabilitySlot.id).where(AvailabilitySlot.profile_id == profile_id).limit(1))
    detail = ProfileDetail(
        **summary.model_dump(),
        bio=profile.bio,
        reviews=reviews,
        intro_video_url=profile.intro_video_url if paid else None,
        portfolio_url=profile.portfolio_url if paid else None,
        # When a plan lapses the extras are kept but only the free allowance is shown.
        social_links=[ProfileLink(platform=link.platform, url=link.url) for link in links[: SOCIAL_LINK_LIMIT[paid]]],
        credentials=[
            PublicCredential(title=c.title, issuing_body=c.issuing_body, verified=c.verification == VerificationStatus.VERIFIED)
            for c in credentials[: CREDENTIAL_LIMIT[paid]]
        ],
        offerings=[
            PublicOffering(title=o.title, description=o.description, price_min_inr=o.price_min_inr, price_max_inr=o.price_max_inr)
            for o in offerings
        ],
        bookable=paid and has_slots is not None,
        experiences=await load_experiences(session, profile_id),
        educations=await load_educations(session, profile_id),
        founded_year=profile.founded_year,
        team_size=profile.team_size,
        member_since=profile.created_at,
    )
    await session.execute(update(Profile).where(Profile.id == profile_id).values(view_count=Profile.view_count + 1))
    await session.commit()
    return detail


async def save_profile(session: AsyncSession, auth_user_id: UUID, profile_id: UUID) -> None:
    """Bookmark a profile for the caller, ignoring the call if it's already saved."""
    user = await _get_user(session, auth_user_id)
    profile = await session.get(Profile, profile_id)
    if profile is None or profile.blocked_at is not None or profile.deleted_at is not None:
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
        .where(SavedProfile.user_id == user.id, Profile.blocked_at.is_(None), Profile.deleted_at.is_(None))
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
