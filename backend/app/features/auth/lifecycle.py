"""Soft delete / restore for accounts, expert profiles, and companies.

Rows are only flagged with deleted_at; a separate purge job hard-deletes them later.
Everything removed in one action shares the same timestamp so it can be restored together.
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, Profile, ProfileKind
from app.models.user import User


class RestoreConflictError(Exception):
    """Raised when restoring would clash with an account/profile created since the deletion."""


async def soft_delete_company(session: AsyncSession, organization_id: UUID, now: datetime) -> None:
    organization = await session.get(Organization, organization_id)
    if organization is not None and organization.deleted_at is None:
        organization.deleted_at = now
    await session.execute(
        update(Profile)
        .where(Profile.organization_id == organization_id, Profile.deleted_at.is_(None))
        .values(deleted_at=now)
    )


async def soft_delete_profile(session: AsyncSession, profile: Profile, now: datetime) -> None:
    if profile.kind is ProfileKind.COMPANY and profile.organization_id is not None:
        await soft_delete_company(session, profile.organization_id, now)
    else:
        profile.deleted_at = now


async def soft_delete_user(session: AsyncSession, user: User, now: datetime) -> None:
    """Delete the account, its expert profile, and any company it is the last remaining admin of."""
    user.deleted_at = now
    await session.execute(
        update(Profile).where(Profile.user_id == user.id, Profile.deleted_at.is_(None)).values(deleted_at=now)
    )
    admin_org_ids = (
        await session.scalars(
            select(OrganizationMember.organization_id).where(
                OrganizationMember.user_id == user.id, OrganizationMember.member_role == MemberRole.ADMIN.value
            )
        )
    ).all()
    for organization_id in admin_org_ids:
        other_admin = await session.scalar(
            select(OrganizationMember.id)
            .join(User, User.id == OrganizationMember.user_id)
            .where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.member_role == MemberRole.ADMIN.value,
                OrganizationMember.user_id != user.id,
                User.deleted_at.is_(None),
            )
        )
        if other_admin is None:
            await soft_delete_company(session, organization_id, now)


async def restore_user(session: AsyncSession, user: User) -> None:
    """Undo a soft delete, including the profiles/companies removed in the same action."""
    if user.deleted_at is None:
        return
    clash = await session.scalar(
        select(User.id).where(
            User.deleted_at.is_(None),
            User.id != user.id,
            or_(User.auth_user_id == user.auth_user_id, User.email == user.email),
        )
    )
    if clash is not None:
        raise RestoreConflictError("This person already signed up again with a new account")

    deleted_at = user.deleted_at
    user.deleted_at = None
    await session.execute(
        update(Profile).where(Profile.user_id == user.id, Profile.deleted_at == deleted_at).values(deleted_at=None)
    )
    org_ids = (await session.scalars(select(Organization.id).where(Organization.deleted_at == deleted_at))).all()
    member_org_ids = set(
        (
            await session.scalars(
                select(OrganizationMember.organization_id).where(OrganizationMember.user_id == user.id)
            )
        ).all()
    )
    for organization_id in org_ids:
        if organization_id in member_org_ids:
            await _restore_company(session, organization_id, deleted_at)


async def _restore_company(session: AsyncSession, organization_id: UUID, deleted_at: datetime) -> None:
    organization = await session.get(Organization, organization_id)
    if organization is not None:
        organization.deleted_at = None
    await session.execute(
        update(Profile)
        .where(Profile.organization_id == organization_id, Profile.deleted_at == deleted_at)
        .values(deleted_at=None)
    )


async def restore_profile(session: AsyncSession, profile: Profile) -> None:
    if profile.deleted_at is None:
        return
    if profile.kind is ProfileKind.COMPANY and profile.organization_id is not None:
        await _restore_company(session, profile.organization_id, profile.deleted_at)
        return
    owner = await session.get(User, profile.user_id)
    if owner is None or owner.deleted_at is not None:
        raise RestoreConflictError("Restore the owner's account first")
    clash = await session.scalar(
        select(Profile.id).where(
            Profile.user_id == profile.user_id,
            Profile.kind == ProfileKind.EXPERT,
            Profile.deleted_at.is_(None),
            Profile.id != profile.id,
        )
    )
    if clash is not None:
        raise RestoreConflictError("This person already created a new expert profile")
    profile.deleted_at = None
