"""Admin-only endpoints for RightConnect Marketing leads, mounted at /admin/marketing-leads."""
from collections.abc import Awaitable
from typing import TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.admin.router import require_platform_admin
from app.features.marketing import service
from app.features.marketing.schemas import ActivityCreate, ActivityOut, ActivityResult, LeadCreate, LeadOut, LeadUpdate
from app.models.user import User

router = APIRouter()

T = TypeVar("T")
ERROR_STATUS = {
    service.LeadNotFoundError: status.HTTP_404_NOT_FOUND,
    service.LeadConflictError: status.HTTP_409_CONFLICT,
}


async def _run(action: Awaitable[T]) -> T:
    try:
        return await action
    except tuple(ERROR_STATUS) as exc:
        raise HTTPException(status_code=ERROR_STATUS[type(exc)], detail=str(exc)) from exc


@router.get("", response_model=list[LeadOut])
async def leads(_: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)) -> list[LeadOut]:
    return await service.list_leads(session)


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def add_lead(payload: LeadCreate, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)) -> LeadOut:
    return await _run(service.create_lead(session, admin, payload))


@router.patch("/{lead_id}", response_model=LeadOut)
async def edit_lead(
    lead_id: UUID, payload: LeadUpdate, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> LeadOut:
    return await _run(service.update_lead(session, admin, lead_id, payload))


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_lead(lead_id: UUID, _: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)) -> None:
    await _run(service.delete_lead(session, lead_id))


@router.get("/{lead_id}/activities", response_model=list[ActivityOut])
async def activities(lead_id: UUID, _: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)) -> list[ActivityOut]:
    return await _run(service.list_activities(session, lead_id))


@router.post("/{lead_id}/activities", response_model=ActivityResult, status_code=status.HTTP_201_CREATED)
async def add_activity(
    lead_id: UUID, payload: ActivityCreate, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> ActivityResult:
    return await _run(service.add_activity(session, admin, lead_id, payload))


@router.delete("/{lead_id}/activities/{activity_id}", response_model=ActivityResult)
async def remove_activity(
    lead_id: UUID, activity_id: UUID, _: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> ActivityResult:
    return await _run(service.delete_activity(session, lead_id, activity_id))
