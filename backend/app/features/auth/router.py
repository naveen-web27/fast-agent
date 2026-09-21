"""HTTP endpoints for authentication handoff and role onboarding."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.auth.schemas import OnboardingRequest, UserResponse
from app.features.auth.service import OnboardingConflictError, create_user_profile, get_user_profile
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


@router.get("/provider-config")
async def get_provider_config() -> dict[str, str]:
    """Expose only the public Supabase browser configuration needed for OAuth."""
    from app.core.config import get_settings

    settings = get_settings()
    return {
        "supabase_url": settings.supabase_url,
        "supabase_publishable_key": settings.supabase_publishable_key,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Return the caller's onboarded profile, or 404 if onboarding hasn't happened yet."""
    profile = await get_user_profile(session, auth_user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Onboarding not completed")
    return profile


@router.post("/onboarding", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def complete_onboarding(
    payload: OnboardingRequest,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a role-specific application profile after external verification."""
    try:
        return await create_user_profile(session, auth_user_id, payload)
    except OnboardingConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc