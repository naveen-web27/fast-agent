"""HTTP endpoints for the customer <-> expert/company request workflow."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import PlanRequiredError
from app.db.session import get_db
from app.features.requests.schemas import (
    AddEventPayload,
    AssignPayload,
    CreateRequestPayload,
    CreateReviewPayload,
    CustomerProfileOut,
    DisputeCompletionPayload,
    InviteCompanyPayload,
    RequestDetail,
    RequestListResponse,
)
from app.features.requests.service import (
    DuplicateInviteError,
    DuplicateReviewError,
    IdentityNotFoundError,
    ProfileTargetError,
    RequestAccessError,
    RequestNotFoundError,
    RequestStateError,
    accept_request,
    add_event,
    assign_request,
    create_request,
    create_review,
    get_customer_profile,
    get_request_detail,
    invite_company,
    list_requests,
    mark_request_done,
    respond_to_completion,
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


@router.get("/{request_id}/customer", response_model=CustomerProfileOut)
async def get_request_customer(
    request_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> CustomerProfileOut:
    """The customer's profile, visible only to people on this request."""
    try:
        return await get_customer_profile(session, auth_user_id, request_id)
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


@router.post("/{request_id}/invite-company", response_model=RequestDetail)
async def invite_company_to_request(
    request_id: UUID,
    payload: InviteCompanyPayload,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Let an expert who has accepted this request bring a company profile in to help fulfil it."""
    try:
        return await invite_company(session, auth_user_id, request_id, payload.profile_id)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RequestAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ProfileTargetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DuplicateInviteError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


def _raise_http(exc: Exception) -> None:
    if isinstance(exc, (IdentityNotFoundError, RequestNotFoundError)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, RequestAccessError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if isinstance(exc, (RequestStateError, DuplicateReviewError)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, PlanRequiredError):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    raise exc


_HANDLED = (
    IdentityNotFoundError, RequestNotFoundError, RequestAccessError, RequestStateError, DuplicateReviewError, PlanRequiredError,
)


@router.post("/{request_id}/complete", response_model=RequestDetail)
async def complete(
    request_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Customer marks the request as done; accepted providers are then asked to confirm."""
    try:
        return await mark_request_done(session, auth_user_id, request_id)
    except _HANDLED as exc:
        _raise_http(exc)


@router.post("/{request_id}/confirm-completion", response_model=RequestDetail)
async def confirm_completion(
    request_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """An accepted expert/company agrees the request is done, which unlocks ratings."""
    try:
        return await respond_to_completion(session, auth_user_id, request_id, confirm=True)
    except _HANDLED as exc:
        _raise_http(exc)


@router.post("/{request_id}/dispute-completion", response_model=RequestDetail)
async def dispute_completion(
    request_id: UUID,
    payload: DisputeCompletionPayload,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """An accepted expert/company reports the request wasn't really done; ratings of them stay on hold."""
    try:
        return await respond_to_completion(session, auth_user_id, request_id, confirm=False, reason=payload.reason)
    except _HANDLED as exc:
        _raise_http(exc)


@router.post("/{request_id}/reviews", response_model=RequestDetail, status_code=status.HTTP_201_CREATED)
async def review(
    request_id: UUID,
    payload: CreateReviewPayload,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Rate an expert or company on a completed request."""
    try:
        return await create_review(session, auth_user_id, request_id, payload)
    except _HANDLED as exc:
        _raise_http(exc)


@router.post("/{request_id}/assign", response_model=RequestDetail)
async def assign(
    request_id: UUID,
    payload: AssignPayload,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> RequestDetail:
    """Company admin (Enterprise) hands this request to a team member, or unassigns it."""
    try:
        return await assign_request(session, auth_user_id, request_id, payload.user_id)
    except _HANDLED as exc:
        _raise_http(exc)
