"""Booking a meeting slot on a request, and cancelling it."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.booking.schemas import BookAppointmentPayload, SlotsResponse
from app.features.booking.slots import ACTIVE_STATUSES, LOCAL_TZ, SLOT_MINUTES, available_slots, bookable_profiles
from app.features.requests.schemas import RequestDetail
from app.features.requests.service import (
    RequestAccessError,
    RequestStateError,
    _build_detail,
    _load_request_for_participant,
)
from app.models.availability import Appointment
from app.models.profile import Profile
from app.models.request import RequestEvent, RequestParticipant, RequestStatus

CLOSED = (RequestStatus.COMPLETED, RequestStatus.CANCELLED)


def _when(moment: datetime) -> str:
    return moment.astimezone(LOCAL_TZ).strftime("%a %d %b, %I:%M %p IST")


async def _bookable_target(session: AsyncSession, participants: list[RequestParticipant], profile_id: UUID) -> Profile:
    if not any(target.profile_id == profile_id for target in await bookable_profiles(session, participants)):
        raise RequestStateError("This provider isn't taking online bookings on this request")
    return await session.get(Profile, profile_id)


async def get_request_slots(session: AsyncSession, auth_user_id: UUID, request_id: UUID, profile_id: UUID) -> SlotsResponse:
    _, _, _, participants = await _load_request_for_participant(session, auth_user_id, request_id)
    profile = await _bookable_target(session, participants, profile_id)
    return SlotsResponse(
        profile_id=profile.id,
        name=profile.display_name,
        slot_minutes=SLOT_MINUTES,
        slots=await available_slots(session, profile),
    )


async def book_appointment(
    session: AsyncSession, auth_user_id: UUID, request_id: UUID, payload: BookAppointmentPayload
) -> RequestDetail:
    """Customer picks one of the provider's open slots; it's confirmed immediately."""
    user, request, my_org_ids, participants = await _load_request_for_participant(session, auth_user_id, request_id)
    if request.customer_id != user.id:
        raise RequestAccessError("Only the customer can book a meeting on this request")
    if request.status in CLOSED:
        raise RequestStateError("This request is already closed")
    profile = await _bookable_target(session, participants, payload.profile_id)
    if payload.starts_at not in await available_slots(session, profile):
        raise RequestStateError("That time is no longer available. Pick another slot")

    session.add(
        Appointment(
            request_id=request.id,
            profile_id=profile.id,
            booked_by=user.id,
            starts_at=payload.starts_at,
            ends_at=payload.starts_at + timedelta(minutes=SLOT_MINUTES),
            status="confirmed",
        )
    )
    session.add(
        RequestEvent(
            request_id=request.id,
            author_id=user.id,
            event_type="system",
            message=f"Meeting booked with {profile.display_name} on {_when(payload.starts_at)}.",
        )
    )
    request.status = RequestStatus.MEETING_BOOKED
    request.updated_at = datetime.now(timezone.utc)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise RequestStateError("Someone just booked that time. Pick another slot") from exc
    await session.refresh(request)
    return await _build_detail(session, request, user, my_org_ids)


async def cancel_appointment(session: AsyncSession, auth_user_id: UUID, request_id: UUID, appointment_id: UUID) -> RequestDetail:
    """Any participant can cancel an upcoming meeting; the slot opens again."""
    user, request, my_org_ids, _ = await _load_request_for_participant(session, auth_user_id, request_id)
    appointment = await session.get(Appointment, appointment_id)
    if appointment is None or appointment.request_id != request.id or appointment.status not in ACTIVE_STATUSES:
        raise RequestStateError("This meeting can't be cancelled")

    appointment.status = "cancelled"
    session.add(
        RequestEvent(
            request_id=request.id,
            author_id=user.id,
            event_type="system",
            message=f"{user.full_name} cancelled the meeting on {_when(appointment.starts_at)}.",
        )
    )
    await session.flush()
    still_booked = await session.scalar(
        select(Appointment.id).where(Appointment.request_id == request.id, Appointment.status.in_(ACTIVE_STATUSES)).limit(1)
    )
    if request.status is RequestStatus.MEETING_BOOKED and still_booked is None:
        request.status = RequestStatus.ACCEPTED
    request.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(request)
    return await _build_detail(session, request, user, my_org_ids)
