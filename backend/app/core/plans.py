"""Per-identity paid plans: Pro unlocks one expert profile, Enterprise unlocks one company.

Customers never pay; every core request flow stays free. Plans only unlock provider tools.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Organization, Profile, ProfileKind
from app.models.user import SubscriptionTier

PLAN_FOR_KIND = {ProfileKind.EXPERT: SubscriptionTier.PRO, ProfileKind.COMPANY: SubscriptionTier.ENTERPRISE}

TEAM_SEAT_LIMIT = 10
SOCIAL_LINK_LIMIT = {False: 2, True: 10}
CREDENTIAL_LIMIT = {False: 1, True: 10}
OFFERING_LIMIT = 20


class PlanRequiredError(Exception):
    """Raised when a provider tool needs the identity's paid plan."""


def _active(tier: SubscriptionTier, expires_at: datetime | None) -> bool:
    return tier is not SubscriptionTier.FREE and expires_at is not None and expires_at > datetime.now(timezone.utc)


def expert_plan_active(profile: Profile) -> bool:
    return _active(profile.subscription_tier, profile.subscription_expires_at)


def company_plan_active(organization: Organization | None) -> bool:
    return organization is not None and _active(organization.subscription_tier, organization.subscription_expires_at)


def plan_expiry(tier: SubscriptionTier, expires_at: datetime | None) -> datetime | None:
    return expires_at if _active(tier, expires_at) else None


async def profile_plan_active(session: AsyncSession, profile: Profile) -> bool:
    """Expert profiles carry their own Pro plan; company profiles use their organization's Enterprise plan."""
    if profile.kind is ProfileKind.EXPERT:
        return expert_plan_active(profile)
    return company_plan_active(await session.get(Organization, profile.organization_id))


def require_plan(active: bool, kind: ProfileKind, feature: str) -> None:
    if not active:
        plan = "Pro" if kind is ProfileKind.EXPERT else "Enterprise"
        raise PlanRequiredError(f"{feature} is part of the {plan} plan. Upgrade from the Plans page to unlock it.")
