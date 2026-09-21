"""Core account-creation workflow for the authentication feature."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.schemas import OnboardingRequest, UserResponse
from app.models.user import User, UserRole


class OnboardingConflictError(Exception):
    """Raised when an auth identity or email has already been onboarded."""


async def get_user_profile(session: AsyncSession, auth_user_id: UUID) -> UserResponse | None:
    """Return the onboarded profile for this auth identity, or None if not onboarded yet."""
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        return None
    onboarding_status = "complete" if user.role is UserRole.CUSTOMER else "verification_pending"
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role.value,
        onboarding_status=onboarding_status,
    )


async def create_user_profile(
    session: AsyncSession,
    auth_user_id: UUID,
    payload: OnboardingRequest,
) -> UserResponse:
    """Persist an application profile for a Supabase-verified identity."""
    existing = await session.scalar(
        select(User).where((User.auth_user_id == auth_user_id) | (User.email == str(payload.email)))
    )
    if existing:
        raise OnboardingConflictError("This account has already completed onboarding")

    role = UserRole(payload.role)
    user = User(
        auth_user_id=auth_user_id,
        full_name=payload.full_name,
        email=str(payload.email),
        phone=payload.phone,
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    onboarding_status = "complete" if role is UserRole.CUSTOMER else "verification_pending"
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=payload.role,
        onboarding_status=onboarding_status,
    )