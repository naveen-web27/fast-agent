"""Company team seats: admins invite staff, who then handle requests assigned to them."""
import html
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.plans import TEAM_SEAT_LIMIT, company_plan_active, require_plan
from app.features.auth.email import EmailDeliveryError, EmailNotConfiguredError, send_email
from app.features.organizations.schemas import PendingInviteOut, TeamMemberOut, TeamResponse
from app.models.organization_invite import OrganizationInvite
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, ProfileKind
from app.models.request import Request, RequestParticipant, RequestStatus
from app.models.user import User, active_user_by_auth_id


class TeamAccessError(Exception):
    """Raised when the caller isn't a member (or admin, for changes) of the company."""


class TeamConflictError(Exception):
    """Raised for duplicate invites, full seats, or removing someone who can't be removed."""


async def _membership(
    session: AsyncSession, auth_user_id: UUID, organization_id: UUID, admin_only: bool
) -> tuple[User, Organization, OrganizationMember]:
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    organization = await session.get(Organization, organization_id)
    if user is None or organization is None or organization.deleted_at is not None:
        raise TeamAccessError("Company not found")
    member = await session.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == user.id
        )
    )
    if member is None or (admin_only and member.member_role != MemberRole.ADMIN.value):
        raise TeamAccessError("Only a company admin can manage the team")
    return user, organization, member


async def _team(session: AsyncSession, organization: Organization, member: OrganizationMember) -> TeamResponse:
    closed_statuses = (RequestStatus.COMPLETED, RequestStatus.CANCELLED)
    rows = (
        await session.execute(
            select(OrganizationMember, User)
            .join(User, User.id == OrganizationMember.user_id)
            .where(OrganizationMember.organization_id == organization.id, User.deleted_at.is_(None))
            .order_by(OrganizationMember.created_at)
        )
    ).all()
    open_counts = dict(
        (
            await session.execute(
                select(RequestParticipant.assigned_user_id, func.count())
                .join(Request, Request.id == RequestParticipant.request_id)
                .where(
                    RequestParticipant.organization_id == organization.id,
                    RequestParticipant.assigned_user_id.is_not(None),
                    Request.status.not_in(closed_statuses),
                )
                .group_by(RequestParticipant.assigned_user_id)
            )
        ).all()
    )
    invites = (
        await session.scalars(
            select(OrganizationInvite)
            .where(OrganizationInvite.organization_id == organization.id, OrganizationInvite.accepted_at.is_(None))
            .order_by(OrganizationInvite.created_at)
        )
    ).all()
    return TeamResponse(
        organization_id=organization.id,
        name=organization.name,
        can_manage=member.member_role == MemberRole.ADMIN.value,
        plan_active=company_plan_active(organization),
        seat_limit=TEAM_SEAT_LIMIT,
        seats_used=len(rows) + len(invites),
        members=[
            TeamMemberOut(
                id=m.id,
                user_id=u.id,
                full_name=u.full_name,
                email=u.email,
                member_role=m.member_role,
                open_assigned=open_counts.get(u.id, 0),
            )
            for m, u in rows
        ],
        invites=[PendingInviteOut(id=i.id, email=i.email, created_at=i.created_at) for i in invites],
    )


async def get_team(session: AsyncSession, auth_user_id: UUID, organization_id: UUID) -> TeamResponse:
    _, organization, member = await _membership(session, auth_user_id, organization_id, admin_only=False)
    return await _team(session, organization, member)


async def invite_member(
    session: AsyncSession, settings: Settings, auth_user_id: UUID, organization_id: UUID, email: str
) -> TeamResponse:
    """Add an existing user straight away, or leave an invite that's accepted when they first sign in."""
    inviter, organization, member = await _membership(session, auth_user_id, organization_id, admin_only=True)
    require_plan(company_plan_active(organization), ProfileKind.COMPANY, "Team seats")
    team = await _team(session, organization, member)
    if team.seats_used >= TEAM_SEAT_LIMIT:
        raise TeamConflictError(f"All {TEAM_SEAT_LIMIT} seats are in use. Remove someone to invite a new member.")
    email = email.strip().lower()
    if any(m.email.lower() == email for m in team.members):
        raise TeamConflictError("This person is already on your team")
    if any(i.email.lower() == email for i in team.invites):
        raise TeamConflictError("An invite for this email is already pending")

    existing_user = await session.scalar(select(User).where(func.lower(User.email) == email, User.deleted_at.is_(None)))
    if existing_user is not None:
        session.add(OrganizationMember(organization_id=organization.id, user_id=existing_user.id, member_role=MemberRole.STAFF.value))
    else:
        session.add(OrganizationInvite(organization_id=organization.id, email=email, invited_by=inviter.id))
    await session.commit()

    try:
        await send_email(
            settings,
            to=email,
            subject=f"You've been added to {organization.name} on RightConnect",
            html=(
                f"<p>{html.escape(inviter.full_name)} added you to the <strong>{html.escape(organization.name)}</strong> "
                f"team on RightConnect.</p><p>Sign in with Google using this email at "
                f"<a href=\"{html.escape(settings.app_base_url)}\">{html.escape(settings.app_base_url)}</a> to see requests assigned to you.</p>"
            ),
        )
    except (EmailNotConfiguredError, EmailDeliveryError):
        pass  # The invite still works; the admin can tell the person directly.
    return await _team(session, organization, member)


async def cancel_invite(session: AsyncSession, auth_user_id: UUID, organization_id: UUID, invite_id: UUID) -> TeamResponse:
    _, organization, member = await _membership(session, auth_user_id, organization_id, admin_only=True)
    await session.execute(
        delete(OrganizationInvite).where(
            OrganizationInvite.id == invite_id,
            OrganizationInvite.organization_id == organization.id,
            OrganizationInvite.accepted_at.is_(None),
        )
    )
    await session.commit()
    return await _team(session, organization, member)


async def remove_member(session: AsyncSession, auth_user_id: UUID, organization_id: UUID, member_id: UUID) -> TeamResponse:
    """Remove a staff member; their open requests go back to the unassigned pile."""
    _, organization, member = await _membership(session, auth_user_id, organization_id, admin_only=True)
    target = await session.get(OrganizationMember, member_id)
    if target is None or target.organization_id != organization.id:
        raise TeamConflictError("Team member not found")
    if target.member_role != MemberRole.STAFF.value:
        raise TeamConflictError("Admins can't be removed here")
    await session.execute(
        update(RequestParticipant)
        .where(RequestParticipant.organization_id == organization.id, RequestParticipant.assigned_user_id == target.user_id)
        .values(assigned_user_id=None)
    )
    await session.delete(target)
    await session.commit()
    return await _team(session, organization, member)
