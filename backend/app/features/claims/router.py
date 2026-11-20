"""HTTP endpoints for finding an unclaimed company listing and claiming it."""
from collections.abc import Awaitable
from typing import TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.features.auth.email import EmailDeliveryError, EmailNotConfiguredError
from app.features.claims.schemas import ClaimCodeRequest, ClaimSubmit, MyClaimOut, UnclaimedListingOut
from app.features.claims.service import (
    ClaimCodeError,
    ClaimEligibilityError,
    ClaimNotFoundError,
    ClaimRateLimitError,
    ListingConflictError,
    ListingNotFoundError,
    get_listing,
    list_my_claims,
    search_unclaimed_listings,
    send_claim_code,
    submit_claim,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()

T = TypeVar("T")
ERROR_STATUS = {
    ListingNotFoundError: status.HTTP_404_NOT_FOUND,
    ClaimNotFoundError: status.HTTP_404_NOT_FOUND,
    ListingConflictError: status.HTTP_409_CONFLICT,
    ClaimEligibilityError: status.HTTP_409_CONFLICT,
    ClaimCodeError: status.HTTP_400_BAD_REQUEST,
    ClaimRateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
}


async def run_claim_action(action: Awaitable[T]) -> T:
    try:
        return await action
    except tuple(ERROR_STATUS) as exc:
        raise HTTPException(status_code=ERROR_STATUS[type(exc)], detail=str(exc)) from exc


@router.get("/listings", response_model=list[UnclaimedListingOut])
async def unclaimed_listings(
    q: str | None = Query(default=None, max_length=120),
    city: str | None = Query(default=None, max_length=100),
    session: AsyncSession = Depends(get_db),
) -> list[UnclaimedListingOut]:
    """Businesses added by RightConnect that their owners haven't claimed yet."""
    return await search_unclaimed_listings(session, q, city)


@router.get("/listings/{profile_id}", response_model=UnclaimedListingOut)
async def listing(profile_id: UUID, session: AsyncSession = Depends(get_db)) -> UnclaimedListingOut:
    return await run_claim_action(get_listing(session, profile_id))


@router.get("/mine", response_model=list[MyClaimOut])
async def my_claims(
    auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> list[MyClaimOut]:
    return await list_my_claims(session, auth_user_id)


@router.post("/code", status_code=status.HTTP_202_ACCEPTED)
async def request_claim_code(
    payload: ClaimCodeRequest,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Email a one-time code that proves the claimant controls the business email."""
    try:
        await run_claim_action(send_claim_code(session, settings, auth_user_id, payload.profile_id, str(payload.email)))
    except EmailNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email sending is not set up on the server yet. Please try again later or contact support.",
        ) from exc
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="We couldn't deliver the code to this email. Check the address or try again later.",
        ) from exc
    return {"status": "sent"}


@router.post("", response_model=MyClaimOut, status_code=status.HTTP_201_CREATED)
async def create_claim(
    payload: ClaimSubmit,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> MyClaimOut:
    """Verify the code and queue the claim for RightConnect to review."""
    return await run_claim_action(submit_claim(session, auth_user_id, payload))
