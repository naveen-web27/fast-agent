"""Service layer for submitting, listing, and messaging within customer requests."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import company_plan_active, require_plan
from app.features.booking.slots import bookable_profiles, request_appointments
from app.features.requests.schemas import (
    ContactInfo,
    CreateRequestPayload,
    CreateReviewPayload,
    DomainClientStat,
    ExpertReferralInfo,
    MemberOption,
    RequestDetail,
    RequestEventOut,
    RequestParticipantOut,
    RequestSummary,
    ReviewTargetOut,
    SocialLinkOut,
)
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, Profile, ProfileKind, Service, VerificationStatus
from app.models.request import Request, RequestEvent, RequestParticipant, RequestStatus
from app.models.review import Review
from app.models.social_link import SocialLink
from app.models.user import User, active_user_by_auth_id

# If a provider neither confirms nor disputes "done", reviews open anyway so they can't dodge ratings by staying silent.
COMPLETION_REVIEW_GRACE = timedelta(days=7)


class IdentityNotFoundError(Exception):
    """Raised when the caller hasn't completed onboarding yet."""


class ProfileTargetError(Exception):
    """Raised when a request is submitted against a profile that can't be found."""


class RequestNotFoundError(Exception):
    """Raised when the request doesn't exist."""


class RequestAccessError(Exception):
    """Raised when the caller isn't a participant of the request."""


class DuplicateInviteError(Exception):
    """Raised when the invited company is already part of the request."""


class RequestStateError(Exception):
    """Raised when an action isn't allowed in the request's current state."""


class DuplicateReviewError(Exception):
    """Raised when the caller already reviewed this profile on this request."""


async def _get_user(session: AsyncSession, auth_user_id: UUID) -> User:
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None:
        raise IdentityNotFoundError("Complete onboarding before using requests")
    return user


async def _my_organization_ids(session: AsyncSession, user_id: UUID) -> set[UUID]:
    """Companies whose whole request inbox the caller sees. Staff only see requests assigned to them."""
    rows = await session.scalars(
        select(OrganizationMember.organization_id)
        .join(Organization, Organization.id == OrganizationMember.organization_id)
        .where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.member_role == MemberRole.ADMIN.value,
            Organization.deleted_at.is_(None),
        )
    )
    return set(rows.all())


def _is_mine(participant: RequestParticipant, user: User, my_org_ids: set[UUID]) -> bool:
    return (
        participant.user_id == user.id
        or participant.assigned_user_id == user.id
        or (participant.organization_id is not None and participant.organization_id in my_org_ids)
    )


async def _social_links_for_profile(session: AsyncSession, profile_id: UUID) -> list[SocialLinkOut]:
    links = await session.scalars(select(SocialLink).where(SocialLink.profile_id == profile_id))
    return [SocialLinkOut(platform=link.platform, url=link.url) for link in links.all()]


async def _contact_info_for_user(session: AsyncSession, target_user: User) -> ContactInfo:
    """Contact card for an individual (customer or expert), including their expert profile's social links."""
    expert_profile = await session.scalar(
        select(Profile).where(
            Profile.user_id == target_user.id, Profile.kind == ProfileKind.EXPERT, Profile.deleted_at.is_(None)
        )
    )
    social_links = await _social_links_for_profile(session, expert_profile.id) if expert_profile is not None else []
    return ContactInfo(
        full_name=target_user.full_name,
        email=target_user.email,
        phone=target_user.phone,
        social_links=social_links,
    )


async def _contact_info_for_organization(
    session: AsyncSession, organization: Organization, assigned_user_id: UUID | None = None
) -> ContactInfo:
    """Contact card for a company: the assigned team member (or primary admin) plus the company's social links."""
    contact_user = await session.get(User, assigned_user_id) if assigned_user_id is not None else None
    if contact_user is None or contact_user.deleted_at is not None:
        admin_member = await session.scalar(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == organization.id, OrganizationMember.member_role == MemberRole.ADMIN.value)
            .order_by(OrganizationMember.created_at)
        )
        contact_user = await session.get(User, admin_member.user_id) if admin_member is not None else None
    company_profile = await session.scalar(
        select(Profile).where(Profile.organization_id == organization.id, Profile.kind == ProfileKind.COMPANY)
    )
    social_links = await _social_links_for_profile(session, company_profile.id) if company_profile is not None else []
    return ContactInfo(
        full_name=organization.name if assigned_user_id is None or contact_user is None else f"{contact_user.full_name} · {organization.name}",
        email=contact_user.email if contact_user is not None else None,
        phone=contact_user.phone if contact_user is not None else None,
        website_url=organization.website_url,
        social_links=social_links,
    )


async def _expert_client_stats(session: AsyncSession, expert_user_id: UUID) -> list[DomainClientStat]:
    """Distinct completed-request clients for this expert, grouped by the request's service domain."""
    stmt = (
        select(func.coalesce(Service.name, "General"), func.count(func.distinct(Request.customer_id)))
        .select_from(Request)
        .join(RequestParticipant, RequestParticipant.request_id == Request.id)
        .outerjoin(Service, Service.id == Request.service_id)
        .where(
            RequestParticipant.user_id == expert_user_id,
            RequestParticipant.participant_role == "expert",
            Request.status == RequestStatus.COMPLETED,
        )
        .group_by(Service.name)
    )
    rows = (await session.execute(stmt)).all()
    return [DomainClientStat(domain=domain, client_count=count) for domain, count in rows]


async def _expert_referral_info(
    session: AsyncSession, participants: list[RequestParticipant]
) -> ExpertReferralInfo | None:
    """Credibility snapshot of the expert on this request, so an invited company can vet them."""
    expert_participant = next((p for p in participants if p.participant_role == "expert" and p.user_id is not None), None)
    if expert_participant is None:
        return None
    profile = await session.scalar(
        select(Profile).where(
            Profile.user_id == expert_participant.user_id,
            Profile.kind == ProfileKind.EXPERT,
            Profile.deleted_at.is_(None),
        )
    )
    if profile is None:
        return None
    return ExpertReferralInfo(
        profile_id=profile.id,
        display_name=profile.display_name,
        headline=profile.headline,
        verified=profile.verification == VerificationStatus.VERIFIED,
        average_rating=float(profile.average_rating),
        review_count=profile.review_count,
        client_stats=await _expert_client_stats(session, expert_participant.user_id),
    )


async def _participant_display_name(session: AsyncSession, participant: RequestParticipant) -> str:
    if participant.user_id is not None:
        profile = await session.scalar(
            select(Profile).where(
                Profile.user_id == participant.user_id, Profile.kind == ProfileKind.EXPERT, Profile.deleted_at.is_(None)
            )
        )
        if profile is not None:
            return profile.display_name
        user = await session.get(User, participant.user_id)
        return user.full_name if user is not None else "Unknown"
    if participant.organization_id is not None:
        organization = await session.get(Organization, participant.organization_id)
        return organization.name if organization is not None else "Unknown company"
    return "Unknown"


def _my_participants(
    participants: list[RequestParticipant], user: User, my_org_ids: set[UUID]
) -> list[RequestParticipant]:
    return [participant for participant in participants if _is_mine(participant, user, my_org_ids)]


async def _participant_profile(session: AsyncSession, participant: RequestParticipant) -> Profile | None:
    if participant.user_id is not None:
        return await session.scalar(
            select(Profile).where(
                Profile.user_id == participant.user_id, Profile.kind == ProfileKind.EXPERT, Profile.deleted_at.is_(None)
            )
        )
    return await session.scalar(
        select(Profile).where(Profile.organization_id == participant.organization_id, Profile.kind == ProfileKind.COMPANY)
    )


async def _review_targets(
    session: AsyncSession,
    request: Request,
    user: User,
    my_org_ids: set[UUID],
    participants: list[RequestParticipant],
) -> list[ReviewTargetOut]:
    """Who the viewer may rate: customer -> every accepted provider; accepted expert -> accepted company."""
    if request.status is not RequestStatus.COMPLETED:
        return []

    if request.customer_id == user.id:
        reviewer_confirmed = True
        candidates = [p for p in participants if p.accepted_at is not None]
    else:
        mine = [p for p in _my_participants(participants, user, my_org_ids) if p.participant_role == "expert" and p.accepted_at is not None]
        if not mine or all(p.completion_disputed_at is not None for p in mine):
            return []
        reviewer_confirmed = any(p.completion_confirmed_at is not None for p in mine)
        candidates = [p for p in participants if p.participant_role == "company" and p.accepted_at is not None]
    if not candidates:
        return []

    reviewed_profile_ids = set(
        (
            await session.scalars(
                select(Review.profile_id).where(Review.request_id == request.id, Review.reviewer_id == user.id)
            )
        ).all()
    )
    opens_at = (request.completed_at or request.updated_at) + COMPLETION_REVIEW_GRACE
    now = datetime.now(timezone.utc)

    targets = []
    for participant in candidates:
        profile = await _participant_profile(session, participant)
        if profile is None or profile.user_id == user.id:
            continue
        if profile.id in reviewed_profile_ids:
            state = "reviewed"
        elif participant.completion_disputed_at is not None:
            state = "disputed"
        elif not reviewer_confirmed:
            state = "confirm_first"
        elif participant.completion_confirmed_at is not None or now >= opens_at:
            state = "open"
        else:
            state = "waiting"
        targets.append(
            ReviewTargetOut(
                profile_id=profile.id,
                name=profile.display_name,
                participant_role=participant.participant_role,
                state=state,
                opens_at=opens_at if state == "waiting" else None,
            )
        )
    return targets


async def _pending_action(
    session: AsyncSession,
    request: Request,
    user: User,
    my_org_ids: set[UUID],
    participants: list[RequestParticipant],
) -> str | None:
    """The one thing the viewer still needs to do on this request, used for the red notification count."""
    if request.status is RequestStatus.CANCELLED:
        return None
    mine = [] if request.customer_id == user.id else _my_participants(participants, user, my_org_ids)
    if request.status is not RequestStatus.COMPLETED:
        return "accept" if any(p.accepted_at is None for p in mine) else None
    if any(
        p.accepted_at is not None and p.completion_confirmed_at is None and p.completion_disputed_at is None for p in mine
    ):
        return "confirm_completion"
    targets = await _review_targets(session, request, user, my_org_ids, participants)
    return "review" if any(target.state == "open" for target in targets) else None


async def _build_summary(
    session: AsyncSession, request: Request, user: User, my_org_ids: set[UUID], participants: list[RequestParticipant]
) -> RequestSummary:
    assigned_to_name = None
    customer_looking = True
    if request.customer_id == user.id:
        my_role = "customer"
        names = [await _participant_display_name(session, participant) for participant in participants]
        counterpart_name = ", ".join(names) if names else "Awaiting a match"
    else:
        mine = next((participant for participant in participants if _is_mine(participant, user, my_org_ids)), None)
        my_role = mine.participant_role if mine is not None else "expert"
        customer = await session.get(User, request.customer_id)
        counterpart_name = customer.full_name if customer is not None else "Customer"
        customer_looking = customer is not None and customer.looking_for_help
        if mine is not None and mine.assigned_user_id is not None:
            assignee = await session.get(User, mine.assigned_user_id)
            assigned_to_name = assignee.full_name if assignee is not None else None

    return RequestSummary(
        id=request.id,
        title=request.title,
        requirements=request.requirements,
        city=request.city,
        status=request.status.value,
        my_role=my_role,
        counterpart_name=counterpart_name,
        pending_action=await _pending_action(session, request, user, my_org_ids, participants),
        assigned_to_name=assigned_to_name,
        customer_looking=customer_looking,
        completed_at=request.completed_at,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


async def _build_detail(
    session: AsyncSession,
    request: Request,
    user: User,
    my_org_ids: set[UUID],
    participants: list[RequestParticipant] | None = None,
) -> RequestDetail:
    if participants is None:
        participants = (
            await session.scalars(select(RequestParticipant).where(RequestParticipant.request_id == request.id))
        ).all()
    summary = await _build_summary(session, request, user, my_org_ids, list(participants))

    # The customer never gets an explicit request_participants row, so synthesize their entry here.
    # They're treated as always-accepted since they're the one who opened the request.
    viewer_is_customer = request.customer_id == user.id
    viewer_participant = next((participant for participant in participants if _is_mine(participant, user, my_org_ids)), None)
    viewer_accepted = viewer_is_customer or (viewer_participant is not None and viewer_participant.accepted_at is not None)

    customer_user = await session.get(User, request.customer_id)
    participant_payload = [
        RequestParticipantOut(
            participant_role="customer",
            name=customer_user.full_name if customer_user is not None else "Customer",
            accepted_at=request.created_at,
            contact=await _contact_info_for_user(session, customer_user) if viewer_accepted and customer_user is not None else None,
        )
    ]
    for participant in participants:
        entry_accepted = participant.accepted_at is not None
        contact = None
        if entry_accepted and viewer_accepted:
            if participant.user_id is not None:
                participant_user = await session.get(User, participant.user_id)
                contact = await _contact_info_for_user(session, participant_user) if participant_user is not None else None
            elif participant.organization_id is not None:
                organization = await session.get(Organization, participant.organization_id)
                contact = (
                    await _contact_info_for_organization(session, organization, participant.assigned_user_id)
                    if organization is not None
                    else None
                )
        assignee = await session.get(User, participant.assigned_user_id) if participant.assigned_user_id else None
        participant_payload.append(
            RequestParticipantOut(
                participant_role=participant.participant_role,
                name=await _participant_display_name(session, participant),
                accepted_at=participant.accepted_at,
                completion_confirmed_at=participant.completion_confirmed_at,
                completion_disputed_at=participant.completion_disputed_at,
                assigned_to_name=assignee.full_name if assignee is not None else None,
                contact=contact,
            )
        )

    events = (
        await session.scalars(
            select(RequestEvent).where(RequestEvent.request_id == request.id).order_by(RequestEvent.created_at)
        )
    ).all()
    event_payload = []
    for event in events:
        author = await session.get(User, event.author_id) if event.author_id is not None else None
        event_payload.append(
            RequestEventOut(
                id=event.id,
                author_name=author.full_name if author is not None else None,
                is_mine=event.author_id == user.id,
                event_type=event.event_type,
                message=event.message,
                created_at=event.created_at,
            )
        )

    expert_referral = await _expert_referral_info(session, list(participants))
    can_mark_done = (
        viewer_is_customer
        and request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED)
        and any(participant.accepted_at is not None for participant in participants)
    )

    # Company admins on an Enterprise plan can hand the request to a team member.
    assignable_members: list[MemberOption] = []
    admin_company = next(
        (p for p in participants if p.organization_id is not None and p.organization_id in my_org_ids), None
    )
    if admin_company is not None and company_plan_active(await session.get(Organization, admin_company.organization_id)):
        member_rows = (
            await session.execute(
                select(User.id, User.full_name, OrganizationMember.member_role)
                .join(OrganizationMember, OrganizationMember.user_id == User.id)
                .where(OrganizationMember.organization_id == admin_company.organization_id, User.deleted_at.is_(None))
                .order_by(User.full_name)
            )
        ).all()
        assignable_members = [
            MemberOption(user_id=member_id, full_name=name, member_role=role) for member_id, name, role in member_rows
        ]

    open_request = request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED)
    return RequestDetail(
        **summary.model_dump(),
        participants=participant_payload,
        events=event_payload,
        expert_referral=expert_referral,
        can_mark_done=can_mark_done,
        review_targets=await _review_targets(session, request, user, my_org_ids, list(participants)),
        can_assign=bool(assignable_members),
        assignable_members=assignable_members,
        assigned_user_id=admin_company.assigned_user_id if admin_company is not None else None,
        appointments=await request_appointments(session, request.id),
        bookable_profiles=await bookable_profiles(session, list(participants)) if viewer_is_customer and open_request else [],
    )


def _is_participant(request: Request, user: User, my_org_ids: set[UUID], participants: list[RequestParticipant]) -> bool:
    if request.customer_id == user.id:
        return True
    return any(_is_mine(participant, user, my_org_ids) for participant in participants)


async def create_request(session: AsyncSession, auth_user_id: UUID, payload: CreateRequestPayload) -> RequestDetail:
    """Create a request that targets one specific expert or company profile."""
    user = await _get_user(session, auth_user_id)

    profile = await session.get(Profile, payload.profile_id)
    if profile is None or profile.blocked_at is not None or profile.deleted_at is not None:
        raise ProfileTargetError("This profile could not be found")
    if profile.user_id == user.id or (
        profile.organization_id is not None and profile.organization_id in await _my_organization_ids(session, user.id)
    ):
        raise ProfileTargetError("This is your own profile. You can't send a request to yourself.")

    request = Request(
        customer_id=user.id,
        service_id=payload.service_id,
        title=payload.title,
        requirements=payload.requirements,
        city=payload.city,
        status=RequestStatus.SUBMITTED,
    )
    session.add(request)
    # A new request means a new need, so the customer is looking again.
    user.looking_for_help = True
    user.need_fulfilled_at = None
    await session.flush()

    if profile.kind is ProfileKind.EXPERT:
        session.add(RequestParticipant(request_id=request.id, user_id=profile.user_id, participant_role="expert"))
    else:
        session.add(
            RequestParticipant(request_id=request.id, organization_id=profile.organization_id, participant_role="company")
        )

    await session.commit()
    await session.refresh(request)

    my_org_ids = await _my_organization_ids(session, user.id)
    return await _build_detail(session, request, user, my_org_ids)


async def list_requests(session: AsyncSession, auth_user_id: UUID) -> list[RequestSummary]:
    """Return every request the caller is part of, as a customer, expert, or company admin."""
    user = await _get_user(session, auth_user_id)
    my_org_ids = await _my_organization_ids(session, user.id)

    conditions = [
        Request.customer_id == user.id,
        RequestParticipant.user_id == user.id,
        RequestParticipant.assigned_user_id == user.id,
    ]
    if my_org_ids:
        conditions.append(RequestParticipant.organization_id.in_(my_org_ids))

    rows = await session.scalars(
        select(Request)
        .outerjoin(RequestParticipant, RequestParticipant.request_id == Request.id)
        .where(or_(*conditions))
        .distinct()
        .order_by(Request.updated_at.desc())
    )
    requests = rows.all()
    if not requests:
        return []

    participants_by_request: dict[UUID, list[RequestParticipant]] = {request.id: [] for request in requests}
    all_participants = await session.scalars(
        select(RequestParticipant).where(RequestParticipant.request_id.in_(participants_by_request.keys()))
    )
    for participant in all_participants.all():
        participants_by_request[participant.request_id].append(participant)

    return [
        await _build_summary(session, request, user, my_org_ids, participants_by_request[request.id])
        for request in requests
    ]


def _or(conditions):
    from sqlalchemy import or_

    return or_(*conditions)


async def get_request_detail(session: AsyncSession, auth_user_id: UUID, request_id: UUID) -> RequestDetail:
    """Return full detail for one request, if the caller is a participant."""
    user = await _get_user(session, auth_user_id)
    request = await session.get(Request, request_id)
    if request is None:
        raise RequestNotFoundError("Request not found")

    my_org_ids = await _my_organization_ids(session, user.id)
    participants = (
        await session.scalars(select(RequestParticipant).where(RequestParticipant.request_id == request.id))
    ).all()
    if not _is_participant(request, user, my_org_ids, list(participants)):
        raise RequestAccessError("You do not have access to this request")

    return await _build_detail(session, request, user, my_org_ids, list(participants))


async def add_event(session: AsyncSession, auth_user_id: UUID, request_id: UUID, message: str) -> RequestDetail:
    """Post a message to the request's shared timeline."""
    user = await _get_user(session, auth_user_id)
    request = await session.get(Request, request_id)
    if request is None:
        raise RequestNotFoundError("Request not found")

    my_org_ids = await _my_organization_ids(session, user.id)
    participants = (
        await session.scalars(select(RequestParticipant).where(RequestParticipant.request_id == request.id))
    ).all()
    if not _is_participant(request, user, my_org_ids, list(participants)):
        raise RequestAccessError("You do not have access to this request")

    session.add(RequestEvent(request_id=request.id, author_id=user.id, event_type="message", message=message))
    request.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(request)

    return await _build_detail(session, request, user, my_org_ids, list(participants))


async def accept_request(session: AsyncSession, auth_user_id: UUID, request_id: UUID) -> RequestDetail:
    """Let the invited expert or company admin accept the request."""
    user = await _get_user(session, auth_user_id)
    request = await session.get(Request, request_id)
    if request is None:
        raise RequestNotFoundError("Request not found")

    my_org_ids = await _my_organization_ids(session, user.id)
    participants = (
        await session.scalars(select(RequestParticipant).where(RequestParticipant.request_id == request.id))
    ).all()
    mine = next((participant for participant in participants if _is_mine(participant, user, my_org_ids)), None)
    if mine is None:
        raise RequestAccessError("Only the invited expert or company can accept this request")

    mine.accepted_at = datetime.now(timezone.utc)
    if request.status is RequestStatus.SUBMITTED:
        request.status = RequestStatus.ACCEPTED
    request.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(request)

    return await _build_detail(session, request, user, my_org_ids)


async def invite_company(session: AsyncSession, auth_user_id: UUID, request_id: UUID, profile_id: UUID) -> RequestDetail:
    """Let an expert who has accepted this request bring a company profile in as a co-participant."""
    user = await _get_user(session, auth_user_id)
    request = await session.get(Request, request_id)
    if request is None:
        raise RequestNotFoundError("Request not found")

    participants = (
        await session.scalars(select(RequestParticipant).where(RequestParticipant.request_id == request.id))
    ).all()
    mine = next(
        (p for p in participants if p.participant_role == "expert" and p.user_id == user.id and p.accepted_at is not None),
        None,
    )
    if mine is None:
        raise RequestAccessError("Only an expert who has accepted this request can invite a company")

    profile = await session.get(Profile, profile_id)
    if (
        profile is None
        or profile.kind is not ProfileKind.COMPANY
        or profile.blocked_at is not None
        or profile.deleted_at is not None
    ):
        raise ProfileTargetError("Choose a valid company profile to invite")

    if any(p.organization_id == profile.organization_id for p in participants if p.organization_id is not None):
        raise DuplicateInviteError("This company is already part of the request")

    session.add(
        RequestParticipant(request_id=request.id, organization_id=profile.organization_id, participant_role="company")
    )
    session.add(
        RequestEvent(
            request_id=request.id,
            author_id=user.id,
            event_type="system",
            message=f"{profile.display_name} was invited into this request.",
        )
    )
    if request.status in (RequestStatus.ACCEPTED, RequestStatus.SUBMITTED):
        request.status = RequestStatus.PROVIDER_INVITED
    request.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(request)

    my_org_ids = await _my_organization_ids(session, user.id)
    return await _build_detail(session, request, user, my_org_ids)


async def _load_request_for_participant(
    session: AsyncSession, auth_user_id: UUID, request_id: UUID
) -> tuple[User, Request, set[UUID], list[RequestParticipant]]:
    user = await _get_user(session, auth_user_id)
    request = await session.get(Request, request_id)
    if request is None:
        raise RequestNotFoundError("Request not found")
    my_org_ids = await _my_organization_ids(session, user.id)
    participants = list(
        (await session.scalars(select(RequestParticipant).where(RequestParticipant.request_id == request.id))).all()
    )
    if not _is_participant(request, user, my_org_ids, participants):
        raise RequestAccessError("You do not have access to this request")
    return user, request, my_org_ids, participants


async def mark_request_done(session: AsyncSession, auth_user_id: UUID, request_id: UUID) -> RequestDetail:
    """Customer closes the request; accepted providers are then asked to confirm before reviews open."""
    user, request, my_org_ids, participants = await _load_request_for_participant(session, auth_user_id, request_id)
    if request.customer_id != user.id:
        raise RequestAccessError("Only the customer can mark this request as done")
    if request.status in (RequestStatus.COMPLETED, RequestStatus.CANCELLED):
        raise RequestStateError("This request is already closed")
    if not any(participant.accepted_at is not None for participant in participants):
        raise RequestStateError("Wait for an expert or company to accept before marking this as done")

    now = datetime.now(timezone.utc)
    request.status = RequestStatus.COMPLETED
    request.completed_at = now
    request.updated_at = now
    session.add(
        RequestEvent(
            request_id=request.id,
            author_id=user.id,
            event_type="system",
            message=f"{user.full_name} marked this request as done. Please confirm so ratings can open.",
        )
    )
    await session.commit()
    await session.refresh(request)
    return await _build_detail(session, request, user, my_org_ids)


async def respond_to_completion(
    session: AsyncSession, auth_user_id: UUID, request_id: UUID, confirm: bool, reason: str | None = None
) -> RequestDetail:
    """An accepted expert/company confirms the work is done, or reports a problem (which blocks reviews of them)."""
    user, request, my_org_ids, participants = await _load_request_for_participant(session, auth_user_id, request_id)
    mine = [p for p in _my_participants(participants, user, my_org_ids) if p.accepted_at is not None]
    if request.customer_id == user.id or not mine:
        raise RequestAccessError("Only an expert or company who accepted this request can respond")
    if request.status is not RequestStatus.COMPLETED:
        raise RequestStateError("The customer has not marked this request as done yet")
    pending = [p for p in mine if p.completion_confirmed_at is None and p.completion_disputed_at is None]
    if not pending:
        raise RequestStateError("You already responded to this request")

    now = datetime.now(timezone.utc)
    for participant in pending:
        if confirm:
            participant.completion_confirmed_at = now
        else:
            participant.completion_disputed_at = now
    message = (
        f"{user.full_name} confirmed this request is done."
        if confirm
        else f"{user.full_name} reported a problem with closing this request: {reason}"
    )
    session.add(RequestEvent(request_id=request.id, author_id=user.id, event_type="system", message=message))
    request.updated_at = now
    await session.commit()
    await session.refresh(request)
    return await _build_detail(session, request, user, my_org_ids)


async def create_review(
    session: AsyncSession, auth_user_id: UUID, request_id: UUID, payload: CreateReviewPayload
) -> RequestDetail:
    """Rate an expert/company on a completed request, once both sides have agreed it's done."""
    user, request, my_org_ids, participants = await _load_request_for_participant(session, auth_user_id, request_id)
    targets = await _review_targets(session, request, user, my_org_ids, participants)
    target = next((t for t in targets if t.profile_id == payload.profile_id), None)
    if target is None:
        raise RequestAccessError("You can't rate this profile on this request")
    if target.state == "reviewed":
        raise DuplicateReviewError("You already rated this profile for this request")
    if target.state != "open":
        raise RequestStateError(
            {
                "waiting": "Ratings open once they confirm the request is done, or automatically after 7 days",
                "disputed": "They reported a problem with this request, so ratings are on hold. Contact support",
                "confirm_first": "Confirm the request is done before rating",
            }[target.state]
        )

    session.add(
        Review(
            request_id=request.id,
            reviewer_id=user.id,
            profile_id=payload.profile_id,
            rating=payload.rating,
            body=payload.body,
            verified_interaction=True,
        )
    )
    # Incremental average keeps any existing (seeded/imported) aggregate intact.
    profile = await session.get(Profile, payload.profile_id)
    total = float(profile.average_rating) * profile.review_count + payload.rating
    profile.review_count += 1
    profile.average_rating = round(total / profile.review_count, 1)
    request.updated_at = datetime.now(timezone.utc)
    if request.customer_id == user.id and user.looking_for_help:
        still_open = await session.scalar(
            select(Request.id)
            .where(
                Request.customer_id == user.id,
                Request.status.notin_((RequestStatus.COMPLETED, RequestStatus.CANCELLED)),
            )
            .limit(1)
        )
        if still_open is None:
            user.looking_for_help = False
            user.need_fulfilled_at = request.updated_at
    await session.commit()
    await session.refresh(request)
    return await _build_detail(session, request, user, my_org_ids)


async def assign_request(
    session: AsyncSession, auth_user_id: UUID, request_id: UUID, assignee_id: UUID | None
) -> RequestDetail:
    """Company admin hands the company's side of a request to a team member (Enterprise)."""
    user, request, my_org_ids, participants = await _load_request_for_participant(session, auth_user_id, request_id)
    company_participant = next(
        (p for p in participants if p.organization_id is not None and p.organization_id in my_org_ids), None
    )
    if company_participant is None:
        raise RequestAccessError("Only an admin of the company on this request can assign it")
    organization = await session.get(Organization, company_participant.organization_id)
    require_plan(company_plan_active(organization), ProfileKind.COMPANY, "Assigning requests to your team")

    assignee = None
    if assignee_id is not None:
        is_member = await session.scalar(
            select(OrganizationMember.id).where(
                OrganizationMember.organization_id == organization.id, OrganizationMember.user_id == assignee_id
            )
        )
        assignee = await session.get(User, assignee_id) if is_member else None
        if assignee is None or assignee.deleted_at is not None:
            raise RequestStateError("Choose someone from your company team")

    company_participant.assigned_user_id = assignee_id
    message = (
        f"{organization.name} assigned this request to {assignee.full_name}."
        if assignee is not None
        else f"{organization.name} unassigned this request."
    )
    session.add(RequestEvent(request_id=request.id, author_id=user.id, event_type="system", message=message))
    request.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(request)
    return await _build_detail(session, request, user, my_org_ids)
