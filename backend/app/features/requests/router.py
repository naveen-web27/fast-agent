"""HTTP endpoints for the customer <-> expert/company request workflow."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.requests.schemas import AddEventPayload, CreateRequestPayload, RequestDetail, RequestListResponse
from app.features.requests.service import (
    IdentityNotFoundError,
    ProfileTargetError,
    RequestAccessError,
    RequestNotFoundError,
    accept_request,
    add_event,
    create_request,
    get_request_detail,
    list_requests,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


@router.post("", response_model=RequestDetail, status_code=status.HTTP_201_CREATED)
async def submit_request(
    payload: CreateRequestPayload,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Submit a new request targeted at a specific expert or company profile."""
    try:
        return await create_request(session, auth_user_id, payload)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfileTargetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=RequestListResponse)
async def list_my_requests(
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestListResponse:
    """List every request the caller is part of, as a customer, expert, or company admin."""
    try:
        results = await list_requests(session, auth_user_id)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RequestListResponse(results=results)


@router.get("/{request_id}", response_model=RequestDetail)
async def get_request(
    request_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Return full detail for one request, including participants and the message timeline."""
    try:
        return await get_request_detail(session, auth_user_id, request_id)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RequestAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{request_id}/events", response_model=RequestDetail)
async def post_event(
    request_id: UUID,
    payload: AddEventPayload,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Add a message to the request's shared timeline."""
    try:
        return await add_event(session, auth_user_id, request_id, payload.message)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RequestAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{request_id}/accept", response_model=RequestDetail)
async def accept(
    request_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Let the invited expert or company admin accept the request."""
    try:
        return await accept_request(session, auth_user_id, request_id)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RequestAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
