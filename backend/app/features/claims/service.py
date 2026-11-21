"""Admin-created company listings that real owners can claim.

Flow: a platform admin adds an unclaimed listing -> a signed-in user proves a business
email with a one-time code and submits a claim -> an admin approves it, which makes the
claimant the company's admin. Unclaimed listings show in Discover but can't take requests.
"""
import hashlib
import html
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.features.auth.email import EmailDeliveryError, EmailNotConfiguredError, send_email
from app.features.claims.schemas import (
    AdminClaimOut,
    ClaimSubmit,
    MyClaimOut,
    UnclaimedListingCreate,
    UnclaimedListingOut,
)
from app.models.admin_action import AdminAction
from app.models.email_verification import EmailVerification
from app.models.organization_claim import ClaimReviewStatus, OrganizationClaim
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import ClaimStatus, Organization, Profile, ProfileKind, Service, VerificationStatus
from app.models.user import User, active_user_by_auth_id

logger = logging.getLogger(__name__)

CLAIM_OTP_PURPOSE = "company_claim"
OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
CODES_PER_EMAIL_WINDOW = 3
CODES_PER_LISTING_HOUR = 10
# A business email on one of these domains can't prove ownership of a website's domain.
FREE_MAIL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "outlook.com", "hotmail.com", "live.com",
    "icloud.com", "me.com", "aol.com", "proton.me", "protonmail.com", "rediffmail.com", "zoho.com", "yandex.com",
})


class ListingNotFoundError(Exception):
    """Raised when the company listing doesn't exist, is hidden, or isn't a company."""


class ListingConflictError(Exception):
    """Raised when a listing is already claimed or a duplicate listing would be created."""


class ClaimEligibilityError(Exception):
    """Raised when the caller can't claim (not onboarded, blocked, already runs a company, pending claim)."""


class ClaimCodeError(Exception):
    """Raised when the submitted one-time code is wrong, expired, or exhausted."""


class ClaimRateLimitError(Exception):
    """Raised when too many codes were requested for a listing or email."""


class ClaimNotFoundError(Exception):
    """Raised when the claim doesn't exist or was already reviewed."""


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "company"
    return f"{base}-{secrets.token_hex(3)}"


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def email_matches_listing(email: str, contact_email: str | None, website_url: str | None) -> bool:
    """True if the proven email is the listing's contact email or on the business website's own domain."""
    email = email.strip().lower()
    if contact_email and email == contact_email.strip().lower():
        return True
    if not website_url:
        return False
    domain = email.rsplit("@", 1)[-1]
    host = (urlparse(website_url).hostname or "").lower().removeprefix("www.")
    if not host or domain in FREE_MAIL_DOMAINS:
        return False
    return domain == host or host.endswith(f".{domain}")


async def _service_for(session: AsyncSession, name: str) -> Service:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:80] or "service"
    service = await session.scalar(select(Service).where(Service.slug == slug))
    if service is None:
        service = Service(name=name.strip(), slug=slug)
        session.add(service)
    return service


def _log(session: AsyncSession, admin: User, action: str, target_id: UUID, label: str, reason: str | None = None) -> None:
    session.add(
        AdminAction(
            admin_user_id=admin.id, action=action, target_type="organization", target_id=target_id,
            target_label=label, reason=reason,
        )
    )


async def _notify(settings: Settings, to: str, subject: str, body: str) -> None:
    """Best-effort email; a missing or failing email provider must not undo an admin decision."""
    try:
        await send_email(settings, to=to, subject=subject, html=body)
    except (EmailNotConfiguredError, EmailDeliveryError):
        logger.warning("Claim notification to %s was not sent", to)


# ---------- Admin: create listings ----------


async def create_unclaimed_listing(session: AsyncSession, admin: User, payload: UnclaimedListingCreate) -> UnclaimedListingOut:
    """Add a real business that hasn't joined yet. It has no members until a claim is approved."""
    duplicate = await session.scalar(
        select(Organization.id).where(
            func.lower(Organization.name) == payload.company_name.lower(),
            func.lower(func.coalesce(Organization.city, "")) == payload.city.lower(),
            Organization.deleted_at.is_(None),
        )
    )
    if duplicate is not None:
        raise ListingConflictError(f"{payload.company_name} in {payload.city} is already listed")

    organization = Organization(
        name=payload.company_name,
        slug=_slugify(payload.company_name),
        description=payload.description,
        website_url=payload.website,
        city=payload.city,
        verification=VerificationStatus.PENDING,
        claim_status=ClaimStatus.UNCLAIMED.value,
        contact_email=payload.contact_email.lower() if payload.contact_email else None,
        contact_phone=payload.contact_phone,
    )
    session.add(organization)
    await session.flush()
    profile = Profile(
        organization_id=organization.id,
        kind=ProfileKind.COMPANY,
        display_name=payload.company_name,
        headline=payload.primary_service,
        bio=payload.description,
        city=payload.city,
        pincode=payload.pincode,
        verification=VerificationStatus.PENDING,
    )
    profile.services = [await _service_for(session, payload.primary_service)]
    session.add(profile)
    _log(session, admin, "create_listing", organization.id, organization.name)
    await session.commit()
    return UnclaimedListingOut(
        profile_id=profile.id,
        organization_id=organization.id,
        name=organization.name,
        headline=profile.headline,
        city=organization.city,
        website_url=organization.website_url,
        claim_status=ClaimStatus.UNCLAIMED.value,
    )


# ---------- Public: find a listing to claim ----------


def _listing_query():
    return (
        select(Profile, Organization)
        .join(Organization, Organization.id == Profile.organization_id)
        .where(
            Profile.kind == ProfileKind.COMPANY,
            Profile.deleted_at.is_(None),
            Profile.blocked_at.is_(None),
            Organization.deleted_at.is_(None),
        )
    )


def _listing_out(profile: Profile, organization: Organization) -> UnclaimedListingOut:
    return UnclaimedListingOut(
        profile_id=profile.id,
        organization_id=organization.id,
        name=organization.name,
        headline=profile.headline,
        city=organization.city,
        website_url=organization.website_url,
        claim_status=organization.claim_status,
    )


def _like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


async def search_unclaimed_listings(session: AsyncSession, q: str | None, city: str | None) -> list[UnclaimedListingOut]:
    stmt = _listing_query().where(Organization.claim_status == ClaimStatus.UNCLAIMED.value)
    if q:
        stmt = stmt.where(or_(Organization.name.ilike(_like(q), escape="\\"), Profile.headline.ilike(_like(q), escape="\\")))
    if city:
        stmt = stmt.where(Organization.city.ilike(_like(city), escape="\\"))
    rows = (await session.execute(stmt.order_by(Organization.name).limit(50))).all()
    return [_listing_out(profile, organization) for profile, organization in rows]


async def get_listing(session: AsyncSession, profile_id: UUID) -> UnclaimedListingOut:
    row = (await session.execute(_listing_query().where(Profile.id == profile_id))).first()
    if row is None:
        raise ListingNotFoundError("This business listing could not be found")
    return _listing_out(*row)


# ---------- Owner: prove an email and submit a claim ----------


async def _claimable(session: AsyncSession, profile_id: UUID, *, lock: bool = False) -> tuple[Profile, Organization]:
    profile = await session.get(Profile, profile_id)
    if profile is None or profile.kind is not ProfileKind.COMPANY or profile.deleted_at or profile.blocked_at:
        raise ListingNotFoundError("This business listing could not be found")
    organization = await session.get(Organization, profile.organization_id, with_for_update=lock)
    if organization is None or organization.deleted_at is not None:
        raise ListingNotFoundError("This business listing could not be found")
    if organization.claim_status != ClaimStatus.UNCLAIMED.value:
        raise ListingConflictError("This business has already been claimed by its owner")
    return profile, organization


async def _administers_company(session: AsyncSession, user_id: UUID) -> bool:
    found = await session.scalar(
        select(OrganizationMember.id)
        .join(Organization, Organization.id == OrganizationMember.organization_id)
        .where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.member_role == MemberRole.ADMIN.value,
            Organization.deleted_at.is_(None),
        )
        .limit(1)
    )
    return found is not None


async def _eligible_claimant(session: AsyncSession, auth_user_id: UUID, organization_id: UUID) -> User:
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None:
        raise ClaimEligibilityError("Finish creating your RightConnect account before claiming a business")
    if user.blocked_at is not None:
        raise ClaimEligibilityError("Your account is suspended")
    if await _administers_company(session, user.id):
        raise ClaimEligibilityError("You already run a company on RightConnect. One account can manage one company.")
    pending = await session.scalar(
        select(OrganizationClaim.id).where(
            OrganizationClaim.organization_id == organization_id,
            OrganizationClaim.user_id == user.id,
            OrganizationClaim.status == ClaimReviewStatus.PENDING.value,
        )
    )
    if pending is not None:
        raise ClaimEligibilityError("Your claim for this business is already waiting for review")
    return user


async def send_claim_code(session: AsyncSession, settings: Settings, auth_user_id: UUID, profile_id: UUID, email: str) -> None:
    """Email a 6-digit code to the business address the claimant wants to prove."""
    email = email.strip().lower()
    _, organization = await _claimable(session, profile_id)
    await _eligible_claimant(session, auth_user_id, organization.id)

    now = datetime.now(timezone.utc)
    recent_for_email = await session.scalar(
        select(func.count(EmailVerification.id)).where(
            EmailVerification.purpose == CLAIM_OTP_PURPOSE,
            EmailVerification.organization_id == organization.id,
            EmailVerification.email == email,
            EmailVerification.created_at >= now - timedelta(minutes=OTP_TTL_MINUTES),
        )
    )
    recent_for_listing = await session.scalar(
        select(func.count(EmailVerification.id)).where(
            EmailVerification.purpose == CLAIM_OTP_PURPOSE,
            EmailVerification.organization_id == organization.id,
            EmailVerification.created_at >= now - timedelta(hours=1),
        )
    )
    if (recent_for_email or 0) >= CODES_PER_EMAIL_WINDOW or (recent_for_listing or 0) >= CODES_PER_LISTING_HOUR:
        raise ClaimRateLimitError("Too many codes requested. Please wait a few minutes and try again.")

    code = f"{secrets.randbelow(1_000_000):06d}"
    session.add(
        EmailVerification(
            email=email,
            purpose=CLAIM_OTP_PURPOSE,
            organization_id=organization.id,
            code_hash=_hash(code),
            expires_at=now + timedelta(minutes=OTP_TTL_MINUTES),
        )
    )
    await session.commit()
    await send_email(
        settings,
        to=email,
        subject=f"Your code to claim {organization.name} on RightConnect",
        html=(
            f"<p>Your code to claim <strong>{html.escape(organization.name)}</strong> is <strong>{code}</strong>. "
            f"It expires in {OTP_TTL_MINUTES} minutes.</p><p>If you didn't ask for this, you can ignore this email.</p>"
        ),
    )


async def submit_claim(session: AsyncSession, auth_user_id: UUID, payload: ClaimSubmit) -> MyClaimOut:
    """Check the one-time code and queue the claim for admin review."""
    email = str(payload.email).strip().lower()
    profile, organization = await _claimable(session, payload.profile_id)
    user = await _eligible_claimant(session, auth_user_id, organization.id)

    verification = await session.scalar(
        select(EmailVerification)
        .where(
            EmailVerification.purpose == CLAIM_OTP_PURPOSE,
            EmailVerification.organization_id == organization.id,
            EmailVerification.email == email,
            EmailVerification.verified_at.is_(None),
        )
        .order_by(EmailVerification.created_at.desc())
        .limit(1)
    )
    now = datetime.now(timezone.utc)
    if verification is None or verification.expires_at < now:
        raise ClaimCodeError("Code expired or not found. Request a new one.")
    if verification.attempts >= OTP_MAX_ATTEMPTS:
        raise ClaimCodeError("Too many attempts. Request a new code.")
    if not secrets.compare_digest(verification.code_hash, _hash(payload.code)):
        verification.attempts += 1
        await session.commit()
        raise ClaimCodeError("Incorrect code")

    verification.verified_at = now
    claim = OrganizationClaim(
        organization_id=organization.id,
        user_id=user.id,
        business_email=email,
        email_matches_listing=email_matches_listing(email, organization.contact_email, organization.website_url),
        phone=payload.phone,
        note=payload.note,
        status=ClaimReviewStatus.PENDING.value,
    )
    session.add(claim)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ClaimEligibilityError("Your claim for this business is already waiting for review") from exc
    await session.refresh(claim)
    return MyClaimOut(
        id=claim.id,
        profile_id=profile.id,
        organization_name=organization.name,
        business_email=claim.business_email,
        status=claim.status,
        review_reason=None,
        created_at=claim.created_at,
        reviewed_at=None,
    )


def _company_profile_id():
    return (
        select(Profile.id)
        .where(Profile.organization_id == OrganizationClaim.organization_id, Profile.kind == ProfileKind.COMPANY)
        .limit(1)
        .scalar_subquery()
    )


async def list_my_claims(session: AsyncSession, auth_user_id: UUID) -> list[MyClaimOut]:
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None:
        return []
    rows = (
        await session.execute(
            select(OrganizationClaim, Organization.name, _company_profile_id())
            .join(Organization, Organization.id == OrganizationClaim.organization_id)
            .where(OrganizationClaim.user_id == user.id)
            .order_by(OrganizationClaim.created_at.desc())
            .limit(50)
        )
    ).all()
    return [
        MyClaimOut(
            id=claim.id,
            profile_id=profile_id,
            organization_name=name,
            business_email=claim.business_email,
            status=claim.status,
            review_reason=claim.review_reason,
            created_at=claim.created_at,
            reviewed_at=claim.reviewed_at,
        )
        for claim, name, profile_id in rows
    ]


# ---------- Admin: review claims ----------


async def list_claims_for_admin(session: AsyncSession, status: str) -> list[AdminClaimOut]:
    stmt = (
        select(OrganizationClaim, Organization, User, _company_profile_id())
        .join(Organization, Organization.id == OrganizationClaim.organization_id)
        .join(User, User.id == OrganizationClaim.user_id)
    )
    if status != "all":
        stmt = stmt.where(OrganizationClaim.status == status)
    rows = (await session.execute(stmt.order_by(OrganizationClaim.created_at.desc()).limit(200))).all()
    return [
        AdminClaimOut(
            id=claim.id,
            organization_id=organization.id,
            profile_id=profile_id,
            organization_name=organization.name,
            city=organization.city,
            listing_contact_email=organization.contact_email,
            listing_contact_phone=organization.contact_phone,
            claimant_name=user.full_name,
            claimant_email=user.email,
            business_email=claim.business_email,
            email_matches_listing=claim.email_matches_listing,
            phone=claim.phone,
            note=claim.note,
            status=claim.status,
            review_reason=claim.review_reason,
            created_at=claim.created_at,
            reviewed_at=claim.reviewed_at,
        )
        for claim, organization, user, profile_id in rows
    ]


async def _pending_claim(session: AsyncSession, claim_id: UUID) -> OrganizationClaim:
    claim = await session.get(OrganizationClaim, claim_id, with_for_update=True)
    if claim is None or claim.status != ClaimReviewStatus.PENDING.value:
        raise ClaimNotFoundError("Claim not found or already reviewed")
    return claim


async def approve_claim(session: AsyncSession, settings: Settings, admin: User, claim_id: UUID) -> None:
    """Make the claimant the company's admin and close every other pending claim for it."""
    claim = await _pending_claim(session, claim_id)
    organization = await session.get(Organization, claim.organization_id, with_for_update=True)
    if organization is None or organization.deleted_at is not None:
        raise ListingNotFoundError("This business listing no longer exists")
    if organization.claim_status != ClaimStatus.UNCLAIMED.value:
        raise ListingConflictError("This business has already been claimed")
    claimant = await session.get(User, claim.user_id)
    if claimant is None or claimant.deleted_at is not None or claimant.blocked_at is not None:
        raise ClaimEligibilityError("The claimant's account is no longer active. Reject this claim instead.")
    if await _administers_company(session, claimant.id):
        raise ClaimEligibilityError("The claimant already runs another company. Reject this claim instead.")

    now = datetime.now(timezone.utc)
    session.add(OrganizationMember(organization_id=organization.id, user_id=claimant.id, member_role=MemberRole.ADMIN.value))
    organization.claim_status = ClaimStatus.CLAIMED.value
    organization.claimed_at = now
    # The claimant proved control of this business email with a one-time code.
    organization.email_domain_verified = True
    claim.status = ClaimReviewStatus.APPROVED.value
    claim.reviewed_by = admin.id
    claim.reviewed_at = now
    others = (
        await session.scalars(
            select(OrganizationClaim).where(
                OrganizationClaim.organization_id == organization.id,
                OrganizationClaim.status == ClaimReviewStatus.PENDING.value,
                OrganizationClaim.id != claim.id,
            )
        )
    ).all()
    for other in others:
        other.status = ClaimReviewStatus.REJECTED.value
        other.review_reason = "Another owner's claim for this business was approved."
        other.reviewed_by = admin.id
        other.reviewed_at = now
    _log(session, admin, "approve_claim", organization.id, organization.name, f"Claimed by {claimant.email}")
    await session.commit()

    name = html.escape(organization.name)
    await _notify(
        settings, claimant.email, f"You now manage {organization.name} on RightConnect",
        f"<p>Your claim for <strong>{name}</strong> was approved. Sign in to update the profile and start receiving requests.</p>",
    )


async def reject_claim(session: AsyncSession, settings: Settings, admin: User, claim_id: UUID, reason: str) -> None:
    claim = await _pending_claim(session, claim_id)
    organization = await session.get(Organization, claim.organization_id)
    claimant = await session.get(User, claim.user_id)
    claim.status = ClaimReviewStatus.REJECTED.value
    claim.review_reason = reason
    claim.reviewed_by = admin.id
    claim.reviewed_at = datetime.now(timezone.utc)
    label = organization.name if organization else str(claim.organization_id)
    _log(session, admin, "reject_claim", claim.organization_id, label, reason)
    await session.commit()

    if claimant is not None:
        await _notify(
            settings, claimant.email, f"Your claim for {label} on RightConnect",
            f"<p>Your claim for <strong>{html.escape(label)}</strong> was not approved.</p><p>Reason: {html.escape(reason)}</p>"
            "<p>You can submit a new claim with more proof of ownership.</p>",
        )
