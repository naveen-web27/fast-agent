"""Slot generation and read helpers for meetings, shared with the requests feature."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import profile_plan_active
from app.features.requests.schemas import AppointmentOut, BookableProfileOut
from app.models.availability import Appointment, AvailabilitySlot
from app.models.profile import Profile, ProfileKind
from app.models.request import RequestParticipant

# India has no DST, so a fixed offset avoids depending on the host's tz database.
LOCAL_TZ = timezone(timedelta(hours=5, minutes=30), "IST")
SLOT_MINUTES = 30
BOOKING_DAYS = 14
MIN_NOTICE = timedelta(hours=2)
ACTIVE_STATUSES = ("proposed", "confirmed")


async def participant_profile(session: AsyncSession, participant: RequestParticipant) -> Profile | None:
    if participant.user_id is not None:
        condition = (Profile.user_id == participant.user_id, Profile.kind == ProfileKind.EXPERT)
    else:
        condition = (Profile.organization_id == participant.organization_id, Profile.kind == ProfileKind.COMPANY)
    return await session.scalar(
        select(Profile).where(*condition, Profile.deleted_at.is_(None), Profile.blocked_at.is_(None))
    )


async def has_availability(session: AsyncSession, profile_id: UUID) -> bool:
    return (await session.scalar(select(AvailabilitySlot.id).where(AvailabilitySlot.profile_id == profile_id).limit(1))) is not None


async def bookable_profiles(session: AsyncSession, participants: list[RequestParticipant]) -> list[BookableProfileOut]:
    """Accepted providers on a paid plan who have published weekly availability."""
    result = []
    for participant in participants:
        if participant.accepted_at is None:
            continue
        profile = await participant_profile(session, participant)
        if profile is None or not await profile_plan_active(session, profile) or not await has_availability(session, profile.id):
            continue
        result.append(BookableProfileOut(profile_id=profile.id, name=profile.display_name))
    return result


async def available_slots(session: AsyncSession, profile: Profile) -> list[datetime]:
    """Open 30-minute slots over the next two weeks, skipping anything already booked."""
    windows = (await session.scalars(select(AvailabilitySlot).where(AvailabilitySlot.profile_id == profile.id))).all()
    if not windows:
        return []
    now = datetime.now(timezone.utc)
    booked = (
        await session.execute(
            select(Appointment.starts_at, Appointment.ends_at).where(
                Appointment.profile_id == profile.id,
                Appointment.status.in_(ACTIVE_STATUSES),
                Appointment.ends_at > now,
            )
        )
    ).all()
    step = timedelta(minutes=SLOT_MINUTES)
    today = now.astimezone(LOCAL_TZ).date()
    slots: set[datetime] = set()
    for offset in range(BOOKING_DAYS):
        day = today + timedelta(days=offset)
        for window in windows:
            if window.weekday != day.weekday():
                continue
            start = datetime.combine(day, window.start_time, tzinfo=LOCAL_TZ)
            end = datetime.combine(day, window.end_time, tzinfo=LOCAL_TZ)
            while start + step <= end:
                overlaps = any(booked_start < start + step and start < booked_end for booked_start, booked_end in booked)
                if start >= now + MIN_NOTICE and not overlaps:
                    slots.add(start)
                start += step
    return sorted(slots)


async def request_appointments(session: AsyncSession, request_id: UUID) -> list[AppointmentOut]:
    rows = (
        await session.execute(
            select(Appointment, Profile.display_name)
            .outerjoin(Profile, Profile.id == Appointment.profile_id)
            .where(Appointment.request_id == request_id)
            .order_by(Appointment.starts_at)
        )
    ).all()
    return [
        AppointmentOut(
            id=appointment.id,
            profile_id=appointment.profile_id,
            with_name=name or "Meeting",
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            status=appointment.status,
        )
        for appointment, name in rows
    ]
