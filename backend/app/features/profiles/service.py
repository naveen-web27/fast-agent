"""Owners editing their expert/company profile: basics (free) plus Pro/Enterprise extras."""
import re
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.links import detect_platform
from app.core.plans import (
    CREDENTIAL_LIMIT,
    OFFERING_LIMIT,
    SOCIAL_LINK_LIMIT,
    profile_plan_active,
    require_plan,
)
from app.features.marketplace.catalog import related_words_for
from app.features.profiles.schemas import (
    AvailabilityUpdate,
    AvailabilityWindow,
    CredentialIn,
    CredentialOut,
    EducationIn,
    EducationOut,
    ExperienceIn,
    ExperienceOut,
    ManagedProfile,
    OfferingIn,
    OfferingOut,
    PlanLimits,
    ProfileUpdate,
    SocialLinkOut,
    SocialLinksUpdate,
)
from app.models.availability import AvailabilitySlot
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, Profile, ProfileKind, Service
from app.models.profile_extras import Credential, ProfileEducation, ProfileExperience, ProfileOffering
from app.models.social_link import SocialLink
from app.models.user import active_user_by_auth_id

EXPERIENCE_LIMIT = 30
EDUCATION_LIMIT = 15


class ProfileNotFoundError(Exception):
    """Raised when the profile doesn't exist or the caller hasn't onboarded."""


class ProfileAccessError(Exception):
    """Raised when the caller doesn't manage this profile."""


class ProfileLimitError(Exception):
    """Raised when adding more items than the current plan allows."""


async def _require_manage(session: AsyncSession, auth_user_id: UUID, profile_id: UUID) -> Profile:
    """The expert who owns the profile, or an admin of the company behind it."""
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    profile = await session.get(Profile, profile_id)
    if user is None or profile is None or profile.deleted_at is not None:
        raise ProfileNotFoundError("Profile not found")
    if profile.kind is ProfileKind.EXPERT:
        allowed = profile.user_id == user.id
    else:
        allowed = (
            await session.scalar(
                select(OrganizationMember.id).where(
                    OrganizationMember.organization_id == profile.organization_id,
                    OrganizationMember.user_id == user.id,
                    OrganizationMember.member_role == MemberRole.ADMIN.value,
                )
            )
        ) is not None
    if not allowed:
        raise ProfileAccessError("You do not manage this profile")
    return profile


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:80] or "service"


async def _services_by_name(session: AsyncSession, names: list[str]) -> list[Service]:
    """Reuse existing service categories by slug, creating new ones the first time they're used."""
    services = []
    for name in names:
        slug = _slugify(name)
        service = await session.scalar(select(Service).where(Service.slug == slug))
        if service is None:
            service = Service(name=name, slug=slug)
            session.add(service)
            await session.flush()
        services.append(service)
    return services


async def load_experiences(session: AsyncSession, profile_id: UUID) -> list[ExperienceOut]:
    """Current roles first, then most recent."""
    rows = await session.scalars(
        select(ProfileExperience)
        .where(ProfileExperience.profile_id == profile_id)
        .order_by(ProfileExperience.end_date.desc().nulls_first(), ProfileExperience.start_date.desc())
    )
    return [
        ExperienceOut(
            id=row.id,
            title=row.title,
            organization=row.organization,
            location=row.location,
            start_date=row.start_date,
            end_date=row.end_date,
            description=row.description,
        )
        for row in rows.all()
    ]


async def load_educations(session: AsyncSession, profile_id: UUID) -> list[EducationOut]:
    rows = await session.scalars(
        select(ProfileEducation)
        .where(ProfileEducation.profile_id == profile_id)
        .order_by(ProfileEducation.end_year.desc().nulls_first(), ProfileEducation.start_year.desc().nulls_last())
    )
    return [
        EducationOut(
            id=row.id,
            school=row.school,
            degree=row.degree,
            field_of_study=row.field_of_study,
            start_year=row.start_year,
            end_year=row.end_year,
            description=row.description,
        )
        for row in rows.all()
    ]


async def _managed(session: AsyncSession, profile: Profile) -> ManagedProfile:
    paid = await profile_plan_active(session, profile)
    links = (await session.scalars(select(SocialLink).where(SocialLink.profile_id == profile.id))).all()
    credentials = (await session.scalars(select(Credential).where(Credential.profile_id == profile.id))).all()
    offerings = (
        await session.scalars(
            select(ProfileOffering).where(ProfileOffering.profile_id == profile.id).order_by(ProfileOffering.created_at)
        )
    ).all()
    windows = (
        await session.scalars(
            select(AvailabilitySlot)
            .where(AvailabilitySlot.profile_id == profile.id)
            .order_by(AvailabilitySlot.weekday, AvailabilitySlot.start_time)
        )
    ).all()
    await session.refresh(profile, ["services"])
    return ManagedProfile(
        id=profile.id,
        kind=profile.kind.value,
        display_name=profile.display_name,
        headline=profile.headline,
        bio=profile.bio,
        city=profile.city,
        years_experience=profile.years_experience,
        languages=profile.languages,
        avatar_url=profile.avatar_url,
        services=[service.name for service in profile.services],
        keywords=profile.keywords,
        suggested_keywords=[
            word for word in related_words_for([service.name for service in profile.services]) if word not in profile.keywords
        ],
        intro_video_url=profile.intro_video_url,
        portfolio_url=profile.portfolio_url,
        founded_year=profile.founded_year,
        team_size=profile.team_size,
        social_links=[SocialLinkOut(platform=link.platform, url=link.url) for link in links],
        experiences=await load_experiences(session, profile.id),
        educations=await load_educations(session, profile.id),
        credentials=[
            CredentialOut(
                id=c.id,
                title=c.title,
                issuing_body=c.issuing_body,
                credential_number=c.credential_number,
                document_url=c.document_url,
                verification=c.verification.value,
            )
            for c in credentials
        ],
        offerings=[
            OfferingOut(id=o.id, title=o.title, description=o.description, price_min_inr=o.price_min_inr, price_max_inr=o.price_max_inr)
            for o in offerings
        ],
        availability=[AvailabilityWindow(weekday=w.weekday, start_time=w.start_time, end_time=w.end_time) for w in windows],
        plan="pro" if profile.kind is ProfileKind.EXPERT else "enterprise",
        plan_active=paid,
        limits=PlanLimits(
            social_links=SOCIAL_LINK_LIMIT[paid], credentials=CREDENTIAL_LIMIT[paid], offerings=OFFERING_LIMIT if paid else 0
        ),
    )


async def get_managed_profile(session: AsyncSession, auth_user_id: UUID, profile_id: UUID) -> ManagedProfile:
    return await _managed(session, await _require_manage(session, auth_user_id, profile_id))


async def update_profile(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, payload: ProfileUpdate) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("intro_video_url") or changes.get("portfolio_url"):
        require_plan(await profile_plan_active(session, profile), profile.kind, "Intro video and portfolio links")

    for field in ("display_name", "headline"):
        if changes.get(field):
            setattr(profile, field, changes[field])
    for field in ("bio", "city", "years_experience", "avatar_url", "intro_video_url", "portfolio_url", "founded_year", "team_size"):
        if field in changes:
            setattr(profile, field, changes[field])
    if changes.get("languages") is not None:
        profile.languages = changes["languages"]
    if changes.get("keywords") is not None:
        profile.keywords = changes["keywords"]
    if changes.get("services") is not None:
        await session.refresh(profile, ["services"])
        profile.services = await _services_by_name(session, changes["services"])
    if profile.kind is ProfileKind.COMPANY and changes.get("display_name"):
        organization = await session.get(Organization, profile.organization_id)
        if organization is not None:
            organization.name = changes["display_name"]
    await session.commit()
    return await _managed(session, profile)


async def replace_social_links(
    session: AsyncSession, auth_user_id: UUID, profile_id: UUID, payload: SocialLinksUpdate
) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    # Platform names must be unique per profile, so a second website becomes "Website 2".
    links: list[tuple[str, str]] = []
    taken: set[str] = set()
    for link in payload.links:
        if any(url == link.url for _, url in links):
            continue
        base = (link.platform or "").strip() or detect_platform(link.url)
        name, number = base, 2
        while name.lower() in taken:
            name, number = f"{base} {number}", number + 1
        taken.add(name.lower())
        links.append((name, link.url))
    limit = SOCIAL_LINK_LIMIT[await profile_plan_active(session, profile)]
    if len(links) > limit:
        raise ProfileLimitError(f"Your plan allows {limit} links. Upgrade to add more.")
    await session.execute(delete(SocialLink).where(SocialLink.profile_id == profile.id))
    for platform, url in links:
        session.add(SocialLink(profile_id=profile.id, platform=platform, url=url))
    await session.commit()
    return await _managed(session, profile)


async def add_experience(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, payload: ExperienceIn) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    count = await session.scalar(select(func.count()).select_from(ProfileExperience).where(ProfileExperience.profile_id == profile.id))
    if (count or 0) >= EXPERIENCE_LIMIT:
        raise ProfileLimitError(f"You can list up to {EXPERIENCE_LIMIT} roles")
    session.add(ProfileExperience(profile_id=profile.id, **payload.model_dump()))
    await session.commit()
    return await _managed(session, profile)


async def update_experience(
    session: AsyncSession, auth_user_id: UUID, profile_id: UUID, experience_id: UUID, payload: ExperienceIn
) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    row = await session.get(ProfileExperience, experience_id)
    if row is None or row.profile_id != profile.id:
        raise ProfileNotFoundError("Experience not found")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    await session.commit()
    return await _managed(session, profile)


async def delete_experience(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, experience_id: UUID) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    await session.execute(
        delete(ProfileExperience).where(ProfileExperience.id == experience_id, ProfileExperience.profile_id == profile.id)
    )
    await session.commit()
    return await _managed(session, profile)


async def add_education(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, payload: EducationIn) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    count = await session.scalar(select(func.count()).select_from(ProfileEducation).where(ProfileEducation.profile_id == profile.id))
    if (count or 0) >= EDUCATION_LIMIT:
        raise ProfileLimitError(f"You can list up to {EDUCATION_LIMIT} schools")
    session.add(ProfileEducation(profile_id=profile.id, **payload.model_dump()))
    await session.commit()
    return await _managed(session, profile)


async def update_education(
    session: AsyncSession, auth_user_id: UUID, profile_id: UUID, education_id: UUID, payload: EducationIn
) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    row = await session.get(ProfileEducation, education_id)
    if row is None or row.profile_id != profile.id:
        raise ProfileNotFoundError("Education not found")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    await session.commit()
    return await _managed(session, profile)


async def delete_education(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, education_id: UUID) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    await session.execute(
        delete(ProfileEducation).where(ProfileEducation.id == education_id, ProfileEducation.profile_id == profile.id)
    )
    await session.commit()
    return await _managed(session, profile)


async def add_credential(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, payload: CredentialIn) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    count = await session.scalar(select(func.count()).select_from(Credential).where(Credential.profile_id == profile.id))
    limit = CREDENTIAL_LIMIT[await profile_plan_active(session, profile)]
    if (count or 0) >= limit:
        raise ProfileLimitError(f"Your plan allows {limit} credential{'s' if limit != 1 else ''}. Upgrade to add more.")
    session.add(Credential(profile_id=profile.id, **payload.model_dump()))
    await session.commit()
    return await _managed(session, profile)


async def delete_credential(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, credential_id: UUID) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    await session.execute(delete(Credential).where(Credential.id == credential_id, Credential.profile_id == profile.id))
    await session.commit()
    return await _managed(session, profile)


async def add_offering(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, payload: OfferingIn) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    require_plan(await profile_plan_active(session, profile), profile.kind, "The service catalogue")
    count = await session.scalar(select(func.count()).select_from(ProfileOffering).where(ProfileOffering.profile_id == profile.id))
    if (count or 0) >= OFFERING_LIMIT:
        raise ProfileLimitError(f"You can list up to {OFFERING_LIMIT} services")
    session.add(ProfileOffering(profile_id=profile.id, **payload.model_dump()))
    await session.commit()
    return await _managed(session, profile)


async def delete_offering(session: AsyncSession, auth_user_id: UUID, profile_id: UUID, offering_id: UUID) -> ManagedProfile:
    profile = await _require_manage(session, auth_user_id, profile_id)
    await session.execute(delete(ProfileOffering).where(ProfileOffering.id == offering_id, ProfileOffering.profile_id == profile.id))
    await session.commit()
    return await _managed(session, profile)


async def set_availability(
    session: AsyncSession, auth_user_id: UUID, profile_id: UUID, payload: AvailabilityUpdate
) -> ManagedProfile:
    """Replace the weekly schedule. Clearing it is always allowed; publishing slots needs the paid plan."""
    profile = await _require_manage(session, auth_user_id, profile_id)
    if payload.windows:
        require_plan(await profile_plan_active(session, profile), profile.kind, "Online booking")
    await session.execute(delete(AvailabilitySlot).where(AvailabilitySlot.profile_id == profile.id))
    for window in payload.windows:
        session.add(
            AvailabilitySlot(profile_id=profile.id, weekday=window.weekday, start_time=window.start_time, end_time=window.end_time)
        )
    await session.commit()
    return await _managed(session, profile)
