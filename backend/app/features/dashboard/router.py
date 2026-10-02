"""HTTP endpoints for the customer, expert and company dashboards."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.dashboard.schemas import CustomerDashboard, ProviderDashboard
from app.features.dashboard.service import (
    DashboardAccessError,
    DashboardNotFoundError,
    company_dashboard,
    customer_dashboard,
    expert_dashboard,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


@router.get("/customer", response_model=CustomerDashboard)
async def customer(
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> CustomerDashboard:
    try:
        return await customer_dashboard(session, auth_user_id)
    except DashboardNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/expert", response_model=ProviderDashboard)
async def expert(
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ProviderDashboard:
    try:
        return await expert_dashboard(session, auth_user_id)
    except DashboardNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/company/{organization_id}", response_model=ProviderDashboard)
async def company(
    organization_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ProviderDashboard:
    try:
        return await company_dashboard(session, auth_user_id, organization_id)
    except DashboardNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DashboardAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
