"""Overview numbers for each identity. Dashboards are free; provider analytics need the identity's plan."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import company_plan_active, expert_plan_active, plan_expiry
from app.features.booking.slots import ACTIVE_STATUSES, LOCAL_TZ, has_availability
from app.features.dashboard.schemas import (
    Completeness,
    CustomerDashboard,
    DomainCount,
    InterestRecommendations,
    MeetingOut,
    MiniProfile,
    MonthCount,
    ProviderDashboard,
    ProviderInsights,
    RequestCounts,
    TeamMemberStat,
)
from app.features.marketplace.service import count_resolved_clients, search_profiles
from app.features.requests.service import list_requests
from app.models.availability import Appointment
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, Profile, ProfileKind, Service
from app.models.profile_extras import Credential
from app.models.request import Request, RequestParticipant, RequestStatus
from app.models.saved_profile import SavedProfile
from app.models.social_link import SocialLink
from app.models.user import User, active_user_by_auth_id

CLOSED = (RequestStatus.COMPLETED, RequestStatus.CANCELLED)
ACTIVE_REQUEST = ("accepted", "meeting_booked", "provider_invited")
PROVIDER_INSIGHTS = ["Profile views", "Accept rate", "Average response time", "Leads by month", "Clients by domain"]
COMPANY_INSIGHTS = ["Pipeline board", "Team performance"]


class DashboardNotFoundError(Exception):
    """Raised when the caller hasn't onboarded or doesn't have this identity."""


class DashboardAccessError(Exception):
    """Raised when the caller isn't a member of the requested company."""


async def _user(session: AsyncSession, auth_user_id: UUID) -> User:
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None:
        raise DashboardNotFoundError("Complete onboarding first")
    return user


def _mini(summary) -> MiniProfile:
    return MiniProfile(
        id=summary.id,
        kind=summary.kind,
        display_name=summary.display_name,
        headline=summary.headline,
        average_rating=summary.average_rating,
        review_count=summary.review_count,
        verified=summary.verified,
    )


async def customer_dashboard(session: AsyncSession, auth_user_id: UUID) -> CustomerDashboard:
    """Free for every customer: request progress, meetings, and picks for each area they're interested in."""
    user = await _user(session, auth_user_id)
    mine = [s for s in await list_requests(session, auth_user_id) if s.my_role == "customer"]
    saved_count = await session.scalar(
        select(func.count())
        .select_from(SavedProfile)
        .join(Profile, Profile.id == SavedProfile.profile_id)
        .where(SavedProfile.user_id == user.id, Profile.deleted_at.is_(None), Profile.blocked_at.is_(None))
    )
    meeting_rows = (
        await session.execute(
            select(Appointment, Request.title, Profile.display_name)
            .join(Request, Request.id == Appointment.request_id)
            .outerjoin(Profile, Profile.id == Appointment.profile_id)
            .where(
                Request.customer_id == user.id,
                Appointment.status.in_(ACTIVE_STATUSES),
                Appointment.ends_at > datetime.now(timezone.utc),
            )
            .order_by(Appointment.starts_at)
            .limit(5)
        )
    ).all()
    recommendations = []
    for interest in list(reversed(user.interests))[:6]:
        found = await search_profiles(session, query=interest, page_size=3)
        recommendations.append(InterestRecommendations(interest=interest, profiles=[_mini(p) for p in found.results]))
    return CustomerDashboard(
        requests=RequestCounts(
            total=len(mine),
            waiting=sum(s.status == "submitted" for s in mine),
            active=sum(s.status in ACTIVE_REQUEST for s in mine),
            completed=sum(s.status == "completed" for s in mine),
        ),
        pending_actions=sum(1 for s in mine if s.pending_action),
        saved_count=saved_count or 0,
        upcoming_meetings=[
            MeetingOut(request_id=a.request_id, request_title=title, with_name=name or "Provider", starts_at=a.starts_at)
            for a, title, name in meeting_rows
        ],
        recommendations=recommendations,
    )


async def _provider_rows(session: AsyncSession, condition) -> list[tuple[RequestParticipant, Request]]:
    rows = await session.execute(
        select(RequestParticipant, Request).join(Request, Request.id == RequestParticipant.request_id).where(condition)
    )
    return [(participant, request) for participant, request in rows.all()]


def _lead_counts(rows: list[tuple[RequestParticipant, Request]]) -> RequestCounts:
    return RequestCounts(
        total=len(rows),
        waiting=sum(p.accepted_at is None and r.status not in CLOSED for p, r in rows),
        active=sum(p.accepted_at is not None and r.status not in CLOSED for p, r in rows),
        completed=sum(r.status is RequestStatus.COMPLETED for _, r in rows),
    )


async def _provider_meetings(session: AsyncSession, profile_id: UUID) -> list[MeetingOut]:
    rows = (
        await session.execute(
            select(Appointment, Request.title, User.full_name)
            .join(Request, Request.id == Appointment.request_id)
            .join(User, User.id == Request.customer_id)
            .where(
                Appointment.profile_id == profile_id,
                Appointment.status.in_(ACTIVE_STATUSES),
                Appointment.ends_at > datetime.now(timezone.utc),
            )
            .order_by(Appointment.starts_at)
            .limit(8)
        )
    ).all()
    return [MeetingOut(request_id=a.request_id, request_title=title, with_name=name, starts_at=a.starts_at) for a, title, name in rows]


async def _completeness(session: AsyncSession, profile: Profile, paid: bool, slots: bool) -> Completeness:
    has_credential = await session.scalar(select(Credential.id).where(Credential.profile_id == profile.id).limit(1))
    has_link = await session.scalar(select(SocialLink.id).where(SocialLink.profile_id == profile.id).limit(1))
    checks = [
        ("A clear headline", profile.headline not in ("Company", "Independent expert")),
        ("A short bio", bool(profile.bio)),
        ("Your city", bool(profile.city)),
        ("A photo or logo", bool(profile.avatar_url)),
        ("Languages", bool(profile.languages)),
        ("Services you offer", bool(profile.services)),
        ("At least one credential", has_credential is not None),
        ("A website or social link", has_link is not None),
    ]
    if profile.kind is ProfileKind.EXPERT:
        checks.append(("Years of experience", profile.years_experience is not None))
    if paid:
        checks.append(("Weekly availability for bookings", slots))
    done = sum(ok for _, ok in checks)
    return Completeness(percent=round(100 * done / len(checks)), missing=[label for label, ok in checks if not ok])


async def _insights(session: AsyncSession, rows: list[tuple[RequestParticipant, Request]], profile: Profile) -> ProviderInsights:
    accepted = [(p, r) for p, r in rows if p.accepted_at is not None]
    minutes = [(p.accepted_at - r.created_at).total_seconds() / 60 for p, r in accepted if p.accepted_at >= r.created_at]

    now = datetime.now(LOCAL_TZ)
    months = []
    year, month = now.year, now.month
    for _ in range(6):
        months.append(f"{year:04d}-{month:02d}")
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    by_month = Counter(r.created_at.astimezone(LOCAL_TZ).strftime("%Y-%m") for _, r in rows)

    service_ids = {r.service_id for _, r in rows if r.service_id is not None}
    names = dict((await session.execute(select(Service.id, Service.name).where(Service.id.in_(service_ids)))).all()) if service_ids else {}
    clients: dict[str, set[UUID]] = defaultdict(set)
    for _, r in rows:
        if r.status is RequestStatus.COMPLETED:
            clients[names.get(r.service_id, "General")].add(r.customer_id)

    return ProviderInsights(
        profile_views=profile.view_count,
        accept_rate=round(100 * len(accepted) / len(rows)) if rows else None,
        avg_response_minutes=round(sum(minutes) / len(minutes)) if minutes else None,
        leads_by_month=[MonthCount(month=m, count=by_month.get(m, 0)) for m in reversed(months)],
        clients_by_domain=sorted(
            (DomainCount(domain=domain, count=len(customers)) for domain, customers in clients.items()),
            key=lambda item: -item.count,
        ),
    )


async def expert_dashboard(session: AsyncSession, auth_user_id: UUID) -> ProviderDashboard:
    user = await _user(session, auth_user_id)
    profile = await session.scalar(
        select(Profile).where(Profile.user_id == user.id, Profile.kind == ProfileKind.EXPERT, Profile.deleted_at.is_(None))
    )
    if profile is None:
        raise DashboardNotFoundError("Create an expert profile first")
    paid = expert_plan_active(profile)
    slots = await has_availability(session, profile.id)
    rows = await _provider_rows(
        session, and_(RequestParticipant.user_id == user.id, RequestParticipant.participant_role == "expert")
    )
    return ProviderDashboard(
        kind="expert",
        profile_id=profile.id,
        name=profile.display_name,
        plan="pro",
        plan_active=paid,
        plan_expires_at=plan_expiry(profile.subscription_tier, profile.subscription_expires_at),
        leads=_lead_counts(rows),
        average_rating=float(profile.average_rating),
        review_count=profile.review_count,
        resolved_clients=await count_resolved_clients(session, profile),
        completeness=await _completeness(session, profile, paid, slots),
        has_availability=slots,
        upcoming_meetings=await _provider_meetings(session, profile.id),
        insights=await _insights(session, rows, profile) if paid else None,
        locked_insights=[] if paid else PROVIDER_INSIGHTS,
    )


async def company_dashboard(session: AsyncSession, auth_user_id: UUID, organization_id: UUID) -> ProviderDashboard:
    """Admins see the whole company; staff see the requests assigned to them."""
    user = await _user(session, auth_user_id)
    organization = await session.get(Organization, organization_id)
    member = await session.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == user.id
        )
    )
    if organization is None or organization.deleted_at is not None or member is None:
        raise DashboardAccessError("You are not part of this company")
    is_admin = member.member_role == MemberRole.ADMIN.value
    profile = await session.scalar(
        select(Profile).where(
            Profile.organization_id == organization.id, Profile.kind == ProfileKind.COMPANY, Profile.deleted_at.is_(None)
        )
    )
    if profile is None:
        raise DashboardNotFoundError("Company profile not found")
    paid = company_plan_active(organization)
    slots = await has_availability(session, profile.id)
    condition = RequestParticipant.organization_id == organization.id
    if not is_admin:
        condition = and_(condition, RequestParticipant.assigned_user_id == user.id)
    rows = await _provider_rows(session, condition)

    insights = None
    if paid:
        insights = await _insights(session, rows, profile)
        open_rows = [(p, r) for p, r in rows if r.status not in CLOSED]
        insights.pipeline = {
            "unassigned": sum(p.assigned_user_id is None for p, _ in open_rows),
            "assigned": sum(p.assigned_user_id is not None and r.status is not RequestStatus.MEETING_BOOKED for p, r in open_rows),
            "meeting_booked": sum(r.status is RequestStatus.MEETING_BOOKED for _, r in open_rows),
            "completed": sum(r.status is RequestStatus.COMPLETED for _, r in rows),
        }
        if is_admin:
            members = (
                await session.execute(
                    select(OrganizationMember.member_role, User.id, User.full_name)
                    .join(User, User.id == OrganizationMember.user_id)
                    .where(OrganizationMember.organization_id == organization.id, User.deleted_at.is_(None))
                    .order_by(User.full_name)
                )
            ).all()
            insights.team = [
                TeamMemberStat(
                    user_id=member_id,
                    full_name=name,
                    member_role=role,
                    open=sum(p.assigned_user_id == member_id for p, _ in open_rows),
                    completed=sum(p.assigned_user_id == member_id and r.status is RequestStatus.COMPLETED for p, r in rows),
                )
                for role, member_id, name in members
            ]

    return ProviderDashboard(
        kind="company",
        profile_id=profile.id,
        name=organization.name,
        organization_id=organization.id,
        member_role=member.member_role,
        plan="enterprise",
        plan_active=paid,
        plan_expires_at=plan_expiry(organization.subscription_tier, organization.subscription_expires_at),
        leads=_lead_counts(rows),
        average_rating=float(profile.average_rating),
        review_count=profile.review_count,
        resolved_clients=await count_resolved_clients(session, profile),
        completeness=await _completeness(session, profile, paid, slots),
        has_availability=slots,
        upcoming_meetings=await _provider_meetings(session, profile.id),
        insights=insights,
        locked_insights=[] if paid else PROVIDER_INSIGHTS + COMPANY_INSIGHTS,
    )
