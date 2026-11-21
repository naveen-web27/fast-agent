"""Admin-only endpoints: profile & account moderation, disputes, stats, and audit trail."""
from collections.abc import Awaitable
from typing import Literal, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.features.admin.schemas import (
    AdminActivity,
    AdminDispute,
    AdminStats,
    AdminUser,
    BlockProfilePayload,
    DisputeResolution,
    PendingProfile,
    VerificationDecision,
)
from app.features.admin.service import (
    AdminSelfActionError,
    DisputeNotFoundError,
    ProfileNotFoundError,
    UserNotFoundError,
    block_user,
    delete_profile,
    delete_user,
    get_stats,
    list_activity,
    list_disputes,
    list_profiles_for_review,
    list_users,
    resolve_dispute,
    set_profile_blocked,
    set_profile_verification,
    unblock_user,
    undelete_profile,
    undelete_user,
)
from app.features.auth.lifecycle import RestoreConflictError
from app.features.claims.router import run_claim_action
from app.features.claims.schemas import AdminClaimOut, ClaimRejection, UnclaimedListingCreate, UnclaimedListingOut
from app.features.claims.service import approve_claim, create_unclaimed_listing, list_claims_for_admin, reject_claim
from app.features.workers import service as worker_service
from app.features.workers.router import run_worker_action
from app.features.workers.schemas import AdminWorkerCreate, AdminWorkerOut, ClaimCodeOut
from app.models.profile import VerificationStatus
from app.models.user import User, UserRole, active_user_by_auth_id
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()

T = TypeVar("T")
_ERROR_STATUS = {
    ProfileNotFoundError: status.HTTP_404_NOT_FOUND,
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    DisputeNotFoundError: status.HTTP_404_NOT_FOUND,
    AdminSelfActionError: status.HTTP_400_BAD_REQUEST,
    RestoreConflictError: status.HTTP_409_CONFLICT,
}


async def _run(action: Awaitable[T]) -> T:
    try:
        return await action
    except tuple(_ERROR_STATUS) as exc:
        raise HTTPException(status_code=_ERROR_STATUS[type(exc)], detail=str(exc)) from exc


async def require_platform_admin(
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """platform_admin role, plus (if ADMIN_EMAILS is set) an allow-listed email."""
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None or user.role is not UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    allowed = settings.admin_email_list
    if allowed and user.email.lower() not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


# ---------- Overview ----------


@router.get("/stats", response_model=AdminStats)
async def stats(_: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)) -> AdminStats:
    return AdminStats(**await get_stats(session))


# ---------- Profiles ----------


@router.get("/profiles", response_model=list[PendingProfile])
async def list_profiles(
    verification: str = Query(default="pending", pattern="^(pending|verified|rejected|unclaimed|blocked|deleted|all)$"),
    q: str | None = Query(default=None, max_length=120),
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> list[PendingProfile]:
    """List marketplace profiles by status, optionally searched by name or owner email."""
    return await list_profiles_for_review(session, verification, q)


@router.post("/profiles/{profile_id}/verification")
async def review_profile(
    profile_id: UUID,
    payload: VerificationDecision,
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await _run(set_profile_verification(session, admin, profile_id, VerificationStatus(payload.status)))
    return {"status": payload.status}


@router.post("/profiles/{profile_id}/block")
async def block_profile(
    profile_id: UUID,
    payload: BlockProfilePayload,
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Hide a profile from discovery and stop it receiving new requests."""
    await _run(set_profile_blocked(session, admin, profile_id, payload.reason))
    return {"status": "blocked"}


@router.post("/profiles/{profile_id}/unblock")
async def unblock_profile(
    profile_id: UUID, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    await _run(set_profile_blocked(session, admin, profile_id, None))
    return {"status": "active"}


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_profile(
    profile_id: UUID, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> None:
    """Soft-delete a profile; a company profile takes its whole company with it."""
    await _run(delete_profile(session, admin, profile_id))


@router.post("/profiles/{profile_id}/restore")
async def restore_profile_endpoint(
    profile_id: UUID, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    await _run(undelete_profile(session, admin, profile_id))
    return {"status": "restored"}


# ---------- Unclaimed company listings & ownership claims ----------


@router.post("/companies", response_model=UnclaimedListingOut, status_code=status.HTTP_201_CREATED)
async def add_unclaimed_company(
    payload: UnclaimedListingCreate, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> UnclaimedListingOut:
    """Add a real local business as an unclaimed listing its owner can claim later."""
    return await run_claim_action(create_unclaimed_listing(session, admin, payload))


@router.get("/claims", response_model=list[AdminClaimOut])
async def claims(
    status_filter: str = Query(default="pending", alias="status", pattern="^(pending|approved|rejected|all)$"),
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> list[AdminClaimOut]:
    return await list_claims_for_admin(session, status_filter)


@router.post("/claims/{claim_id}/approve")
async def approve(
    claim_id: UUID,
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Make the claimant the company's admin; other pending claims for it are rejected."""
    await run_claim_action(approve_claim(session, settings, admin, claim_id))
    return {"status": "approved"}


@router.post("/claims/{claim_id}/reject")
async def reject(
    claim_id: UUID,
    payload: ClaimRejection,
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    await run_claim_action(reject_claim(session, settings, admin, claim_id, payload.reason))
    return {"status": "rejected"}


# ---------- Workers (service partners) ----------


@router.get("/workers", response_model=list[AdminWorkerOut])
async def admin_workers(
    status_filter: str = Query(default="all", alias="status", pattern="^(unclaimed|claimed|blocked|deleted|all)$"),
    q: str | None = Query(default=None, max_length=120),
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> list[AdminWorkerOut]:
    return await worker_service.admin_list_workers(session, status_filter, q)


@router.post("/workers", response_model=ClaimCodeOut, status_code=status.HTTP_201_CREATED)
async def admin_add_worker(
    payload: AdminWorkerCreate, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> ClaimCodeOut:
    """Add a real local worker; give them the returned one-time code so they can claim the profile."""
    return await run_worker_action(worker_service.admin_create_worker(session, admin, payload))


@router.post("/workers/{worker_id}/claim-code", response_model=ClaimCodeOut)
async def admin_worker_code(
    worker_id: UUID, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> ClaimCodeOut:
    """Issue a fresh claim code (the old one stops working)."""
    return await run_worker_action(worker_service.admin_new_claim_code(session, admin, worker_id))


@router.post("/workers/{worker_id}/block")
async def admin_block_worker(
    worker_id: UUID, payload: BlockProfilePayload, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    await run_worker_action(worker_service.admin_moderate_worker(session, admin, worker_id, "block", payload.reason))
    return {"status": "blocked"}


@router.post("/workers/{worker_id}/{action}")
async def admin_change_worker(
    worker_id: UUID,
    action: Literal["unblock", "delete", "restore"],
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await run_worker_action(worker_service.admin_moderate_worker(session, admin, worker_id, action, None))
    return {"status": action}


# ---------- Accounts ----------


@router.get("/users", response_model=list[AdminUser])
async def users(
    status_filter: str = Query(default="active", alias="status", pattern="^(active|blocked|deleted|all)$"),
    role: str | None = Query(default=None, pattern="^(customer|expert|company_admin|platform_admin|worker)$"),
    q: str | None = Query(default=None, max_length=120),
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> list[AdminUser]:
    return [AdminUser(**row) for row in await list_users(session, status_filter, role, q)]


@router.post("/users/{user_id}/block")
async def block_account(
    user_id: UUID,
    payload: BlockProfilePayload,
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Suspend the account and hide every profile it owns."""
    await _run(block_user(session, admin, user_id, payload.reason))
    return {"status": "blocked"}


@router.post("/users/{user_id}/unblock")
async def unblock_account(
    user_id: UUID, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    await _run(unblock_user(session, admin, user_id))
    return {"status": "active"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    user_id: UUID, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> None:
    """Soft-delete the account (deleted_at); a purge job removes the data later."""
    await _run(delete_user(session, admin, user_id))


@router.post("/users/{user_id}/restore")
async def restore_account(
    user_id: UUID, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    await _run(undelete_user(session, admin, user_id))
    return {"status": "restored"}


# ---------- Disputes & activity ----------


@router.get("/disputes", response_model=list[AdminDispute])
async def disputes(_: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)) -> list[AdminDispute]:
    return [AdminDispute(**row) for row in await list_disputes(session)]


@router.post("/disputes/{participant_id}/resolve")
async def resolve(
    participant_id: UUID,
    payload: DisputeResolution,
    admin: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await _run(resolve_dispute(session, admin, participant_id, payload.action))
    return {"status": payload.action}


@router.get("/activity", response_model=list[AdminActivity])
async def activity(_: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)) -> list[AdminActivity]:
    return [AdminActivity(**row) for row in await list_activity(session)]
