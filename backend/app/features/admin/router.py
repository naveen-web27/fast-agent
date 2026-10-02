"""Admin-only endpoints for reviewing and verifying marketplace profiles."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.admin.schemas import BlockProfilePayload, PendingProfile, VerificationDecision
from app.features.admin.service import (
    ProfileNotFoundError,
    delete_profile,
    list_profiles_for_review,
    set_profile_blocked,
    set_profile_verification,
)
from app.models.profile import VerificationStatus
from app.models.user import User, UserRole
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


async def require_platform_admin(
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Only platform admins may review and verify marketplace profiles."""
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None or user.role is not UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.get("/profiles", response_model=list[PendingProfile], dependencies=[Depends(require_platform_admin)])
async def list_profiles(
    verification: str = Query(default="pending", pattern="^(pending|verified|rejected|blocked|all)$"),
    q: str | None = Query(default=None, max_length=120),
    session: AsyncSession = Depends(get_db),
) -> list[PendingProfile]:
    """List marketplace profiles by status, optionally searched by name or owner email."""
    return await list_profiles_for_review(session, verification, q)


@router.post("/profiles/{profile_id}/verification", dependencies=[Depends(require_platform_admin)])
async def review_profile(
    profile_id: UUID,
    payload: VerificationDecision,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Mark a profile (and its organization, if any) as verified or rejected."""
    try:
        await set_profile_verification(session, profile_id, VerificationStatus(payload.status))
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"status": payload.status}


@router.post("/profiles/{profile_id}/block", dependencies=[Depends(require_platform_admin)])
async def block_profile(
    profile_id: UUID,
    payload: BlockProfilePayload,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Hide a profile from discovery and stop it receiving new requests."""
    try:
        await set_profile_blocked(session, profile_id, payload.reason)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"status": "blocked"}


@router.post("/profiles/{profile_id}/unblock", dependencies=[Depends(require_platform_admin)])
async def unblock_profile(profile_id: UUID, session: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        await set_profile_blocked(session, profile_id, None)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"status": "active"}


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_platform_admin)])
async def remove_profile(profile_id: UUID, session: AsyncSession = Depends(get_db)) -> None:
    """Permanently delete a profile; deleting a company profile removes the whole company."""
    try:
        await delete_profile(session, profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
