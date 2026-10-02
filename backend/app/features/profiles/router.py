"""HTTP endpoints for owners editing their expert/company profile."""
from collections.abc import Awaitable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import PlanRequiredError
from app.db.session import get_db
from app.features.profiles.schemas import (
    AvailabilityUpdate,
    CredentialIn,
    ManagedProfile,
    OfferingIn,
    ProfileUpdate,
    SocialLinksUpdate,
)
from app.features.profiles.service import (
    ProfileAccessError,
    ProfileLimitError,
    ProfileNotFoundError,
    add_credential,
    add_offering,
    delete_credential,
    delete_offering,
    get_managed_profile,
    replace_social_links,
    set_availability,
    update_profile,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


async def _run(call: Awaitable[ManagedProfile]) -> ManagedProfile:
    try:
        return await call
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfileAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PlanRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    except ProfileLimitError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/profiles/{profile_id}/manage", response_model=ManagedProfile)
async def get_profile_for_editing(
    profile_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ManagedProfile:
    """Everything the owner can edit, with what their plan unlocks."""
    return await _run(get_managed_profile(session, auth_user_id, profile_id))


@router.patch("/profiles/{profile_id}", response_model=ManagedProfile)
async def edit_profile(
    profile_id: UUID,
    payload: ProfileUpdate,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ManagedProfile:
    return await _run(update_profile(session, auth_user_id, profile_id, payload))


@router.put("/profiles/{profile_id}/social-links", response_model=ManagedProfile)
async def edit_social_links(
    profile_id: UUID,
    payload: SocialLinksUpdate,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ManagedProfile:
    return await _run(replace_social_links(session, auth_user_id, profile_id, payload))


@router.post("/profiles/{profile_id}/credentials", response_model=ManagedProfile, status_code=status.HTTP_201_CREATED)
async def create_credential(
    profile_id: UUID,
    payload: CredentialIn,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ManagedProfile:
    return await _run(add_credential(session, auth_user_id, profile_id, payload))


@router.delete("/profiles/{profile_id}/credentials/{credential_id}", response_model=ManagedProfile)
async def remove_credential(
    profile_id: UUID,
    credential_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ManagedProfile:
    return await _run(delete_credential(session, auth_user_id, profile_id, credential_id))


@router.post("/profiles/{profile_id}/offerings", response_model=ManagedProfile, status_code=status.HTTP_201_CREATED)
async def create_offering(
    profile_id: UUID,
    payload: OfferingIn,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ManagedProfile:
    return await _run(add_offering(session, auth_user_id, profile_id, payload))


@router.delete("/profiles/{profile_id}/offerings/{offering_id}", response_model=ManagedProfile)
async def remove_offering(
    profile_id: UUID,
    offering_id: UUID,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ManagedProfile:
    return await _run(delete_offering(session, auth_user_id, profile_id, offering_id))


@router.put("/profiles/{profile_id}/availability", response_model=ManagedProfile)
async def edit_availability(
    profile_id: UUID,
    payload: AvailabilityUpdate,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ManagedProfile:
    return await _run(set_availability(session, auth_user_id, profile_id, payload))
