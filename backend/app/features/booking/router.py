"""HTTP endpoints for booking meetings on a request."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.booking.schemas import BookAppointmentPayload, SlotsResponse
from app.features.booking.service import book_appointment, cancel_appointment, get_request_slots
from app.features.requests.schemas import RequestDetail
from app.features.requests.service import (
    IdentityNotFoundError,
    RequestAccessError,
    RequestNotFoundError,
    RequestStateError,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


def _raise_http(exc: Exception) -> None:
    if isinstance(exc, (IdentityNotFoundError, RequestNotFoundError)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, RequestAccessError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


_HANDLED = (IdentityNotFoundError, RequestNotFoundError, RequestAccessError, RequestStateError)


@router.get("/{request_id}/slots", response_model=SlotsResponse)
async def list_slots(
    request_id: UUID,
    profile_id: UUID = Query(),
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> SlotsResponse:
    """Open meeting slots for an accepted provider on this request."""
    try:
        return await get_request_slots(session, auth_user_id, request_id, profile_id)
    except _HANDLED as exc:
        _raise_http(exc)


@router.post("/{request_id}/appointments", response_model=RequestDetail, status_code=status.HTTP_201_CREATED)
async def book(
    request_id: UUID,
    payload: BookAppointmentPayload,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Customer books one of the provider's open slots."""
    try:
        return await book_appointment(session, auth_user_id, request_id, payload)
    except _HANDLED as exc:
        _raise_http(exc)


@router.post("/{request_id}/appointments/{appointment_id}/cancel", response_model=RequestDetail)
async def cancel(
    request_id: UUID,
    appointment_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Cancel an upcoming meeting so the slot opens again."""
    try:
        return await cancel_appointment(session, auth_user_id, request_id, appointment_id)
    except _HANDLED as exc:
        _raise_http(exc)
