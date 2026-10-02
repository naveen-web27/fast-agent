"""HTTP endpoints for company team seats."""
from collections.abc import Awaitable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.plans import PlanRequiredError
from app.db.session import get_db
from app.features.organizations.schemas import InvitePayload, TeamResponse
from app.features.organizations.service import (
    TeamAccessError,
    TeamConflictError,
    cancel_invite,
    get_team,
    invite_member,
    remove_member,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


async def _run(call: Awaitable[TeamResponse]) -> TeamResponse:
    try:
        return await call
    except TeamAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PlanRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    except TeamConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{organization_id}/team", response_model=TeamResponse)
async def team(
    organization_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> TeamResponse:
    return await _run(get_team(session, auth_user_id, organization_id))


@router.post("/{organization_id}/team/invites", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def invite(
    organization_id: UUID,
    payload: InvitePayload,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TeamResponse:
    """Enterprise: add a staff member by email (joins on their next sign-in if they're new)."""
    return await _run(invite_member(session, settings, auth_user_id, organization_id, str(payload.email)))


@router.delete("/{organization_id}/team/invites/{invite_id}", response_model=TeamResponse)
async def revoke_invite(
    organization_id: UUID,
    invite_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> TeamResponse:
    return await _run(cancel_invite(session, auth_user_id, organization_id, invite_id))


@router.delete("/{organization_id}/team/members/{member_id}", response_model=TeamResponse)
async def remove(
    organization_id: UUID,
    member_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> TeamResponse:
    return await _run(remove_member(session, auth_user_id, organization_id, member_id))
