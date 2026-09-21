"""HTTP endpoints for authentication handoff and role onboarding."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.features.auth.email import EmailNotConfiguredError
from app.features.auth.schemas import (
    CompanyMembership,
    CompanyRequest,
    DomainOtpSendRequest,
    DomainOtpVerifyRequest,
    ExpertProfileRequest,
    ExpertProfileSummary,
    IdentitiesResponse,
    InterestRequest,
    InterestsResponse,
    OnboardingRequest,
    UserResponse,
)
from app.features.auth.service import (
    ExpertProfileConflictError,
    IdentityNotFoundError,
    InvalidOtpError,
    OnboardingConflictError,
    OrganizationAccessError,
    add_company,
    add_expert_profile,
    add_interest,
    create_user_profile,
    get_identities,
    get_user_profile,
    remove_interest,
    send_domain_otp,
    verify_domain_otp,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


@router.get("/provider-config")
async def get_provider_config() -> dict[str, str]:
    """Expose only the public Supabase browser configuration needed for OAuth."""
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


@router.get("/identities", response_model=IdentitiesResponse)
async def list_identities(
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> IdentitiesResponse:
    """Return everything this account can act as: customer, expert profile, and/or companies."""
    identities = await get_identities(session, auth_user_id)
    if identities is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Onboarding not completed")
    return identities


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


@router.post("/identities/expert", response_model=ExpertProfileSummary, status_code=status.HTTP_201_CREATED)
async def create_expert_profile(
    payload: ExpertProfileRequest,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ExpertProfileSummary:
    """Add a personal expert listing to an existing account."""
    try:
        return await add_expert_profile(session, auth_user_id, payload)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExpertProfileConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/identities/companies", response_model=CompanyMembership, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyRequest,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> CompanyMembership:
    """Register a new company and make the caller its first admin."""
    try:
        return await add_company(session, auth_user_id, payload)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/identities/companies/domain-otp/send", status_code=status.HTTP_202_ACCEPTED)
async def request_domain_otp(
    payload: DomainOtpSendRequest,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Email a one-time code to prove control of a company email address."""
    try:
        await send_domain_otp(session, settings, auth_user_id, payload.organization_id, payload.email)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OrganizationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EmailNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return {"status": "sent"}


@router.post("/identities/companies/domain-otp/verify")
async def confirm_domain_otp(
    payload: DomainOtpVerifyRequest,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Confirm a code and mark the company's email domain as verified."""
    try:
        await verify_domain_otp(session, auth_user_id, payload.organization_id, payload.email, payload.code)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OrganizationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidOtpError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "verified"}


@router.post("/interests", response_model=InterestsResponse)
async def save_interest(
    payload: InterestRequest,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> InterestsResponse:
    """Add an area of interest, seeded at onboarding or captured from a marketplace search."""
    try:
        interests = await add_interest(session, auth_user_id, payload.interest)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return InterestsResponse(interests=interests)


@router.delete("/interests", response_model=InterestsResponse)
async def delete_interest(
    interest: str,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> InterestsResponse:
    """Remove an area of interest from the caller's saved list (used by the settings editor)."""
    try:
        interests = await remove_interest(session, auth_user_id, interest)
    except IdentityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return InterestsResponse(interests=interests)
