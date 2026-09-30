"""Stripe Checkout endpoints for subscription upgrades."""
import hashlib
import hmac
import time
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import SubscriptionTier, User
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()


@router.post("/checkout")
async def create_checkout_session(
    plan: str,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Create a hosted Stripe Checkout session for a configured plan."""
    price_id = {"pro": settings.stripe_pro_price_id, "enterprise": settings.stripe_enterprise_price_id}.get(plan)
    if not settings.stripe_secret_key or not price_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Payments are not configured yet")
    user = await session.scalar(select(User).where(User.auth_user_id == auth_user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Onboarding not completed")
    payload = {
        "mode": "subscription",
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "success_url": f"{settings.app_base_url.rstrip('/')}/pages/marketplace.html?payment=success",
        "cancel_url": f"{settings.app_base_url.rstrip('/')}/pages/marketplace.html?payment=cancelled",
        "client_reference_id": str(user.id),
        "metadata[user_id]": str(user.id),
        "metadata[plan]": plan,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post("https://api.stripe.com/v1/checkout/sessions", data=payload, auth=(settings.stripe_secret_key, ""))
    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not start payment")
    return {"checkout_url": response.json()["url"]}


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, session: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Apply a paid subscription only for a signed Stripe event."""
    body = await request.body()
    signature = request.headers.get("stripe-signature", "")
    timestamp = next((part.split("=", 1)[1] for part in signature.split(",") if part.startswith("t=")), "")
    signatures = [part.split("=", 1)[1] for part in signature.split(",") if part.startswith("v1=")]
    try:
        timestamp_value = int(timestamp)
    except ValueError:
        timestamp_value = 0
    expected = hmac.new(settings.stripe_webhook_secret.encode(), f"{timestamp}.{body.decode()}".encode(), hashlib.sha256).hexdigest()
    if not settings.stripe_webhook_secret or not timestamp_value or not any(hmac.compare_digest(expected, value) for value in signatures) or abs(time.time() - timestamp_value) > 300:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")
    event = await request.json()
    if event.get("type") == "checkout.session.completed":
        session_data = event.get("data", {}).get("object", {})
        user_id = session_data.get("metadata", {}).get("user_id")
        plan = session_data.get("metadata", {}).get("plan")
        if user_id and plan in {"pro", "enterprise"}:
            user = await session.get(User, UUID(user_id))
            if user:
                user.subscription_tier = SubscriptionTier(plan)
                await session.commit()
    return {"status": "ok"}