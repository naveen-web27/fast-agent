"""Account-creation and multi-role identity workflow for the authentication feature."""
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.features.auth.email import send_email
from app.features.auth.schemas import (
    CompanyMembership,
    CompanyRequest,
    ExpertProfileRequest,
    ExpertProfileSummary,
    IdentitiesResponse,
    OnboardingRequest,
    UserResponse,
)
from app.models.email_verification import EmailVerification
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, Profile, ProfileKind, VerificationStatus
from app.models.user import User, UserRole

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


class OnboardingConflictError(Exception):
    """Raised when an auth identity or email has already been onboarded."""


class IdentityNotFoundError(Exception):
    """Raised when an operation needs a base account that hasn't been created yet."""


class ExpertProfileConflictError(Exception):
    """Raised when the account already has a personal expert profile."""


class OrganizationAccessError(Exception):
    """Raised when the caller isn't an admin of the target organization."""


class InvalidOtpError(Exception):
    """Raised when a submitted verification code is wrong, expired, or exhausted."""


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "company"
    return f"{base}-{secrets.token_hex(3)}"


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
        interests=user.interests,
        onboarding_status=onboarding_status,
    )


async def create_user_profile(
    session: AsyncSession,
    auth_user_id: UUID,
    payload: OnboardingRequest,
) -> UserResponse:
    """Create the base account for a Supabase-verified identity, plus its first expert/company listing."""
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
        interests=[payload.interest] if payload.interest else [],
    )
    session.add(user)
    await session.flush()

    if role is UserRole.EXPERT:
        session.add(
            Profile(
                user_id=user.id,
                kind=ProfileKind.EXPERT,
                display_name=payload.full_name,
                headline=payload.primary_service or "Independent expert",
                city=payload.city,
                years_experience=payload.years_experience,
                languages=[payload.preferred_language] if payload.preferred_language else [],
                verification=VerificationStatus.PENDING,
            )
        )
    elif role is UserRole.COMPANY_ADMIN and payload.company_name:
        organization = Organization(
            name=payload.company_name,
            slug=_slugify(payload.company_name),
            website_url=payload.website,
            city=payload.city,
            verification=VerificationStatus.PENDING,
        )
        session.add(organization)
        await session.flush()
        session.add(OrganizationMember(organization_id=organization.id, user_id=user.id, member_role=MemberRole.ADMIN.value))
        session.add(
            Profile(
                organization_id=organization.id,
                kind=ProfileKind.COMPANY,
                display_name=payload.company_name,
                headline="Company",
                city=payload.city,
                verification=VerificationStatus.PENDING,
            )
        )

    await session.commit()
    await session.refresh(user)

    onboarding_status = "complete" if role is UserRole.CUSTOMER else "verification_pending"
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=payload.role,
        interests=user.interests,
        onboarding_status=onboarding_status,
    )


async def get_identities(session: AsyncSession, auth_user_id: UUID) -> IdentitiesResponse | None:
    """Return everything this auth identity can act as: customer, expert, and/or company admin."""
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        return None

    expert_profile_row = await session.scalar(
        select(Profile).where(Profile.kind == ProfileKind.EXPERT, Profile.user_id == user.id)
    )
    expert_profile = (
        ExpertProfileSummary(
            id=expert_profile_row.id,
            headline=expert_profile_row.headline,
            verification=expert_profile_row.verification.value,
            average_rating=float(expert_profile_row.average_rating),
            review_count=expert_profile_row.review_count,
        )
        if expert_profile_row
        else None
    )

    membership_rows = (
        await session.execute(
            select(OrganizationMember, Organization)
            .join(Organization, Organization.id == OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user.id)
        )
    ).all()
    companies = [
        CompanyMembership(
            organization_id=organization.id,
            name=organization.name,
            member_role=member.member_role,
            verification=organization.verification.value,
            email_domain_verified=organization.email_domain_verified,
        )
        for member, organization in membership_rows
    ]

    onboarding_status = "complete" if user.role is UserRole.CUSTOMER else "verification_pending"
    return IdentitiesResponse(
        user=UserResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role.value,
            interests=user.interests,
            onboarding_status=onboarding_status,
        ),
        expert_profile=expert_profile,
        companies=companies,
    )


async def add_expert_profile(session: AsyncSession, auth_user_id: UUID, payload: ExpertProfileRequest) -> ExpertProfileSummary:
    """Add a personal expert listing to an account that has already completed base onboarding."""
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        raise IdentityNotFoundError("Complete onboarding before adding an expert profile")

    existing = await session.scalar(select(Profile).where(Profile.kind == ProfileKind.EXPERT, Profile.user_id == user.id))
    if existing:
        raise ExpertProfileConflictError("This account already has an expert profile")

    profile = Profile(
        user_id=user.id,
        kind=ProfileKind.EXPERT,
        display_name=user.full_name,
        headline=payload.headline,
        bio=payload.bio,
        city=payload.city,
        years_experience=payload.years_experience,
        languages=payload.languages,
        verification=VerificationStatus.PENDING,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return ExpertProfileSummary(
        id=profile.id,
        headline=profile.headline,
        verification=profile.verification.value,
        average_rating=float(profile.average_rating),
        review_count=profile.review_count,
    )


async def add_company(session: AsyncSession, auth_user_id: UUID, payload: CompanyRequest) -> CompanyMembership:
    """Register a new company and make the caller its first admin."""
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        raise IdentityNotFoundError("Complete onboarding before adding a company")

    organization = Organization(
        name=payload.company_name,
        slug=_slugify(payload.company_name),
        website_url=payload.website,
        city=payload.city,
        verification=VerificationStatus.PENDING,
    )
    session.add(organization)
    await session.flush()
    session.add(OrganizationMember(organization_id=organization.id, user_id=user.id, member_role=MemberRole.ADMIN.value))
    session.add(
        Profile(
            organization_id=organization.id,
            kind=ProfileKind.COMPANY,
            display_name=payload.company_name,
            headline="Company",
            city=payload.city,
            verification=VerificationStatus.PENDING,
        )
    )
    await session.commit()
    await session.refresh(organization)
    return CompanyMembership(
        organization_id=organization.id,
        name=organization.name,
        member_role=MemberRole.ADMIN.value,
        verification=organization.verification.value,
        email_domain_verified=organization.email_domain_verified,
    )


async def _require_admin_membership(session: AsyncSession, auth_user_id: UUID, organization_id: UUID) -> None:
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        raise IdentityNotFoundError("Complete onboarding first")
    member = await session.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == user.id
        )
    )
    if member is None or member.member_role != MemberRole.ADMIN.value:
        raise OrganizationAccessError("You are not an admin of this company")


async def send_domain_otp(
    session: AsyncSession, settings: Settings, auth_user_id: UUID, organization_id: UUID, email: str
) -> None:
    """Email a 6-digit code to prove control of a company email address."""
    await _require_admin_membership(session, auth_user_id, organization_id)

    code = f"{secrets.randbelow(1_000_000):06d}"
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    session.add(
        EmailVerification(
            email=email,
            purpose="company_domain",
            organization_id=organization_id,
            code_hash=code_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES),
        )
    )
    await session.commit()

    await send_email(
        settings,
        to=email,
        subject="Your RightConnect company verification code",
        html=f"<p>Your verification code is <strong>{code}</strong>. It expires in {OTP_TTL_MINUTES} minutes.</p>",
    )


async def verify_domain_otp(session: AsyncSession, auth_user_id: UUID, organization_id: UUID, email: str, code: str) -> None:
    """Confirm a code and mark the company's email domain as verified."""
    await _require_admin_membership(session, auth_user_id, organization_id)

    verification = await session.scalar(
        select(EmailVerification)
        .where(
            EmailVerification.organization_id == organization_id,
            EmailVerification.email == email,
            EmailVerification.purpose == "company_domain",
            EmailVerification.verified_at.is_(None),
        )
        .order_by(EmailVerification.created_at.desc())
    )
    if verification is None or verification.expires_at < datetime.now(timezone.utc):
        raise InvalidOtpError("Code expired or not found, request a new one")
    if verification.attempts >= OTP_MAX_ATTEMPTS:
        raise InvalidOtpError("Too many attempts, request a new code")
    if verification.code_hash != hashlib.sha256(code.encode()).hexdigest():
        verification.attempts += 1
        await session.commit()
        raise InvalidOtpError("Incorrect code")

    verification.verified_at = datetime.now(timezone.utc)
    organization = await session.get(Organization, organization_id)
    if organization is not None:
        organization.email_domain_verified = True
    await session.commit()


async def add_interest(session: AsyncSession, auth_user_id: UUID, interest: str) -> list[str]:
    """Add an area of interest (e.g. from onboarding or a marketplace search), de-duplicated case-insensitively."""
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        raise IdentityNotFoundError("Complete onboarding before saving an interest")

    normalized = interest.strip()
    if normalized and not any(existing.lower() == normalized.lower() for existing in user.interests):
        user.interests = [*user.interests, normalized]
        await session.commit()
        await session.refresh(user)
    return user.interests


async def remove_interest(session: AsyncSession, auth_user_id: UUID, interest: str) -> list[str]:
    """Remove an area of interest from the caller's saved list."""
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        raise IdentityNotFoundError("Complete onboarding before editing interests")

    normalized = interest.strip().lower()
    user.interests = [existing for existing in user.interests if existing.lower() != normalized]
    await session.commit()
    await session.refresh(user)
    return user.interests