"""Service layer for submitting, listing, and messaging within customer requests."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.requests.schemas import (
    CreateRequestPayload,
    RequestDetail,
    RequestEventOut,
    RequestParticipantOut,
    RequestSummary,
)
from app.models.organization_member import OrganizationMember
from app.models.profile import Organization, Profile, ProfileKind
from app.models.request import Request, RequestEvent, RequestParticipant, RequestStatus
from app.models.user import User


class IdentityNotFoundError(Exception):
    """Raised when the caller hasn't completed onboarding yet."""


class ProfileTargetError(Exception):
    """Raised when a request is submitted against a profile that can't be found."""


class RequestNotFoundError(Exception):
    """Raised when the request doesn't exist."""


class RequestAccessError(Exception):
    """Raised when the caller isn't a participant of the request."""


async def _get_user(session: AsyncSession, auth_user_id: UUID) -> User:
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        raise IdentityNotFoundError("Complete onboarding before using requests")
    return user


async def _my_organization_ids(session: AsyncSession, user_id: UUID) -> set[UUID]:
    rows = await session.scalars(select(OrganizationMember.organization_id).where(OrganizationMember.user_id == user_id))
    return set(rows.all())


async def _participant_display_name(session: AsyncSession, participant: RequestParticipant) -> str:
    if participant.user_id is not None:
        profile = await session.scalar(
            select(Profile).where(Profile.user_id == participant.user_id, Profile.kind == ProfileKind.EXPERT)
        )
        if profile is not None:
            return profile.display_name
        user = await session.get(User, participant.user_id)
        return user.full_name if user is not None else "Unknown"
    if participant.organization_id is not None:
        organization = await session.get(Organization, participant.organization_id)
        return organization.name if organization is not None else "Unknown company"
    return "Unknown"


async def _build_summary(
    session: AsyncSession, request: Request, user: User, my_org_ids: set[UUID], participants: list[RequestParticipant]
) -> RequestSummary:
    if request.customer_id == user.id:
        my_role = "customer"
        names = [await _participant_display_name(session, participant) for participant in participants]
        counterpart_name = ", ".join(names) if names else "Awaiting a match"
    else:
        mine = next(
            (
                participant
                for participant in participants
                if participant.user_id == user.id
                or (participant.organization_id is not None and participant.organization_id in my_org_ids)
            ),
            None,
        )
        my_role = mine.participant_role if mine is not None else "expert"
        customer = await session.get(User, request.customer_id)
        counterpart_name = customer.full_name if customer is not None else "Customer"

    return RequestSummary(
        id=request.id,
        title=request.title,
        requirements=request.requirements,
        city=request.city,
        status=request.status.value,
        my_role=my_role,
        counterpart_name=counterpart_name,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


async def _build_detail(session: AsyncSession, request: Request, user: User, my_org_ids: set[UUID]) -> RequestDetail:
    participants = (
        await session.scalars(select(RequestParticipant).where(RequestParticipant.request_id == request.id))
    ).all()
    summary = await _build_summary(session, request, user, my_org_ids, list(participants))

    participant_payload = [
        RequestParticipantOut(
            participant_role=participant.participant_role,
            name=await _participant_display_name(session, participant),
            accepted_at=participant.accepted_at,
        )
        for participant in participants
    ]

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
                event_type=event.event_type,
                message=event.message,
                created_at=event.created_at,
            )
        )

    return RequestDetail(**summary.model_dump(), participants=participant_payload, events=event_payload)


def _is_participant(request: Request, user: User, my_org_ids: set[UUID], participants: list[RequestParticipant]) -> bool:
    if request.customer_id == user.id:
        return True
    return any(
        participant.user_id == user.id or (participant.organization_id is not None and participant.organization_id in my_org_ids)
        for participant in participants
    )


async def create_request(session: AsyncSession, auth_user_id: UUID, payload: CreateRequestPayload) -> RequestDetail:
    """Create a request that targets one specific expert or company profile."""
    user = await _get_user(session, auth_user_id)

    profile = await session.get(Profile, payload.profile_id)
    if profile is None:
        raise ProfileTargetError("This profile could not be found")

    request = Request(
        customer_id=user.id,
        title=payload.title,
        requirements=payload.requirements,
        city=payload.city,
        status=RequestStatus.SUBMITTED,
    )
    session.add(request)
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

    conditions = [Request.customer_id == user.id, RequestParticipant.user_id == user.id]
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

    summaries = []
    for request in requests:
        participants = (
            await session.scalars(select(RequestParticipant).where(RequestParticipant.request_id == request.id))
        ).all()
        summaries.append(await _build_summary(session, request, user, my_org_ids, list(participants)))
    return summaries


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

    return await _build_detail(session, request, user, my_org_ids)


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

    return await _build_detail(session, request, user, my_org_ids)


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
    mine = next(
        (
            participant
            for participant in participants
            if participant.user_id == user.id
            or (participant.organization_id is not None and participant.organization_id in my_org_ids)
        ),
        None,
    )
    if mine is None:
        raise RequestAccessError("Only the invited expert or company can accept this request")

    mine.accepted_at = datetime.now(timezone.utc)
    if request.status is RequestStatus.SUBMITTED:
        request.status = RequestStatus.ACCEPTED
    request.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(request)

    return await _build_detail(session, request, user, my_org_ids)
