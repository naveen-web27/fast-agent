"""Razorpay Standard Checkout and legacy Payment Links for 30-day passes."""
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.features.payments.verification import foreign_origin, matching_payment, valid_payment_signature
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.payment import Payment
from app.models.profile import Organization, Profile, ProfileKind
from app.models.user import SubscriptionTier, User, active_user_by_auth_id
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()
ACCESS_DAYS = 30


def plan_prices(settings: Settings) -> dict[str, int]:
    return {"pro": settings.razorpay_pro_amount_paise, "enterprise": settings.razorpay_enterprise_amount_paise}


@router.get("/plans")
async def list_plans(settings: Settings = Depends(get_settings)) -> dict:
    ready = bool(settings.razorpay_key_id and settings.razorpay_key_secret)
    return {"plans": [{"id": plan, "amount_paise": price if price >= 100 else None, "available": ready and price >= 100, "days": ACCESS_DAYS}
                      for plan, price in plan_prices(settings).items()]}


async def new_payment(plan: str, auth_user_id: UUID, session: AsyncSession, settings: Settings) -> tuple[Payment, User, str]:
    amount = plan_prices(settings)[plan]
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(status_code=503, detail="This plan is not available for checkout yet")
    if amount < 100:
        raise HTTPException(status_code=400, detail="Plan amount must be at least 100 paise")
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="Complete onboarding before checkout")
    profile_id = organization_id = None
    if plan == "pro":
        profile_id = await session.scalar(
            select(Profile.id).where(
                Profile.user_id == user.id, Profile.kind == ProfileKind.EXPERT, Profile.deleted_at.is_(None)
            )
        )
        if profile_id is None:
            raise HTTPException(status_code=409, detail="Pro is for expert profiles. Create your expert profile first.")
        label = "Pro (expert profile)"
    else:
        organization_id = await session.scalar(
            select(OrganizationMember.organization_id)
            .join(Organization, Organization.id == OrganizationMember.organization_id)
            .where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.member_role == MemberRole.ADMIN.value,
                Organization.deleted_at.is_(None),
            )
        )
        if organization_id is None:
            raise HTTPException(status_code=409, detail="Enterprise is for companies. Register your company first.")
        label = "Enterprise (company)"
    payment = Payment(id=uuid.uuid4(), user_id=user.id, profile_id=profile_id, organization_id=organization_id,
                      plan=plan, amount_paise=amount, status="pending")
    session.add(payment)
    await session.commit()
    return payment, user, label


async def razorpay_api(settings: Settings, method: str, path: str, payload: dict | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(method, f"https://api.razorpay.com/v1/{path}", json=payload,
                                            auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("Invalid provider response")
        return result
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Payment provider authentication failed") from exc
        raise HTTPException(status_code=500, detail="Payment provider request failed") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=500, detail="Payment provider is unavailable") from exc


async def activate_payment(payment: Payment, payment_id: str, session: AsyncSession) -> dict:
    if payment.status == "paid":
        if payment.razorpay_payment_id != payment_id:
            raise HTTPException(status_code=400, detail="Payment details do not match")
        return {"status": "paid", "access_expires_at": payment.access_expires_at.isoformat()}
    if payment.status != "pending":
        raise HTTPException(status_code=400, detail="Payment is not pending")
    now = datetime.now(timezone.utc)
    if payment.profile_id or payment.organization_id:
        target = (await session.get(Profile, payment.profile_id, with_for_update=True) if payment.profile_id
                  else await session.get(Organization, payment.organization_id, with_for_update=True))
    else:
        target = await session.get(User, payment.user_id, with_for_update=True)
    if target is None or getattr(target, "deleted_at", None) is not None:
        raise HTTPException(status_code=409, detail="The profile for this payment no longer exists")
    expires_at = max(now, target.subscription_expires_at or now) + timedelta(days=ACCESS_DAYS)
    payment.status = "paid"
    payment.razorpay_payment_id = payment_id
    payment.paid_at = now
    payment.access_expires_at = expires_at
    target.subscription_tier = SubscriptionTier(payment.plan)
    target.subscription_expires_at = expires_at
    await session.commit()
    return {"status": "paid", "access_expires_at": expires_at.isoformat()}


@router.post("/create-order")
async def create_order(
    plan: Literal["pro", "enterprise"],
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    payment, user, label = await new_payment(plan, auth_user_id, session, settings)
    order = await razorpay_api(settings, "POST", "orders", {
        "amount": payment.amount_paise, "currency": "INR", "receipt": str(payment.id),
        "notes": {"rightconnect_payment_id": str(payment.id), "rightconnect_origin": settings.app_base_url.rstrip("/")},
    })
    order_id = order.get("id")
    if not isinstance(order_id, str) or not order_id.startswith("order_") \
            or order.get("amount") != payment.amount_paise or order.get("currency") != "INR":
        raise HTTPException(status_code=500, detail="Invalid order returned by provider")
    payment.razorpay_order_id = order_id
    await session.commit()
    return {"order_id": order_id, "amount": payment.amount_paise, "currency": "INR",
            "key_id": settings.razorpay_key_id, "description": f"{label} - {ACCESS_DAYS} days",
            "prefill": {"name": user.full_name, "email": user.email or ""}}


@router.post("/verify-payment")
async def verify_payment(
    body: dict | None = Body(default=None),
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    fields = ("razorpay_order_id", "razorpay_payment_id", "razorpay_signature")
    if not body or any(not isinstance(body.get(field), str) or not body[field] for field in fields):
        raise HTTPException(status_code=400, detail="Missing payment verification fields")
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(status_code=503, detail="Payment verification is unavailable")
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="Complete onboarding before checkout")
    payment = await session.scalar(select(Payment).where(
        Payment.razorpay_order_id == body["razorpay_order_id"], Payment.user_id == user.id
    ).with_for_update())
    if payment is None:
        raise HTTPException(status_code=400, detail="Unknown payment order for this account")
    payment_id = body["razorpay_payment_id"]
    if not valid_payment_signature(payment.razorpay_order_id, payment_id, body["razorpay_signature"], settings.razorpay_key_secret):
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    if payment.status == "paid":
        return await activate_payment(payment, payment_id, session)
    if payment.status != "pending":
        raise HTTPException(status_code=400, detail="Payment is not pending")
    captured = await razorpay_api(settings, "GET", f"payments/{payment_id}")
    if not matching_payment(captured, payment.razorpay_order_id, payment.amount_paise, payment_id):
        raise HTTPException(status_code=400, detail="Payment details do not match")
    if captured["status"] != "captured":
        return {"status": "pending", "detail": "Payment authorized; awaiting capture. Do not pay again."}
    return await activate_payment(payment, payment_id, session)


@router.post("/checkout")
async def create_checkout_session(
    plan: Literal["pro", "enterprise"],
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    if not settings.razorpay_webhook_secret:
        raise HTTPException(status_code=503, detail="Payment Links require a webhook secret")
    payment, user, label = await new_payment(plan, auth_user_id, session, settings)

    payload = {
        "amount": payment.amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": f"RightConnect {label} - {ACCESS_DAYS} days access",
        "reference_id": str(payment.id),
        "notes": {"rightconnect_origin": settings.app_base_url.rstrip("/")},
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
    if not settings.razorpay_webhook_secret or not hmac.compare_digest(signature.encode(), expected.encode()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")
    event = await request.json()
    if event.get("event") == "order.paid":
        payload = event.get("payload", {})
        order = payload.get("order", {}).get("entity", {})
        captured = payload.get("payment", {}).get("entity", {})
        if foreign_origin(order, settings.app_base_url):
            return {"status": "ignored"}
        notes = order.get("notes") or {}
        if not isinstance(notes, dict) or not notes.get("rightconnect_payment_id"):
            return {"status": "ignored"}
        try:
            payment_id = UUID(notes["rightconnect_payment_id"])
        except (ValueError, TypeError):
            return {"status": "ignored"}
        payment = await session.get(Payment, payment_id, with_for_update=True)
        if payment is None or payment.razorpay_order_id != order.get("id"):
            raise HTTPException(status_code=503, detail="Payment record not ready")
        provider_payment_id = captured.get("id")
        if not isinstance(provider_payment_id, str) or not provider_payment_id \
                or order.get("status") != "paid" or order.get("currency") != "INR" \
                or order.get("amount") != payment.amount_paise or order.get("amount_paid") != payment.amount_paise \
                or not matching_payment(captured, payment.razorpay_order_id, payment.amount_paise, provider_payment_id) \
                or captured.get("status") != "captured":
            raise HTTPException(status_code=400, detail="Payment details do not match")
        await activate_payment(payment, provider_payment_id, session)
        return {"status": "ok"}
    if event.get("event") == "payment_link.paid":
        payload = event.get("payload", {})
        link = payload.get("payment_link", {}).get("entity", {})
        captured = payload.get("payment", {}).get("entity", {})
        if foreign_origin(link, settings.app_base_url):
            return {"status": "ignored"}
        try:
            payment_id = UUID(link.get("reference_id", ""))
        except (ValueError, TypeError):
            return {"status": "ignored"}
        payment = await session.get(Payment, payment_id, with_for_update=True)
        if payment is None and not (link.get("notes") or {}).get("rightconnect_origin"):
            return {"status": "ignored"}
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
        await activate_payment(payment, captured["id"], session)
    return {"status": "ok"}