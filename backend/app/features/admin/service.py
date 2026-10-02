"""Admin tools: profile verification/moderation, account moderation, disputes, and an audit trail."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.lifecycle import restore_profile, restore_user, soft_delete_profile, soft_delete_user
from app.models.admin_action import AdminAction
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, Profile, ProfileKind, VerificationStatus
from app.models.request import Request, RequestEvent, RequestParticipant, RequestStatus
from app.models.user import User, UserRole


class ProfileNotFoundError(Exception):
    """Raised when the target profile does not exist."""


class UserNotFoundError(Exception):
    """Raised when the target account does not exist."""


class AdminSelfActionError(Exception):
    """Raised when an admin tries to block or delete their own account."""


class DisputeNotFoundError(Exception):
    """Raised when the dispute was already resolved or never existed."""


def _log(
    session: AsyncSession, admin: User, action: str, target_type: str, target_id: UUID, label: str | None, reason: str | None
) -> None:
    session.add(
        AdminAction(
            admin_user_id=admin.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_label=label,
            reason=reason,
        )
    )


# ---------- Profiles ----------


async def list_profiles_for_review(session: AsyncSession, status: str, q: str | None = None) -> list[dict]:
    """Return profiles filtered by pending/verified/rejected/blocked/deleted/all, optionally searched by name or email."""
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
        query = query.where(Profile.blocked_at.is_not(None), Profile.deleted_at.is_(None))
    elif status == "deleted":
        query = query.where(Profile.deleted_at.is_not(None))
    elif status != "all":
        query = query.where(
            Profile.verification == VerificationStatus(status), Profile.blocked_at.is_(None), Profile.deleted_at.is_(None)
        )
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
            "deleted_at": profile.deleted_at,
            "created_at": profile.created_at,
        }
        for profile, email in rows
    ]


async def _get_profile(session: AsyncSession, profile_id: UUID) -> Profile:
    profile = await session.get(Profile, profile_id)
    if profile is None:
        raise ProfileNotFoundError("Profile not found")
    return profile


async def set_profile_verification(
    session: AsyncSession, admin: User, profile_id: UUID, decision: VerificationStatus
) -> None:
    """Mark a profile (and its organization, if it belongs to one) as verified or rejected."""
    profile = await _get_profile(session, profile_id)
    profile.verification = decision
    if profile.organization_id is not None:
        organization = await session.get(Organization, profile.organization_id)
        if organization is not None:
            organization.verification = decision
    _log(session, admin, decision.value, "profile", profile.id, profile.display_name, None)
    await session.commit()


async def set_profile_blocked(session: AsyncSession, admin: User, profile_id: UUID, reason: str | None) -> None:
    """Block (reason given) or unblock (reason None) a profile. Blocked profiles vanish from discovery."""
    profile = await _get_profile(session, profile_id)
    profile.blocked_at = datetime.now(timezone.utc) if reason else None
    profile.blocked_reason = reason
    _log(session, admin, "block" if reason else "unblock", "profile", profile.id, profile.display_name, reason)
    await session.commit()


async def delete_profile(session: AsyncSession, admin: User, profile_id: UUID) -> None:
    """Soft-delete a profile (a company profile takes its whole company with it)."""
    profile = await _get_profile(session, profile_id)
    if profile.deleted_at is None:
        await soft_delete_profile(session, profile, datetime.now(timezone.utc))
    _log(session, admin, "delete", "profile", profile.id, profile.display_name, None)
    await session.commit()


async def undelete_profile(session: AsyncSession, admin: User, profile_id: UUID) -> None:
    profile = await _get_profile(session, profile_id)
    await restore_profile(session, profile)
    _log(session, admin, "restore", "profile", profile.id, profile.display_name, None)
    await session.commit()


# ---------- Accounts ----------


async def list_users(session: AsyncSession, status: str, role: str | None, q: str | None) -> list[dict]:
    query = select(User)
    if status == "active":
        query = query.where(User.deleted_at.is_(None), User.blocked_at.is_(None))
    elif status == "blocked":
        query = query.where(User.deleted_at.is_(None), User.blocked_at.is_not(None))
    elif status == "deleted":
        query = query.where(User.deleted_at.is_not(None))
    if role:
        query = query.where(User.role == UserRole(role))
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(User.full_name.ilike(pattern), User.email.ilike(pattern), User.phone.ilike(pattern)))
    users = (await session.scalars(query.order_by(User.created_at.desc()).limit(200))).all()

    results = []
    for user in users:
        expert = await session.scalar(
            select(Profile.display_name).where(
                Profile.user_id == user.id, Profile.kind == ProfileKind.EXPERT, Profile.deleted_at.is_(None)
            )
        )
        companies = (
            await session.scalars(
                select(Organization.name)
                .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
                .where(OrganizationMember.user_id == user.id, Organization.deleted_at.is_(None))
            )
        ).all()
        request_count = await session.scalar(select(func.count(Request.id)).where(Request.customer_id == user.id))
        results.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role.value,
                "created_at": user.created_at,
                "blocked_at": user.blocked_at,
                "blocked_reason": user.blocked_reason,
                "deleted_at": user.deleted_at,
                "has_expert_profile": expert is not None,
                "companies": list(companies),
                "requests_sent": request_count or 0,
            }
        )
    return results


async def _get_user_for_admin(session: AsyncSession, admin: User, user_id: UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise UserNotFoundError("User not found")
    if user.id == admin.id:
        raise AdminSelfActionError("You can't do this to your own admin account")
    return user


async def _owned_live_profiles(session: AsyncSession, user: User) -> list[Profile]:
    """The user's expert profile plus the company profiles they administer."""
    admin_org_ids = select(OrganizationMember.organization_id).where(
        OrganizationMember.user_id == user.id, OrganizationMember.member_role == MemberRole.ADMIN.value
    )
    return list(
        (
            await session.scalars(
                select(Profile).where(
                    Profile.deleted_at.is_(None),
                    or_(Profile.user_id == user.id, Profile.organization_id.in_(admin_org_ids)),
                )
            )
        ).all()
    )


async def block_user(session: AsyncSession, admin: User, user_id: UUID, reason: str) -> None:
    """Suspend the account (API returns 403 for them) and hide everything they own from the marketplace."""
    user = await _get_user_for_admin(session, admin, user_id)
    now = datetime.now(timezone.utc)
    user.blocked_at = now
    user.blocked_reason = reason
    for profile in await _owned_live_profiles(session, user):
        if profile.blocked_at is None:
            profile.blocked_at = now
            profile.blocked_reason = f"Owner account blocked: {reason}"
    _log(session, admin, "block", "user", user.id, user.email, reason)
    await session.commit()


async def unblock_user(session: AsyncSession, admin: User, user_id: UUID) -> None:
    user = await _get_user_for_admin(session, admin, user_id)
    blocked_at = user.blocked_at
    user.blocked_at = None
    user.blocked_reason = None
    if blocked_at is not None:
        # Only lift profile blocks applied together with the account block, not separate ones.
        for profile in await _owned_live_profiles(session, user):
            if profile.blocked_at == blocked_at:
                profile.blocked_at = None
                profile.blocked_reason = None
    _log(session, admin, "unblock", "user", user.id, user.email, None)
    await session.commit()


async def delete_user(session: AsyncSession, admin: User, user_id: UUID) -> None:
    user = await _get_user_for_admin(session, admin, user_id)
    if user.deleted_at is None:
        await soft_delete_user(session, user, datetime.now(timezone.utc))
    _log(session, admin, "delete", "user", user.id, user.email, None)
    await session.commit()


async def undelete_user(session: AsyncSession, admin: User, user_id: UUID) -> None:
    user = await _get_user_for_admin(session, admin, user_id)
    await restore_user(session, user)
    _log(session, admin, "restore", "user", user.id, user.email, None)
    await session.commit()


# ---------- Overview, disputes, activity ----------


async def get_stats(session: AsyncSession) -> dict:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    live_user = User.deleted_at.is_(None)
    live_profile = (Profile.deleted_at.is_(None), Profile.blocked_at.is_(None))

    async def count(stmt) -> int:
        return (await session.scalar(stmt)) or 0

    return {
        "users_total": await count(select(func.count(User.id)).where(live_user)),
        "users_new_7d": await count(select(func.count(User.id)).where(live_user, User.created_at >= week_ago)),
        "users_blocked": await count(select(func.count(User.id)).where(live_user, User.blocked_at.is_not(None))),
        "users_deleted": await count(select(func.count(User.id)).where(User.deleted_at.is_not(None))),
        "experts_live": await count(
            select(func.count(Profile.id)).where(Profile.kind == ProfileKind.EXPERT, *live_profile)
        ),
        "companies_live": await count(
            select(func.count(Profile.id)).where(Profile.kind == ProfileKind.COMPANY, *live_profile)
        ),
        "profiles_pending": await count(
            select(func.count(Profile.id)).where(Profile.verification == VerificationStatus.PENDING, *live_profile)
        ),
        "profiles_blocked": await count(
            select(func.count(Profile.id)).where(Profile.deleted_at.is_(None), Profile.blocked_at.is_not(None))
        ),
        "requests_open": await count(
            select(func.count(Request.id)).where(
                Request.status.not_in([RequestStatus.COMPLETED, RequestStatus.CANCELLED])
            )
        ),
        "requests_new_7d": await count(select(func.count(Request.id)).where(Request.created_at >= week_ago)),
        "requests_completed": await count(
            select(func.count(Request.id)).where(Request.status == RequestStatus.COMPLETED)
        ),
        "disputes_open": await count(
            select(func.count(RequestParticipant.id)).where(RequestParticipant.completion_disputed_at.is_not(None))
        ),
    }


async def list_disputes(session: AsyncSession) -> list[dict]:
    """Providers who reported a problem after the customer marked the request done."""
    rows = (
        await session.execute(
            select(RequestParticipant, Request)
            .join(Request, Request.id == RequestParticipant.request_id)
            .where(RequestParticipant.completion_disputed_at.is_not(None))
            .order_by(RequestParticipant.completion_disputed_at.desc())
        )
    ).all()
    results = []
    for participant, request in rows:
        customer = await session.get(User, request.customer_id)
        if participant.user_id is not None:
            provider = await session.get(User, participant.user_id)
            provider_name = provider.full_name if provider else "Unknown expert"
        else:
            organization = await session.get(Organization, participant.organization_id)
            provider_name = organization.name if organization else "Unknown company"
        reason_event = await session.scalar(
            select(RequestEvent.message)
            .where(RequestEvent.request_id == request.id, RequestEvent.message.ilike("%reported a problem%"))
            .order_by(RequestEvent.created_at.desc())
        )
        results.append(
            {
                "participant_id": participant.id,
                "request_id": request.id,
                "request_title": request.title,
                "customer_name": customer.full_name if customer else "Unknown",
                "customer_email": customer.email if customer else None,
                "provider_name": provider_name,
                "provider_role": participant.participant_role,
                "disputed_at": participant.completion_disputed_at,
                "reason": reason_event,
            }
        )
    return results


async def resolve_dispute(session: AsyncSession, admin: User, participant_id: UUID, action: str) -> None:
    """open_ratings: overrule the report so ratings unlock. reopen: send the request back to in-progress."""
    participant = await session.get(RequestParticipant, participant_id)
    if participant is None or participant.completion_disputed_at is None:
        raise DisputeNotFoundError("Dispute not found or already resolved")
    request = await session.get(Request, participant.request_id)
    now = datetime.now(timezone.utc)
    if action == "open_ratings":
        participant.completion_disputed_at = None
        participant.completion_confirmed_at = now
        message = "RightConnect support reviewed the reported problem. Ratings are now open."
    else:
        participants = (
            await session.scalars(select(RequestParticipant).where(RequestParticipant.request_id == request.id))
        ).all()
        for item in participants:
            item.completion_disputed_at = None
            item.completion_confirmed_at = None
        request.status = RequestStatus.ACCEPTED
        request.completed_at = None
        message = "RightConnect support reopened this request after a reported problem. Mark it done again when finished."
    session.add(RequestEvent(request_id=request.id, author_id=None, event_type="system", message=message))
    request.updated_at = now
    _log(session, admin, f"dispute_{action}", "request", request.id, request.title, None)
    await session.commit()


async def list_activity(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(
            select(AdminAction, User.full_name)
            .outerjoin(User, User.id == AdminAction.admin_user_id)
            .order_by(AdminAction.created_at.desc())
            .limit(100)
        )
    ).all()
    return [
        {
            "id": action.id,
            "admin_name": name,
            "action": action.action,
            "target_type": action.target_type,
            "target_id": action.target_id,
            "target_label": action.target_label,
            "reason": action.reason,
            "created_at": action.created_at,
        }
        for action, name in rows
    ]
