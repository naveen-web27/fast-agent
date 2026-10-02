"""Hosted Razorpay Payment Links for 30-day access passes."""
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.payment import Payment
from app.models.user import SubscriptionTier, User, active_user_by_auth_id
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()
ACCESS_DAYS = 30


def plan_prices(settings: Settings) -> dict[str, int]:
    return {"pro": settings.razorpay_pro_amount_paise, "enterprise": settings.razorpay_enterprise_amount_paise}


@router.get("/plans")
async def list_plans(settings: Settings = Depends(get_settings)) -> dict:
    ready = bool(settings.razorpay_key_id and settings.razorpay_key_secret and settings.razorpay_webhook_secret)
    return {"plans": [{"id": plan, "amount_paise": price if price >= 100 else None, "available": ready and price >= 100, "days": ACCESS_DAYS}
                      for plan, price in plan_prices(settings).items()]}


@router.post("/checkout")
async def create_checkout_session(
    plan: Literal["pro", "enterprise"],
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    amount = plan_prices(settings)[plan]
    if not settings.razorpay_key_id or not settings.razorpay_key_secret or not settings.razorpay_webhook_secret or amount < 100:
        raise HTTPException(status_code=503, detail="This plan is not available for checkout yet")
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="Complete onboarding before checkout")
    payment = Payment(id=uuid.uuid4(), user_id=user.id, plan=plan, amount_paise=amount, status="pending")
    session.add(payment)
    await session.commit()

    payload = {
        "amount": amount,
        "currency": "INR",
        "accept_partial": False,
        "description": f"RightConnect {plan.title()} - {ACCESS_DAYS} days access",
        "reference_id": str(payment.id),
        "customer": {"name": user.full_name, "email": user.email},
        "notify": {"email": False, "sms": False},
        "callback_url": f"{settings.app_base_url.rstrip('/')}/pages/plans.html?payment=returned",
        "callback_method": "get",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post("https://api.razorpay.com/v1/payment_links", json=payload,
                                         auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
        response.raise_for_status()
        link = response.json()
        link_id = link["id"]
        checkout_url = link["short_url"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not create the payment link") from exc
    if not checkout_url.startswith(("https://rzp.io/", "https://razorpay.com/")):
        raise HTTPException(status_code=502, detail="Invalid payment link returned by provider")
    payment.razorpay_link_id = link_id
    await session.commit()
    return {"checkout_url": checkout_url}


@router.post("/webhook", include_in_schema=False)
async def razorpay_webhook(request: Request, session: AsyncSession = Depends(get_db),
                          settings: Settings = Depends(get_settings)) -> dict[str, str]:
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    expected = hmac.new(settings.razorpay_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    if not settings.razorpay_webhook_secret or not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")
    event = await request.json()
    if event.get("event") == "payment_link.paid":
        payload = event.get("payload", {})
        link = payload.get("payment_link", {}).get("entity", {})
        captured = payload.get("payment", {}).get("entity", {})
        try:
            payment_id = UUID(link.get("reference_id", ""))
        except (ValueError, TypeError):
            return {"status": "ignored"}
        payment = await session.get(Payment, payment_id, with_for_update=True)
        if payment is None or payment.razorpay_link_id != link.get("id"):
            raise HTTPException(status_code=503, detail="Payment record not ready")
        if payment.status == "paid":
            return {"status": "ok"}
        if payment.status != "pending" or link.get("status") != "paid" or link.get("currency") != "INR" \
                or link.get("amount") != payment.amount_paise or link.get("amount_paid") != payment.amount_paise \
                or captured.get("status") != "captured" or captured.get("currency") != "INR" \
                or captured.get("amount") != payment.amount_paise \
                or not captured.get("id"):
            raise HTTPException(status_code=400, detail="Payment details do not match")
        user = await session.get(User, payment.user_id, with_for_update=True)
        now = datetime.now(timezone.utc)
        expires_at = max(now, user.subscription_expires_at or now) + timedelta(days=ACCESS_DAYS)
        payment.status = "paid"
        payment.razorpay_payment_id = captured["id"]
        payment.paid_at = now
        payment.access_expires_at = expires_at
        user.subscription_tier = (SubscriptionTier.ENTERPRISE if user.subscription_tier == SubscriptionTier.ENTERPRISE
                      and user.subscription_expires_at and user.subscription_expires_at > now
                      else SubscriptionTier(payment.plan))
        user.subscription_expires_at = expires_at
        await session.commit()
    return {"status": "ok"}