"""Public browsing and profile-owner publishing with serialized per-profile quotas."""
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import profile_plan_active
from app.features.profiles.service import ProfileAccessError, ProfileNotFoundError, _require_manage
from app.features.showcases.links import parse_video_link, validate_cover_url
from app.features.showcases.schemas import ManagedShowcases, ShowcaseInput, ShowcaseList, ShowcaseOut
from app.models.profile import Organization, Profile, ProfileKind
from app.models.showcase import VideoShowcase
from app.models.user import User

SHOWCASE_LIMIT = {False: 2, True: 10}


class ShowcaseConflictError(Exception):
    """Duplicate link or exhausted profile quota."""


def to_showcase(row: VideoShowcase, provider_name: str) -> ShowcaseOut:
    return ShowcaseOut(
        id=row.id, profile_id=row.profile_id, provider_name=provider_name,
        source_url=row.source_url, platform=parse_video_link(row.source_url).platform,
        title=row.title, description=row.description, cover_url=row.cover_url, created_at=row.created_at,
    )


def public_showcases() -> Select[tuple[VideoShowcase, str]]:
    return (
        select(VideoShowcase, Profile.display_name)
        .join(Profile, Profile.id == VideoShowcase.profile_id)
        .outerjoin(User, User.id == Profile.user_id)
        .outerjoin(Organization, Organization.id == Profile.organization_id)
        .where(
            Profile.deleted_at.is_(None), Profile.blocked_at.is_(None),
            or_(
                (Profile.kind == ProfileKind.EXPERT) & User.id.is_not(None)
                & User.deleted_at.is_(None) & User.blocked_at.is_(None),
                (Profile.kind == ProfileKind.COMPANY) & Organization.id.is_not(None)
                & Organization.deleted_at.is_(None),
            ),
        )
    )


async def list_showcases(
    session: AsyncSession, page: int, page_size: int, profile_id: UUID | None = None,
) -> ShowcaseList:
    stmt = public_showcases()
    if profile_id:
        stmt = stmt.where(VideoShowcase.profile_id == profile_id)
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await session.execute(
        stmt.order_by(VideoShowcase.created_at.desc(), VideoShowcase.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).all()
    return ShowcaseList(
        results=[to_showcase(row, name) for row, name in rows],
        total=total, page=page, page_size=page_size,
    )


async def managed_profile(session: AsyncSession, auth_user_id: UUID, profile_id: UUID) -> Profile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    if profile.blocked_at is not None:
        raise ProfileAccessError("This profile is blocked and cannot publish showcases.")
    if profile.kind is ProfileKind.COMPANY:
        organization = await session.get(Organization, profile.organization_id)
        if organization is None or organization.deleted_at is not None:
            raise ProfileNotFoundError("Company not found")
    return profile


async def managed_showcases(session: AsyncSession, auth_user_id: UUID, profile_id: UUID) -> ManagedShowcases:
    profile = await managed_profile(session, auth_user_id, profile_id)
    paid = await profile_plan_active(session, profile)
    rows = (await session.scalars(
        select(VideoShowcase).where(VideoShowcase.profile_id == profile_id)
        .order_by(VideoShowcase.created_at.desc(), VideoShowcase.id.desc())
    )).all()
    return ManagedShowcases(
        results=[to_showcase(row, profile.display_name) for row in rows],
        total=len(rows), limit=SHOWCASE_LIMIT[paid], plan_active=paid,
    )


async def save_showcase(
    session: AsyncSession, auth_user_id: UUID, profile_id: UUID, payload: ShowcaseInput,
    supabase_url: str, showcase_id: UUID | None = None,
) -> ShowcaseOut:
    profile = await managed_profile(session, auth_user_id, profile_id)
    # All mutations lock the parent, so concurrent submissions cannot exceed the quota.
    await session.execute(select(Profile.id).where(Profile.id == profile_id).with_for_update())
    row = None
    if showcase_id:
        row = await session.get(VideoShowcase, showcase_id)
        if row is None or row.profile_id != profile_id:
            raise ProfileNotFoundError("Showcase not found")
    source = parse_video_link(payload.source_url)
    # Other company admins can retain the current cover, but cannot attach arbitrary URLs.
    if row is not None and payload.cover_url == row.cover_url:
        cover = row.cover_url
    else:
        cover = validate_cover_url(payload.cover_url, source, supabase_url, auth_user_id)
    duplicate = await session.scalar(select(VideoShowcase.id).where(
        VideoShowcase.profile_id == profile_id, VideoShowcase.source_url == source.url,
        VideoShowcase.id != showcase_id if showcase_id else True,
    ))
    if duplicate is not None:
        raise ShowcaseConflictError("This video is already published on this profile.")
    if row is None:
        paid = await profile_plan_active(session, profile)
        count = await session.scalar(
            select(func.count()).select_from(VideoShowcase).where(VideoShowcase.profile_id == profile_id)
        ) or 0
        if count >= SHOWCASE_LIMIT[paid]:
            raise ShowcaseConflictError(
                f"This profile can publish {SHOWCASE_LIMIT[paid]} showcases. "
                + (
                    "Remove an existing post before adding another."
                    if paid else
                    "Remove an existing post or upgrade this profile to an active Pro/Enterprise plan for up to 10."
                )
            )
        row = VideoShowcase(profile_id=profile_id)
        session.add(row)
    row.source_url = source.url
    row.cover_url = cover
    row.title = payload.title
    row.description = payload.description
    await session.commit()
    await session.refresh(row)
    return to_showcase(row, profile.display_name)


async def remove_showcase(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, showcase_id: UUID) -> None:
    await managed_profile(session, auth_user_id, profile_id)
    await session.execute(select(Profile.id).where(Profile.id == profile_id).with_for_update())
    row = await session.get(VideoShowcase, showcase_id)
    if row is None or row.profile_id != profile_id:
        raise ProfileNotFoundError("Showcase not found")
    await session.delete(row)
    await session.commit()
