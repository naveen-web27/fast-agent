"""Admin-only endpoints for lead management, mounted at /admin/leads."""
from collections.abc import Awaitable
from typing import TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.admin.router import require_platform_admin
from app.features.leads import service
from app.features.leads.schemas import LeadCreate, LeadImport, LeadImportResult, LeadOut, LeadStatus, LeadType, LeadUpdate
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
async def leads(
    status_filter: LeadStatus | None = Query(default=None, alias="status"),
    lead_type: LeadType | None = Query(default=None, alias="type"),
    q: str | None = Query(default=None, max_length=120),
    profile: str | None = Query(default=None, pattern="^(created|missing)$"),
    due: bool = Query(default=False, description="Only follow-ups due today or earlier"),
    _: User = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> list[LeadOut]:
    return await service.list_leads(session, status_filter, lead_type, q, profile, due)


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def add_lead(payload: LeadCreate, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)) -> LeadOut:
    return await _run(service.create_lead(session, admin, payload))


@router.post("/import", response_model=LeadImportResult)
async def import_leads(
    payload: LeadImport, admin: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> LeadImportResult:
    """Rows pasted from Excel or Google Sheets. Existing numbers only get their empty fields filled."""
    return await service.import_leads(session, admin, payload)


@router.patch("/{lead_id}", response_model=LeadOut)
async def edit_lead(
    lead_id: UUID, payload: LeadUpdate, _: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)
) -> LeadOut:
    return await _run(service.update_lead(session, lead_id, payload))


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_lead(lead_id: UUID, _: User = Depends(require_platform_admin), session: AsyncSession = Depends(get_db)) -> None:
    await _run(service.delete_lead(session, lead_id))
